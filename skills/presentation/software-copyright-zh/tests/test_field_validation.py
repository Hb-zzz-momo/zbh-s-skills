from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import validate_application_fields as field_tool  # noqa: E402


def valid_application() -> dict:
    values = {
        "software_full_name": "示例业务系统",
        "software_short_name": "示例系统",
        "version": "V1.0",
        "software_category": "应用软件",
        "copyright_holders": [{"name": "示例主体", "type": "organization"}],
        "development_completion_date": "2026-01-15",
        "development_method": "单独开发",
        "publication_status": "unpublished",
        "first_publication_date": None,
        "rights_scope": "全部权利",
        "rights_acquisition_method": "原始取得",
        "development_hardware": "合成测试环境",
        "runtime_hardware": "合成测试环境",
        "development_os": "Windows",
        "development_tools": ["Visual Studio Code"],
        "runtime_platform": "浏览器",
        "runtime_support": ["Python"],
        "programming_languages": ["Python"],
        "source_line_count": 42,
        "application_purpose": "验证业务资料整理流程",
        "industry": "通用软件",
        "main_functions": "处理示例数据并展示可核验结果。",
        "technical_characteristics": "本地运行并保留来源记录。",
    }
    fields = {}
    for key, value in values.items():
        rule = field_tool.FIELD_RULES[key]
        fields[key] = {
            "value": value,
            "suggested_value": None,
            "data_type": field_tool.FIELD_DATA_TYPES[key],
            "required": bool(rule.get("required")),
            "character_limit": None,
            "allowed_values": sorted(rule.get("allowed", [])),
            "source": "user",
            "project_inferable": False,
            "user_confirmation_required": True,
            "confirmed": True,
            "verified_at": "2026-07-12T12:00:00Z",
        }
    return {
        "schema_version": 1,
        "official_form_verified_at": "2026-07-12",
        "fields": fields,
        "confirmed_fields": list(fields),
        "user_confirmed": True,
        "confirmed_at": "2026-07-12T12:00:00Z",
    }


class ApplicationFieldValidationTests(unittest.TestCase):
    def test_legacy_truthy_form_date_cannot_claim_current_verification(self) -> None:
        report = field_tool.validate_application_fields(valid_application(), require_confirmed=True)
        self.assertEqual(report["status"], "CAUTION")
        self.assertEqual(report["summary"]["errors"], 0)
        self.assertFalse(report["current_online_form_verified"])
        self.assertIn("LEGACY_FORM_DATE_NOT_EVIDENCE", {item["rule_id"] for item in report["findings"]})

    def test_form_version_without_snapshot_cannot_claim_current_verification(self) -> None:
        data = valid_application()
        data.pop("official_form_verified_at", None)
        data["current_form_evidence"] = {
            "source_url": "https://register.ccopyright.com.cn/login.html",
            "verified_at": "2026-07-12",
            "form_version": "synthetic-test-snapshot",
        }
        report = field_tool.validate_application_fields(data, require_confirmed=True)
        self.assertEqual(report["status"], "CAUTION")
        self.assertFalse(report["current_online_form_verified"])
        self.assertIn("CURRENT_FORM_SNAPSHOT_MISSING", {item["rule_id"] for item in report["findings"]})

    def test_readable_in_project_form_snapshot_requires_matching_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = root / "软件著作权申请资料" / "00-项目证据" / "official-form.html"
            snapshot.parent.mkdir(parents=True)
            snapshot.write_text("<html><title>软件登记表单</title><body>synthetic bound form snapshot</body></html>", encoding="utf-8")
            data = valid_application()
            data.pop("official_form_verified_at", None)
            data["current_form_evidence"] = {
                "source_url": "https://register.ccopyright.com.cn/software-register/form.html",
                "verified_at": "2026-07-12",
                "form_version": "synthetic-test-snapshot",
                "snapshot_path": snapshot.relative_to(root).as_posix(),
                "snapshot_sha256": hashlib.sha256(snapshot.read_bytes()).hexdigest(),
                "capture_method": "browser-export",
                "captured_at": "2026-07-12T12:00:00+08:00",
                "page_title": "软件登记表单",
                "field_names": list(field_tool.FIELD_RULES),
                "user_confirmed_source": True,
            }
            report = field_tool.validate_application_fields(
                data,
                require_confirmed=True,
                snapshot_root=root,
            )
            self.assertEqual(report["status"], "PASS")
            self.assertTrue(report["current_online_form_verified"])

            application_path = root / "软件著作权申请资料" / "01-草稿" / "application.json"
            application_path.parent.mkdir()
            application_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "validate_application_fields.py"),
                    str(application_path),
                    "--require-confirmed",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 0, completed.stdout)
            self.assertTrue(json.loads(completed.stdout)["current_online_form_verified"])

            data["current_form_evidence"]["snapshot_sha256"] = "0" * 64
            report = field_tool.validate_application_fields(
                data,
                require_confirmed=True,
                snapshot_root=root,
            )
            self.assertEqual(report["status"], "BLOCK")
            self.assertIn("CURRENT_FORM_SNAPSHOT_HASH_MISMATCH", {item["rule_id"] for item in report["findings"]})

    def test_current_form_snapshot_must_remain_inside_bound_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            root = container / "project"
            root.mkdir()
            outside = container / "outside.html"
            outside.write_text("synthetic outside snapshot", encoding="utf-8")
            data = valid_application()
            data.pop("official_form_verified_at", None)
            data["current_form_evidence"] = {
                "source_url": "https://register.ccopyright.com.cn/software-register/form.html",
                "verified_at": "2026-07-12",
                "snapshot_path": "../outside.html",
                "snapshot_sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
                "capture_method": "browser-export",
                "captured_at": "2026-07-12T12:00:00+08:00",
                "page_title": "软件登记表单",
                "field_names": list(field_tool.FIELD_RULES),
                "user_confirmed_source": True,
            }
            report = field_tool.validate_application_fields(data, snapshot_root=root)
            self.assertEqual(report["status"], "BLOCK")
            self.assertIn("CURRENT_FORM_SNAPSHOT_OUTSIDE_ROOT", {item["rule_id"] for item in report["findings"]})

    def test_suggested_value_never_becomes_formal_when_confirmation_is_required(self) -> None:
        data = valid_application()
        data["fields"]["software_full_name"] = {
            "value": None,
            "suggested_value": "仅为建议的软件名称",
            "confirmed": True,
        }
        report = field_tool.validate_application_fields(data, require_confirmed=True)
        self.assertEqual(report["status"], "BLOCK")
        self.assertIn("SUGGESTED_VALUE_NOT_FORMAL", {item["rule_id"] for item in report["findings"]})

    def test_formal_validation_requires_complete_consistent_field_metadata(self) -> None:
        data = valid_application()
        data["fields"]["software_full_name"].pop("source")
        data["fields"]["version"]["data_type"] = "integer"
        data["fields"]["industry"]["confirmed"] = False
        report = field_tool.validate_application_fields(data, require_confirmed=True)
        rule_ids = {item["rule_id"] for item in report["findings"]}
        self.assertIn("FIELD_METADATA_INVALID", rule_ids)
        self.assertIn("FIELD_CONFIRMATION_CONFLICT", rule_ids)
        self.assertEqual(report["status"], "BLOCK")

    def test_malformed_current_form_evidence_blocks_without_traceback(self) -> None:
        data = valid_application()
        data["current_form_evidence"] = ["bad-shape"]
        report = field_tool.validate_application_fields(data, require_confirmed=True)
        self.assertEqual(report["status"], "BLOCK")
        self.assertIn("CURRENT_FORM_EVIDENCE_INVALID", {item["rule_id"] for item in report["findings"]})

    def test_detects_missing_required_field(self) -> None:
        data = valid_application()
        del data["fields"]["software_full_name"]
        report = field_tool.validate_application_fields(data, require_confirmed=True)
        rule_ids = {item["rule_id"] for item in report["findings"]}
        self.assertIn("REQUIRED_FIELD_MISSING", rule_ids)
        self.assertEqual(report["status"], "BLOCK")

    def test_detects_first_publication_date_for_unpublished_software(self) -> None:
        data = valid_application()
        data["fields"]["first_publication_date"]["value"] = "2026-01-16"
        report = field_tool.validate_application_fields(data, require_confirmed=True)
        rule_ids = {item["rule_id"] for item in report["findings"]}
        self.assertIn("UNPUBLISHED_DATE_CONFLICT", rule_ids)

    def test_sensitive_field_is_blocked_without_echoing_value(self) -> None:
        data = valid_application()
        synthetic_value = "SYNTHETIC-PRIVATE-VALUE"
        data["fields"]["identity_document_number"] = synthetic_value
        report = field_tool.validate_application_fields(data)
        self.assertIn("SENSITIVE_FIELD_IN_PUBLIC_DATA", {item["rule_id"] for item in report["findings"]})
        self.assertNotIn(synthetic_value, json.dumps(report, ensure_ascii=False))

    def test_sensitive_value_pattern_is_blocked_even_under_an_unknown_key(self) -> None:
        data = valid_application()
        data["unexpected_public_note"] = "91350211M000100Y4X"
        report = field_tool.validate_application_fields(data)
        self.assertIn("SENSITIVE_VALUE_IN_PUBLIC_DATA", {item["rule_id"] for item in report["findings"]})

    def test_declared_character_limit_requires_source_and_is_enforced(self) -> None:
        data = valid_application()
        data["fields"]["software_full_name"] = {
            "value": "示例业务系统",
            "confirmed": True,
            "character_limit": 4,
            "character_limit_source": {
                "kind": "synthetic-workflow-test",
                "reference": "fixture://field-limit",
            },
        }
        report = field_tool.validate_application_fields(data, require_confirmed=True)
        self.assertEqual(report["status"], "BLOCK")
        self.assertIn("CHARACTER_LIMIT_EXCEEDED", {item["rule_id"] for item in report["findings"]})

        data["fields"]["software_full_name"].pop("character_limit_source")
        report = field_tool.validate_application_fields(data, require_confirmed=True)
        self.assertIn("CHARACTER_LIMIT_SOURCE_MISSING", {item["rule_id"] for item in report["findings"]})

    def test_malformed_nested_field_is_machine_readable_block(self) -> None:
        data = valid_application()
        data["fields"]["copyright_holders"]["value"] = ["bad-shape"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "application.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPTS / "validate_application_fields.py"), str(path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(json.loads(completed.stdout)["status"], "BLOCK")
            self.assertNotIn("Traceback", completed.stderr)

    def test_malformed_external_schema_returns_json_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            application_path = root / "application.json"
            schema_path = root / "schema.json"
            application_path.write_text(json.dumps(valid_application(), ensure_ascii=False), encoding="utf-8")
            schema_path.write_text(json.dumps({"schema_version": 1, "fields": ["bad-shape"]}), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "validate_application_fields.py"),
                    str(application_path),
                    "--schema",
                    str(schema_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 3)
            self.assertEqual(json.loads(completed.stdout)["status"], "ERROR")
            self.assertNotIn("Traceback", completed.stderr)

    def test_cli_returns_machine_readable_nonzero_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "application.json"
            path.write_text(json.dumps({"fields": {}}, ensure_ascii=False), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPTS / "validate_application_fields.py"), str(path), "--require-confirmed"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(json.loads(completed.stdout)["status"], "BLOCK")


if __name__ == "__main__":
    unittest.main()
