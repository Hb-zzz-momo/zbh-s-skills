from __future__ import annotations

import hashlib
import base64
import json
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path
from unittest import mock
from xml.sax.saxutils import escape


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import validate_consistency as consistency_tool  # noqa: E402
import validate_outputs as output_tool  # noqa: E402
from validate_application_fields import serialize_application_txt  # noqa: E402
from test_field_validation import valid_application  # noqa: E402


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def make_png(width: int, height: int) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    row = b"\x00" + (b"\x40\x80\xc0" * width)
    return signature + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(row * height)) + chunk(b"IEND", b"")
JPEG_2X2 = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIs"
    "IxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIy"
    "MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAACAAIDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAA"
    "AAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAk"
    "M2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKT"
    "lJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QA"
    "HwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdh"
    "cRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hp"
    "anN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk"
    "5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDi6KKK+ZP3E//Z"
)


def write_minimal_docx(path: Path, text: str, embedded_images: dict[str, bytes] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    embedded_images = embedded_images or {}
    paragraphs = "".join(
        f"<w:p><w:r><w:t xml:space=\"preserve\">{escape(line)}</w:t></w:r></w:p>"
        for line in text.splitlines()
    )
    drawings = "".join(
        f'<w:p><w:r><w:drawing><a:blip r:embed="rIdImage{index}"/></w:drawing></w:r></w:p>'
        for index, _ in enumerate(embedded_images, start=1)
    )
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        f"<w:body>{paragraphs}{drawings}<w:sectPr/></w:body></w:document>"
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Default Extension="png" ContentType="image/png"/>'
            '<Override PartName="/word/document.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '</Types>',
        )
        archive.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="word/document.xml"/>'
            '</Relationships>',
        )
        archive.writestr("word/document.xml", document_xml)
        if embedded_images:
            relationships = "".join(
                f'<Relationship Id="rIdImage{index}" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
                f'Target="media/{name}"/>'
                for index, name in enumerate(embedded_images, start=1)
            )
            archive.writestr(
                "word/_rels/document.xml.rels",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                f"{relationships}</Relationships>",
            )
            for name, payload in embedded_images.items():
                archive.writestr(f"word/media/{name}", payload)


def write_minimal_pdf(path: Path, text: str) -> None:
    safe_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 10 Tf 40 100 Td ({safe_text}) Tj ET".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 150] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    payload = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(payload))
        payload.extend(f"{index} 0 obj\n".encode("ascii"))
        payload.extend(obj + b"\nendobj\n")
    xref = len(payload)
    payload.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    payload.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        payload.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    payload.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
    )
    path.write_bytes(bytes(payload))


class ConsistencyValidationTests(unittest.TestCase):
    def base_inputs(self, root: Path) -> tuple[Path, Path, Path, Path, Path]:
        material_root = root / "软件著作权申请资料"
        evidence_dir = material_root / "00-项目证据"
        draft_dir = material_root / "01-草稿"
        evidence_dir.mkdir(parents=True)
        draft_dir.mkdir()
        source = root / "src" / "service.py"
        source.parent.mkdir()
        source.write_text("def run():\n    return 1\n", encoding="utf-8")
        application_data = valid_application()
        application_data["fields"]["source_line_count"]["value"] = 2
        application = draft_dir / "申请表信息.json"
        application.write_text(json.dumps(application_data, ensure_ascii=False), encoding="utf-8")
        manual = draft_dir / "操作手册.md"
        manual.write_text("# 示例业务系统 V1.0 操作手册\n\n用户执行真实操作。\n", encoding="utf-8")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        manifest = evidence_dir / "source-manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "project_root": str(root.resolve()),
                    "files": [
                        {
                            "path": "src/service.py",
                            "language": "Python",
                            "line_count": 2,
                            "sha256": digest,
                            "category": "service",
                            "is_third_party": False,
                            "selection_reason": "",
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        selection = draft_dir / "代码文件选择.json"
        selection.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "user_confirmed": True,
                    "confirmed_at": "2026-07-12T12:00:00Z",
                    "candidates": [
                        {
                            "path": "src/service.py",
                            "selected": True,
                            "is_third_party": False,
                            "sha256": digest,
                            "selected_content_sha256": digest,
                            "user_confirmed": True,
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        evidence_map = evidence_dir / "source-evidence-map.json"
        evidence_map.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "features": [
                        {
                            "feature_id": "feature-example-processing",
                            "feature_name": "示例处理",
                            "description": "处理示例数据",
                            "evidence_files": ["src/service.py"],
                            "routes": [],
                            "api_endpoints": [],
                            "screenshots": ["screen-1"],
                            "confidence": "confirmed",
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return material_root, application, manifest, selection, evidence_map

    def run_consistency(self, root: Path) -> dict:
        material_root, application, manifest, selection, evidence_map = self.base_inputs(root)
        return consistency_tool.validate_consistency(
            application_path=application,
            materials_root=material_root,
            source_manifest_path=manifest,
            selection_path=selection,
            evidence_map_path=evidence_map,
            project_root=root,
        )

    def test_detects_software_name_inconsistency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_root, application, manifest, selection, evidence_map = self.base_inputs(root)
            (material_root / "01-草稿" / "操作手册.md").write_text("# 另一个系统 V1.0 操作手册\n", encoding="utf-8")
            report = consistency_tool.validate_consistency(application, material_root, manifest, selection, evidence_map, root)
            self.assertIn("SOFTWARE_NAME_MISMATCH", {item["rule_id"] for item in report["findings"]})

    def test_detects_version_inconsistency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_root, application, manifest, selection, evidence_map = self.base_inputs(root)
            (material_root / "01-草稿" / "操作手册.md").write_text("# 示例业务系统 V2.0 操作手册\n", encoding="utf-8")
            report = consistency_tool.validate_consistency(application, material_root, manifest, selection, evidence_map, root)
            self.assertIn("VERSION_MISMATCH", {item["rule_id"] for item in report["findings"]})

    def test_formal_application_txt_must_match_every_confirmed_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_root, application, manifest, selection, evidence_map = self.base_inputs(root)
            formal = material_root / "03-正式资料"
            formal.mkdir()
            data = json.loads(application.read_text(encoding="utf-8"))
            text = serialize_application_txt(data).replace('industry\t"通用软件"', 'industry\t"错误行业"')
            (formal / "申请表信息.txt").write_text(text, encoding="utf-8")
            report = consistency_tool.validate_consistency(
                application, material_root, manifest, selection, evidence_map, root
            )
            self.assertIn("APPLICATION_TXT_FIELD_MISMATCH", {item["rule_id"] for item in report["findings"]})

    def test_detects_third_party_selection_even_if_input_claims_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_root, application, manifest, selection, evidence_map = self.base_inputs(root)
            data = json.loads(selection.read_text(encoding="utf-8"))
            data["candidates"].append(
                {"path": "node_modules/example/index.js", "selected": True, "is_third_party": False, "sha256": "synthetic"}
            )
            selection.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            report = consistency_tool.validate_consistency(application, material_root, manifest, selection, evidence_map, root)
            self.assertIn("THIRD_PARTY_SOURCE_SELECTED", {item["rule_id"] for item in report["findings"]})

    def test_detects_manifest_flagged_third_party_inside_source_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_root, application, manifest, selection, evidence_map = self.base_inputs(root)
            manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
            manifest_data["files"][0]["is_third_party"] = True
            manifest.write_text(json.dumps(manifest_data, ensure_ascii=False), encoding="utf-8")
            report = consistency_tool.validate_consistency(application, material_root, manifest, selection, evidence_map, root)
            self.assertIn("THIRD_PARTY_SOURCE_SELECTED", {item["rule_id"] for item in report["findings"]})

    def test_detects_selected_test_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_root, application, manifest, selection, evidence_map = self.base_inputs(root)
            snapshot = root / "tests" / "__snapshots__" / "state.js"
            snapshot.parent.mkdir(parents=True)
            snapshot.write_text("export const state = 'snapshot';\n", encoding="utf-8")
            digest = hashlib.sha256(snapshot.read_bytes()).hexdigest()
            manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
            manifest_data["files"].append(
                {
                    "path": "tests/__snapshots__/state.js",
                    "language": "JavaScript",
                    "line_count": 1,
                    "sha256": digest,
                    "category": "source",
                    "is_third_party": False,
                }
            )
            manifest.write_text(json.dumps(manifest_data, ensure_ascii=False), encoding="utf-8")
            selection_data = json.loads(selection.read_text(encoding="utf-8"))
            selection_data["candidates"].append(
                {"path": "tests/__snapshots__/state.js", "selected": True, "sha256": digest}
            )
            selection.write_text(json.dumps(selection_data, ensure_ascii=False), encoding="utf-8")
            report = consistency_tool.validate_consistency(application, material_root, manifest, selection, evidence_map, root)
            self.assertIn("TEST_SNAPSHOT_SOURCE_SELECTED", {item["rule_id"] for item in report["findings"]})

    def test_detects_stale_source_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_root, application, manifest, selection, evidence_map = self.base_inputs(root)
            (root / "src" / "service.py").write_text("def run():\n    return 2\n", encoding="utf-8")
            report = consistency_tool.validate_consistency(application, material_root, manifest, selection, evidence_map, root)
            self.assertIn("SOURCE_HASH_MISMATCH", {item["rule_id"] for item in report["findings"]})

    def test_selection_requires_item_confirmation_and_exact_confirmed_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_root, application, manifest, selection, evidence_map = self.base_inputs(root)
            data = json.loads(selection.read_text(encoding="utf-8"))
            data["candidates"][0]["user_confirmed"] = False
            data["candidates"][0]["sha256"] = "0" * 64
            data["candidates"][0]["selected_content_sha256"] = "1" * 64
            selection.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            report = consistency_tool.validate_consistency(application, material_root, manifest, selection, evidence_map, root)
            rules = {item["rule_id"] for item in report["findings"]}
            self.assertIn("CODE_ITEM_NOT_CONFIRMED", rules)
            self.assertIn("SELECTION_MANIFEST_HASH_MISMATCH", rules)
            self.assertIn("SELECTED_CONTENT_HASH_MISMATCH", rules)

    def test_detects_duplicate_selected_source_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_root, application, manifest, selection, evidence_map = self.base_inputs(root)
            source = root / "src" / "service.py"
            duplicate = root / "src" / "duplicate.py"
            duplicate.write_bytes(source.read_bytes())
            digest = hashlib.sha256(duplicate.read_bytes()).hexdigest()
            manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
            manifest_data["files"].append(
                {
                    "path": "src/duplicate.py",
                    "language": "Python",
                    "line_count": 2,
                    "sha256": digest,
                    "category": "service",
                    "is_third_party": False,
                    "selection_reason": "",
                }
            )
            manifest.write_text(json.dumps(manifest_data, ensure_ascii=False), encoding="utf-8")
            selection_data = json.loads(selection.read_text(encoding="utf-8"))
            selection_data["candidates"].append(
                {"path": "src/duplicate.py", "selected": True, "is_third_party": False, "sha256": digest}
            )
            selection.write_text(json.dumps(selection_data, ensure_ascii=False), encoding="utf-8")
            report = consistency_tool.validate_consistency(application, material_root, manifest, selection, evidence_map, root)
            self.assertIn("DUPLICATE_SOURCE_CONTENT", {item["rule_id"] for item in report["findings"]})

    def test_detects_synthetic_secret_pattern_in_selected_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_root, application, manifest, selection, evidence_map = self.base_inputs(root)
            source = root / "src" / "service.py"
            source.write_text('password = "SYNTHETIC_TEST_ONLY"\n', encoding="utf-8")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
            manifest_data["files"][0]["sha256"] = digest
            manifest_data["files"][0]["line_count"] = 1
            manifest.write_text(json.dumps(manifest_data, ensure_ascii=False), encoding="utf-8")
            selection_data = json.loads(selection.read_text(encoding="utf-8"))
            selection_data["candidates"][0]["sha256"] = digest
            selection.write_text(json.dumps(selection_data, ensure_ascii=False), encoding="utf-8")
            report = consistency_tool.validate_consistency(application, material_root, manifest, selection, evidence_map, root)
            self.assertIn("SENSITIVE_DATA_IN_SELECTED_SOURCE", {item["rule_id"] for item in report["findings"]})

    def test_blocks_empty_confirmed_source_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_root, application, manifest, selection, evidence_map = self.base_inputs(root)
            selection.write_text(json.dumps({"schema_version": 1, "user_confirmed": True, "confirmed_at": "2026-07-12T12:00:00Z", "candidates": []}), encoding="utf-8")
            report = consistency_tool.validate_consistency(application, material_root, manifest, selection, evidence_map, root)
            self.assertIn("CODE_SELECTION_EMPTY", {item["rule_id"] for item in report["findings"]})

    def test_blocks_confirmed_feature_without_hashed_source_and_screenshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_root, application, manifest, selection, evidence_map = self.base_inputs(root)
            evidence_map.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "features": [
                            {
                                "feature_id": "feature-example-processing",
                                "feature_name": "示例处理",
                                "description": "处理示例数据",
                                "confidence": "confirmed",
                                "evidence_files": [],
                                "routes": [],
                                "api_endpoints": [],
                                "screenshots": [],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            report = consistency_tool.validate_consistency(application, material_root, manifest, selection, evidence_map, root)
            rule_ids = {item["rule_id"] for item in report["findings"]}
            self.assertIn("CONFIRMED_FEATURE_SOURCE_MISSING", rule_ids)
            self.assertIn("CONFIRMED_FEATURE_SCREENSHOT_MISSING", rule_ids)

    def test_blocks_source_line_count_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_root, application, manifest, selection, evidence_map = self.base_inputs(root)
            data = json.loads(application.read_text(encoding="utf-8"))
            data["fields"]["source_line_count"]["value"] = 999
            application.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            report = consistency_tool.validate_consistency(application, material_root, manifest, selection, evidence_map, root)
            self.assertIn("SOURCE_LINE_COUNT_MISMATCH", {item["rule_id"] for item in report["findings"]})

    def test_blocks_code_docx_without_selected_source_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_root, application, manifest, selection, evidence_map = self.base_inputs(root)
            formal = material_root / "03-正式资料"
            formal.mkdir()
            write_minimal_docx(formal / "示例业务系统_代码鉴别材料.docx", "示例业务系统 V1.0\n只有名称，没有源码")
            report = consistency_tool.validate_consistency(application, material_root, manifest, selection, evidence_map, root)
            self.assertIn("SELECTED_SOURCE_NOT_IN_CODE_DOCX", {item["rule_id"] for item in report["findings"]})

    def test_blocks_reordered_or_superstring_code_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_root, application, manifest, selection, evidence_map = self.base_inputs(root)
            formal = material_root / "03-正式资料"
            formal.mkdir()
            write_minimal_docx(
                formal / "示例业务系统_代码鉴别材料.docx",
                "示例业务系统 V1.0\n    return 10\n    return 1\ndef run():",
            )
            report = consistency_tool.validate_consistency(application, material_root, manifest, selection, evidence_map, root)
            self.assertIn("SELECTED_SOURCE_NOT_IN_CODE_DOCX", {item["rule_id"] for item in report["findings"]})

    def test_final_output_detects_placeholders_and_sensitive_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            material_root = Path(tmp) / "软件著作权申请资料"
            (material_root / "03-正式资料").mkdir(parents=True)
            (material_root / "04-校验报告").mkdir()
            (material_root / "03-正式资料" / "申请表信息.txt").write_text("待补充 此处略", encoding="utf-8")
            (material_root / "04-校验报告" / "run.log").write_text("api_key=SYNTHETIC_TEST_ONLY", encoding="utf-8")
            report = output_tool.validate_outputs(material_root)
            rule_ids = {item["rule_id"] for item in report["findings"]}
            self.assertIn("PLACEHOLDER_IN_FORMAL_OUTPUT", rule_ids)
            self.assertIn("SENSITIVE_DATA_IN_LOG_OR_TEST", rule_ids)

    def test_mode_b_audit_backs_up_hashes_and_never_modifies_original(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            existing = root / "existing-materials"
            existing.mkdir()
            original = existing / "操作手册.md"
            original_bytes = "# 示例业务系统 V1.0 操作手册\n\n用户执行真实操作。\n".encode("utf-8")
            original.write_bytes(original_bytes)
            material_root = root / "软件著作权申请资料"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "validate_outputs.py"),
                    str(material_root),
                    "--project-root",
                    str(root),
                    "--audit-existing",
                    str(existing),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 0, completed.stdout or completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "PASS")
            self.assertFalse(payload["modifications_performed"])
            self.assertFalse(payload["repair_authorized"])
            self.assertEqual(original.read_bytes(), original_bytes)
            record = payload["files"][0]
            self.assertTrue(record["hash_matches"])
            backup = material_root / record["backup_path"]
            self.assertEqual(backup.read_bytes(), original_bytes)
            self.assertFalse(bool(backup.stat().st_mode & stat.S_IWRITE))
            report_root = material_root / "04-校验报告"
            self.assertTrue((report_root / "material-audit-report.json").is_file())
            self.assertTrue((report_root / "material-audit-report.md").is_file())

    def test_mode_b_audit_blocks_placeholder_but_still_preserves_original(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            existing = root / "existing-materials"
            existing.mkdir()
            original = existing / "操作手册.md"
            original_bytes = "示例业务系统 V1.0 待补充\n".encode("utf-8")
            original.write_bytes(original_bytes)
            material_root = root / "软件著作权申请资料"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "validate_outputs.py"),
                    str(material_root),
                    "--project-root",
                    str(root),
                    "--audit-existing",
                    str(existing),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 2)
            payload = json.loads(completed.stdout)
            self.assertIn("PLACEHOLDER_IN_EXISTING_MATERIAL", {item["rule_id"] for item in payload["findings"]})
            self.assertEqual(original.read_bytes(), original_bytes)
            self.assertTrue((material_root / payload["files"][0]["backup_path"]).is_file())

    def test_mode_b_authorized_repair_is_bound_to_baseline_hashes_and_revalidated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            existing = root / "existing-materials"
            existing.mkdir()
            original = existing / "操作手册.md"
            before = "示例业务系统 V1.0 待补充\n".encode("utf-8")
            original.write_bytes(before)
            material_root = root / "软件著作权申请资料"
            command = [
                sys.executable,
                str(SCRIPTS / "validate_outputs.py"),
                str(material_root),
                "--project-root",
                str(root),
                "--audit-existing",
                str(existing),
            ]
            initial = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(initial.returncode, 2, initial.stdout)
            initial_payload = json.loads(initial.stdout)
            after = "# 示例业务系统 V1.0 操作手册\n\n用户执行已确认操作。\n".encode("utf-8")
            original.write_bytes(after)
            ledger = material_root / "01-草稿" / "repair-ledger.json"
            ledger.parent.mkdir(exist_ok=True)
            ledger.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "repair_authorized": True,
                        "authorized_by": "synthetic-test-user",
                        "authorized_at": "2026-07-12T12:00:00Z",
                        "baseline_report": initial_payload["immutable_report"],
                        "authorized_changes": [
                            {
                                "path": "操作手册.md",
                                "before_sha256": hashlib.sha256(before).hexdigest(),
                                "after_sha256": hashlib.sha256(after).hexdigest(),
                                "description": "删除占位文字并补入已确认操作说明",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            repaired = subprocess.run(
                [*command, "--repair-ledger", str(ledger)],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(repaired.returncode, 0, repaired.stdout or repaired.stderr)
            payload = json.loads(repaired.stdout)
            self.assertTrue(payload["repair_authorized"])
            self.assertTrue(payload["modifications_performed"])
            self.assertTrue(payload["revalidation_complete"])
            self.assertEqual(payload["authorized_changes"][0]["path"], "操作手册.md")

    def test_rejects_prefix_only_fake_screenshot_docx_and_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            material_root = Path(tmp) / "软件著作权申请资料"
            (material_root / "02-截图" / "images").mkdir(parents=True)
            (material_root / "03-正式资料").mkdir()
            (material_root / "04-校验报告" / "rendered").mkdir(parents=True)
            (material_root / "02-截图" / "screenshot-plan.md").write_text(
                "fake.png | page | / | data | action | feature | user | 2026-07-12", encoding="utf-8"
            )
            (material_root / "02-截图" / "images" / "fake.png").write_bytes(b"not-an-image")
            fake_docx = material_root / "03-正式资料" / "示例业务系统_操作手册.docx"
            with zipfile.ZipFile(fake_docx, "w") as archive:
                archive.writestr("word/document.xml", "<bad/>")
            fake_pdf = material_root / "04-校验报告" / "rendered" / "fake.pdf"
            fake_pdf.write_bytes(b"%PDF- fake")
            fake_record = {
                "input": "03-正式资料/示例业务系统_操作手册.docx",
                "input_sha256": hashlib.sha256(fake_docx.read_bytes()).hexdigest(),
                "artifact": "04-校验报告/rendered/fake.pdf",
                "page_count": 1,
                "renderer": "local-renderer",
                "command": "render",
                "rendered_at": "2026-07-12T12:00:00Z",
            }
            (material_root / "04-校验报告" / "render-report.md").write_text(
                "status: PASS\nvisual_validation: completed\nrepair_rounds: 1\n"
                f"render_record: {json.dumps(fake_record)}\n",
                encoding="utf-8",
            )
            report = output_tool.validate_outputs(material_root)
            rule_ids = {item["rule_id"] for item in report["findings"]}
            self.assertIn("SCREENSHOT_IMAGE_INVALID", rule_ids)
            self.assertIn("DOCX_PACKAGE_INVALID", rule_ids)
            self.assertIn("RENDER_ARTIFACT_INVALID", rule_ids)

    def test_real_decoders_reject_marker_only_jpeg_and_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_jpeg = root / "fake.jpg"
            fake_jpeg.write_bytes(bytes.fromhex("FFD8FFC0000B080001000101011100FFD9"))
            fake_pdf = root / "fake.pdf"
            fake_pdf.write_bytes(b"%PDF-1.4 xref trailer /Type /Page startxref 0 %%EOF")
            self.assertFalse(output_tool.validate_image(fake_jpeg))
            self.assertEqual(output_tool.pdf_page_count(fake_pdf), 0)

    def test_screenshot_and_manual_gates_reject_shallow_untraceable_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            material_root = Path(tmp) / "软件著作权申请资料"
            (material_root / "01-草稿").mkdir(parents=True)
            images = material_root / "02-截图" / "images"
            images.mkdir(parents=True)
            (material_root / "03-正式资料").mkdir()
            (material_root / "04-校验报告").mkdir()
            (material_root / "01-草稿" / "操作手册.md").write_text("一句话手册", encoding="utf-8")
            (material_root / "01-草稿" / "草稿自检记录.md").write_text("检查通过", encoding="utf-8")
            (material_root / "02-截图" / "screenshot-plan.md").write_text("screen.png | page", encoding="utf-8")
            (images / "screen.png").write_bytes(PNG_1X1)
            report = output_tool.validate_outputs(material_root)
            rule_ids = {item["rule_id"] for item in report["findings"]}
            self.assertIn("SCREENSHOT_DIMENSIONS_TOO_SMALL", rule_ids)
            self.assertIn("SCREENSHOT_METADATA_MISSING", rule_ids)
            self.assertIn("MANUAL_CONTENT_TOO_SHALLOW", rule_ids)
            self.assertIn("MANUAL_SELF_CHECK_INVALID", rule_ids)

    def test_standard_library_fallback_validates_real_jpeg_and_classic_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            jpeg = root / "screen.jpg"
            jpeg.write_bytes(JPEG_2X2)
            pdf = root / "rendered.pdf"
            write_minimal_pdf(pdf, "rendered material")

            real_import = __import__

            def import_without_pillow(name: str, *args: object, **kwargs: object) -> object:
                if name == "PIL" or name.startswith("PIL."):
                    raise ImportError("Pillow intentionally unavailable in fallback test")
                return real_import(name, *args, **kwargs)

            with mock.patch("builtins.__import__", side_effect=import_without_pillow):
                self.assertTrue(output_tool.validate_image(jpeg))
            with mock.patch.object(output_tool.shutil, "which", return_value=None):
                self.assertEqual(output_tool.pdf_page_count(pdf), 1)

    def test_rejects_stale_duplicate_render_mapping_and_wrong_page_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            material_root = Path(tmp) / "软件著作权申请资料"
            formal = material_root / "03-正式资料"
            reports = material_root / "04-校验报告"
            rendered = reports / "rendered"
            formal.mkdir(parents=True)
            rendered.mkdir(parents=True)
            manual = formal / "示例业务系统_操作手册.docx"
            code = formal / "示例业务系统_代码鉴别材料.docx"
            write_minimal_docx(manual, "示例业务系统 V1.0")
            write_minimal_docx(code, "示例业务系统 V1.0\ndef run():\n    return 1")
            artifact = rendered / "shared.pdf"
            write_minimal_pdf(artifact, "one page")
            records = [
                {
                    "input": "03-正式资料/示例业务系统_操作手册.docx",
                    "input_sha256": "0" * 64,
                    "artifact": "04-校验报告/rendered/shared.pdf",
                    "page_count": 2,
                    "renderer": "local-renderer",
                    "command": "render",
                    "rendered_at": "2026-07-12T12:00:00Z",
                },
                {
                    "input": "03-正式资料/示例业务系统_代码鉴别材料.docx",
                    "input_sha256": hashlib.sha256(code.read_bytes()).hexdigest(),
                    "artifact": "04-校验报告/rendered/shared.pdf",
                    "page_count": 1,
                    "renderer": "local-renderer",
                    "command": "render",
                    "rendered_at": "2026-07-12T12:00:00Z",
                },
            ]
            (reports / "render-report.md").write_text(
                "status: PASS\nvisual_validation: completed\nrepair_rounds: 1\n"
                + "".join(f"render_record: {json.dumps(item, ensure_ascii=False)}\n" for item in records),
                encoding="utf-8",
            )
            report = output_tool.validate_outputs(material_root)
            rule_ids = {item["rule_id"] for item in report["findings"]}
            self.assertIn("RENDER_INPUT_HASH_MISMATCH", rule_ids)
            self.assertIn("RENDER_ARTIFACT_DUPLICATE", rule_ids)
            self.assertIn("RENDER_PAGE_COUNT_MISMATCH", rule_ids)

    def test_consistency_cli_rejects_malformed_nested_json_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_root, application, manifest, selection, evidence_map = self.base_inputs(root)
            manifest.write_text(json.dumps({"project_root": str(root), "files": ["bad-shape"]}), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "validate_consistency.py"),
                    "--application",
                    str(application),
                    "--materials-root",
                    str(material_root),
                    "--source-manifest",
                    str(manifest),
                    "--selection",
                    str(selection),
                    "--evidence-map",
                    str(evidence_map),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 3)
            self.assertEqual(json.loads(completed.stdout)["status"], "ERROR")
            self.assertNotIn("Traceback", completed.stderr)

    def test_malformed_workflow_state_is_reported_not_raised(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            material_root = Path(tmp) / "软件著作权申请资料"
            material_root.mkdir()
            (material_root / "workflow-state.json").write_text(json.dumps({"stages": ["bad-shape"]}), encoding="utf-8")
            report = output_tool.validate_outputs(material_root)
            self.assertEqual(report["status"], "BLOCK")
            self.assertIn("WORKFLOW_STATE_INVALID", {item["rule_id"] for item in report["findings"]})
            completed = subprocess.run(
                [sys.executable, str(SCRIPTS / "validate_outputs.py"), str(material_root)],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 3)
            self.assertEqual(json.loads(completed.stdout)["status"], "ERROR")
            self.assertNotIn("Traceback", completed.stderr)

    def test_passed_workflow_stage_without_evidence_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            material_root = Path(tmp) / "软件著作权申请资料"
            material_root.mkdir()
            stages = {
                name: {
                    "status": "pending" if name == "final-review" else "pass",
                    "evidence": [],
                    "confirmed_by_user": False,
                }
                for name in output_tool.WORKFLOW_STAGES
            }
            state = {
                "schema_version": 1,
                "mode": "A",
                "project_root": str(Path(tmp).resolve()),
                "current_stage": "final-review",
                "stages": stages,
                "confirmations": {
                    "project": True,
                    "business": True,
                    "application_fields": True,
                    "code_selection": True,
                    "screenshot_method": True,
                    "markdown_bundle": True,
                },
                "formal_generation_authorized": True,
                "screenshot_method": "user",
                "updated_at": "2026-07-12T12:00:00Z",
            }
            (material_root / "workflow-state.json").write_text(json.dumps(state), encoding="utf-8")
            findings: list[dict] = []
            output_tool.validate_state(material_root, findings)
            self.assertIn("WORKFLOW_STAGE_EVIDENCE_MISSING", {item["rule_id"] for item in findings})

    def test_workflow_stage_rejects_unrelated_existing_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            material_root = Path(tmp) / "软件著作权申请资料"
            material_root.mkdir()
            unrelated = material_root / "foo.json"
            unrelated.write_text("{}", encoding="utf-8")
            stages = {
                name: {
                    "status": "pending" if name == "final-review" else "pass",
                    "evidence": [] if name == "final-review" else ["foo.json"],
                    "confirmed_by_user": False,
                }
                for name in output_tool.WORKFLOW_STAGES
            }
            state = {
                "schema_version": 1,
                "mode": "A",
                "project_root": str(Path(tmp).resolve()),
                "current_stage": "final-review",
                "stages": stages,
                "confirmations": {
                    "project": True,
                    "business": True,
                    "application_fields": True,
                    "code_selection": True,
                    "screenshot_method": True,
                    "markdown_bundle": True,
                },
                "formal_generation_authorized": True,
                "screenshot_method": "user",
                "updated_at": "2026-07-12T12:00:00Z",
            }
            (material_root / "workflow-state.json").write_text(json.dumps(state), encoding="utf-8")
            findings: list[dict] = []
            output_tool.validate_state(material_root, findings)
            self.assertIn("WORKFLOW_STAGE_EVIDENCE_MISMATCH", {item["rule_id"] for item in findings})

    def test_incomplete_business_and_evidence_schema_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            output_tool.validate_business_understanding_payload({"user_confirmed": True})
        with self.assertRaises(ValueError):
            consistency_tool.validate_evidence_map_payload(
                {"schema_version": 1, "features": [{"feature_name": "示例处理", "confidence": "confirmed"}]}
            )

    def test_git_tracking_detects_chinese_material_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            formal = root / "软件著作权申请资料" / "03-正式资料" / "申请表信息.txt"
            formal.parent.mkdir(parents=True)
            formal.write_text("sanitized", encoding="utf-8")
            initialized = subprocess.run(["git", "init", "-q", str(root)], capture_output=True)
            if initialized.returncode != 0:
                self.skipTest("git is unavailable")
            subprocess.run(["git", "-C", str(root), "add", "--", formal.relative_to(root).as_posix()], check=True, capture_output=True)
            tracked, state = output_tool.git_tracked_paths(root, [formal])
            self.assertEqual(state, "verified")
            self.assertIn("软件著作权申请资料/03-正式资料/申请表信息.txt", tracked)

    def test_provenance_report_contains_recorded_and_current_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_root, application, manifest, selection, evidence_map = self.base_inputs(root)
            formal = material_root / "03-正式资料"
            formal.mkdir()
            write_minimal_docx(formal / "示例业务系统_代码鉴别材料.docx", "示例业务系统 V1.0\ndef run():\n    return 1")
            provenance_path = material_root / "04-校验报告" / "provenance-report.md"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "validate_consistency.py"),
                    "--application",
                    str(application),
                    "--materials-root",
                    str(material_root),
                    "--source-manifest",
                    str(manifest),
                    "--selection",
                    str(selection),
                    "--evidence-map",
                    str(evidence_map),
                    "--provenance-report",
                    str(provenance_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertIn(completed.returncode, {1, 2})
            digest = hashlib.sha256((root / "src" / "service.py").read_bytes()).hexdigest()
            report_text = provenance_path.read_text(encoding="utf-8")
            self.assertIn(digest, report_text)
            self.assertIn("selected_content_sha256", report_text)

    def test_all_eight_clis_complete_bundle_stays_caution_and_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_source = root / "src" / "service.py"
            project_source.parent.mkdir()
            project_source.write_text("def run():\n    return 1\n", encoding="utf-8")
            (root / "app.py").write_text("from src.service import run\nprint(run())\n", encoding="utf-8")
            (root / "test_service.py").write_text(
                "import unittest\nfrom src.service import run\n"
                "class ServiceTests(unittest.TestCase):\n    def test_run(self): self.assertEqual(run(), 1)\n",
                encoding="utf-8",
            )
            frontend = root / "frontend" / "src"
            frontend.mkdir(parents=True)
            (frontend / "main.ts").write_text("export const value: number = 1;\n", encoding="utf-8")
            (root / "package.json").write_text(json.dumps({"dependencies": {"typescript": "test"}}), encoding="utf-8")
            (root / "README.md").write_text("Run python app.py and python -m unittest test_service.py", encoding="utf-8")
            (root / "LICENSE").write_text("Synthetic test license", encoding="utf-8")
            runtime_dir = root / "runtime-evidence"
            runtime_dir.mkdir()
            runtime_checks = []
            for kind, command in (
                ("startup", [sys.executable, "app.py"]),
                ("core-flow", [sys.executable, "-c", "from src.service import run; assert run() == 1"]),
                ("test", [sys.executable, "-m", "unittest", "test_service.py"]),
            ):
                completed = subprocess.run(command, cwd=root, capture_output=True, text=True, encoding="utf-8")
                self.assertEqual(completed.returncode, 0, completed.stdout or completed.stderr)
                log = runtime_dir / f"{kind}.log"
                log.write_text(
                    f"command={subprocess.list2cmdline(command)}\nexit_code={completed.returncode}\n"
                    f"stdout={completed.stdout}\nstderr={completed.stderr}\n",
                    encoding="utf-8",
                )
                relative_log = log.relative_to(root).as_posix()
                runtime_checks.append(
                    {
                        "kind": kind,
                        "command": subprocess.list2cmdline(command),
                        "cwd": ".",
                        "started_at": "2026-07-12T12:00:00Z",
                        "finished_at": "2026-07-12T12:00:01Z",
                        "passed": True,
                        "exit_code": completed.returncode,
                        "evidence_paths": [relative_log],
                        "evidence_sha256": {relative_log: hashlib.sha256(log.read_bytes()).hexdigest()},
                    }
                )
            runtime_path = root / "runtime-evidence.json"
            runtime_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "software_identity": {
                            "software_name": "示例业务系统",
                            "version": "V1.0",
                            "user_confirmed": True,
                        },
                        "checks": runtime_checks,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            material_root = root / "软件著作权申请资料"
            evidence_dir = material_root / "00-项目证据"
            draft_dir = material_root / "01-草稿"
            cli_commands = [
                [
                    sys.executable,
                    str(SCRIPTS / "check_environment.py"),
                    str(root),
                    "--initialize",
                    "--mode",
                    "A",
                ],
                [
                    sys.executable,
                    str(SCRIPTS / "analyze_project.py"),
                    str(root),
                    "--readiness",
                    "--runtime-evidence",
                    str(runtime_path),
                    "--output",
                    str(evidence_dir / "project-analysis.json"),
                ],
                [
                    sys.executable,
                    str(SCRIPTS / "collect_source_manifest.py"),
                    str(root),
                    "--output",
                    str(evidence_dir / "source-manifest.json"),
                ],
                [
                    sys.executable,
                    str(SCRIPTS / "count_source_lines.py"),
                    str(root),
                    "--manifest",
                    str(evidence_dir / "source-manifest.json"),
                    "--output",
                    str(evidence_dir / "source-line-count.json"),
                ],
                [
                    sys.executable,
                    str(SCRIPTS / "propose_code_selection.py"),
                    str(root),
                    "--manifest",
                    str(evidence_dir / "source-manifest.json"),
                    "--json-output",
                    str(draft_dir / "代码文件选择.json"),
                    "--markdown-output",
                    str(draft_dir / "代码文件候选清单.md"),
                ],
            ]
            for command in cli_commands:
                completed = subprocess.run(command, cwd=root, capture_output=True, text=True, encoding="utf-8")
                self.assertIn(completed.returncode, (0, 1), completed.stderr or completed.stdout)
                self.assertIsInstance(json.loads(completed.stdout), dict)
            for folder in ("00-项目证据", "01-草稿", "02-截图/images", "03-正式资料", "04-校验报告"):
                (material_root / folder).mkdir(parents=True, exist_ok=True)
            transition_script = str(SCRIPTS / "check_environment.py")

            def advance(stage: str, evidence: list[str], *extra: str) -> None:
                command = [sys.executable, transition_script, str(root), "--advance-stage", stage]
                for path in evidence:
                    command.extend(("--evidence", path))
                command.extend(extra)
                completed = subprocess.run(command, cwd=root, capture_output=True, text=True, encoding="utf-8")
                self.assertEqual(completed.returncode, 0, completed.stdout or completed.stderr)

            advance(
                "project",
                [
                    "00-项目证据/project-analysis.json",
                    "00-项目证据/source-manifest.json",
                    "00-项目证据/source-line-count.json",
                ],
                "--confirm",
            )
            advance(
                "readiness",
                ["04-校验报告/readiness-report.json", "04-校验报告/readiness-report.md"],
            )
            source_hash = hashlib.sha256(project_source.read_bytes()).hexdigest()
            (material_root / "00-项目证据" / "source-evidence-map.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "features": [
                            {
                                "feature_id": "feature-example-processing",
                                "feature_name": "示例处理",
                                "description": "处理示例数据并返回结果",
                                "evidence_files": ["src/service.py"],
                                "routes": [],
                                "api_endpoints": [],
                                "screenshots": ["screen.png"],
                                "confidence": "confirmed",
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (material_root / "01-草稿" / "业务理解.md").write_text("已确认业务理解", encoding="utf-8")
            (material_root / "01-草稿" / "业务理解.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "software_name": "示例业务系统",
                        "product_positioning": "用于验证真实材料链的本地业务系统",
                        "industry": "通用软件",
                        "target_users": ["本地验证用户"],
                        "core_value": ["可追溯处理"],
                        "business_features": [
                            {
                                "feature_name": "示例处理",
                                "description": "处理示例数据并返回结果",
                                "evidence_ids": ["feature-example-processing"],
                                "confidence": "confirmed",
                            }
                        ],
                        "operation_flows": ["进入系统后执行示例处理并查看结果"],
                        "page_modules": ["示例处理页"],
                        "manual_modules": [
                            {
                                "title": "示例处理",
                                "purpose": "处理示例数据",
                                "entry": "打开示例处理入口",
                                "visible_elements": ["处理按钮"],
                                "user_actions": ["执行处理"],
                                "input_or_state_rules": ["输入必须为示例数据"],
                                "error_feedback": ["输入无效时显示错误"],
                                "result_feedback": ["显示处理结果"],
                                "evidence_ids": ["feature-example-processing"],
                                "screenshot_ids": ["screen.png"],
                            }
                        ],
                        "application_purpose": "验证业务资料整理流程",
                        "main_functions": "处理示例数据并展示可核验结果。",
                        "technical_characteristics": "本地运行并保留来源记录。",
                        "system_requirements": {"runtime": "Python"},
                        "evidence_sources": ["src/service.py"],
                        "excluded_features": [],
                        "user_confirmed": True,
                        "confirmed_at": "2026-07-12T12:00:00Z",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            advance(
                "business",
                ["01-草稿/业务理解.json", "01-草稿/业务理解.md", "00-项目证据/source-evidence-map.json"],
                "--confirm",
            )
            (material_root / "01-草稿" / "申请表信息.md").write_text("示例业务系统 V1.0", encoding="utf-8")
            application_data = valid_application()
            line_count_payload = json.loads(
                (material_root / "00-项目证据" / "source-line-count.json").read_text(encoding="utf-8")
            )
            application_data["fields"]["source_line_count"]["value"] = line_count_payload["summary"]["total_source_lines"]
            application_path = material_root / "01-草稿" / "申请表信息.json"
            application_path.write_text(
                json.dumps(application_data, ensure_ascii=False), encoding="utf-8"
            )
            field_validation = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "validate_application_fields.py"),
                    str(application_path),
                    "--require-confirmed",
                ],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertIn(field_validation.returncode, (0, 1), field_validation.stderr or field_validation.stdout)
            self.assertIn(json.loads(field_validation.stdout)["status"], ("PASS", "CAUTION"))
            advance(
                "application-fields",
                ["01-草稿/申请表信息.json", "01-草稿/申请表信息.md"],
                "--confirm",
            )
            (material_root / "01-草稿" / "代码文件候选清单.md").write_text("src/service.py", encoding="utf-8")
            (material_root / "01-草稿" / "代码文件选择.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "user_confirmed": True,
                        "confirmed_at": "2026-07-12T12:00:00Z",
                        "candidates": [
                            {
                                "path": "src/service.py",
                                "selected": True,
                                "is_third_party": False,
                                "sha256": source_hash,
                                "selected_content_sha256": source_hash,
                                "user_confirmed": True,
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            advance(
                "code-selection",
                ["01-草稿/代码文件选择.json", "01-草稿/代码文件候选清单.md"],
                "--confirm",
            )
            (material_root / "01-草稿" / "操作手册.md").write_text(
                "# 示例业务系统 V1.0 操作手册\n\n"
                "用户从主菜单进入示例处理页面，确认页面显示处理按钮和输入区域后提交整数数据；输入为空时系统保持当前页面并显示错误。\n\n"
                "处理完成后页面显示可核验结果，用户可以对照原始输入确认结果；遇到非法状态时系统不保存数据并给出明确反馈。\n",
                encoding="utf-8",
            )
            (material_root / "01-草稿" / "草稿自检记录.md").write_text(
                "status: PASS\nreviewer: synthetic-test-reviewer\nreviewed_at: 2026-07-12T12:00:00Z\n"
                "evidence_mapping: PASS\nnatural_language: PASS\nno_template_marketing: PASS\n"
                "screenshot_mapping: PASS\nsensitive_data: PASS\n",
                encoding="utf-8",
            )
            screenshot = material_root / "02-截图" / "images" / "screen.png"
            screenshot.write_bytes(make_png(640, 480))
            screenshot_hash = hashlib.sha256(screenshot.read_bytes()).hexdigest()
            (material_root / "02-截图" / "screenshot-plan.md").write_text(
                "| 截图文件 | 对应页面 | 访问路径 | 前置数据 | 操作动作 | 证明的功能 | 采集方式 | 采集时间 | 证据 ID | 敏感信息 | SHA-256 |\n"
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
                f"| screen.png | 示例处理页 | /example | 脱敏测试数据 | 单击处理 | 示例处理 | user | 2026-07-12T12:00:00Z | feature-example-processing | 否 | {screenshot_hash} |\n",
                encoding="utf-8",
            )
            advance(
                "screenshot-method",
                ["02-截图/screenshot-plan.md", "02-截图/images/screen.png"],
                "--confirm",
                "--screenshot-method",
                "user",
            )
            advance(
                "markdown-draft",
                ["01-草稿/操作手册.md", "01-草稿/草稿自检记录.md"],
                "--confirm",
            )
            (material_root / "03-正式资料" / "申请表信息.txt").write_text(
                serialize_application_txt(application_data), encoding="utf-8"
            )
            manual_docx_path = material_root / "03-正式资料" / "示例业务系统_操作手册.docx"
            code_docx_path = material_root / "03-正式资料" / "示例业务系统_代码鉴别材料.docx"
            write_minimal_docx(
                manual_docx_path,
                "示例业务系统 V1.0\n示例处理",
                {"screen.png": screenshot.read_bytes()},
            )
            write_minimal_docx(code_docx_path, "示例业务系统 V1.0\ndef run():\n    return 1")
            advance(
                "formal-generation",
                [
                    "03-正式资料/申请表信息.txt",
                    "03-正式资料/示例业务系统_操作手册.docx",
                    "03-正式资料/示例业务系统_代码鉴别材料.docx",
                ],
                "--confirm",
                "--authorize-formal-generation",
            )
            reports = material_root / "04-校验报告"
            consistency_validation = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "validate_consistency.py"),
                    "--application",
                    str(application_path),
                    "--materials-root",
                    str(material_root),
                    "--source-manifest",
                    str(material_root / "00-项目证据" / "source-manifest.json"),
                    "--selection",
                    str(material_root / "01-草稿" / "代码文件选择.json"),
                    "--evidence-map",
                    str(material_root / "00-项目证据" / "source-evidence-map.json"),
                    "--project-root",
                    str(root),
                    "--report",
                    str(reports / "consistency-report.md"),
                    "--provenance-report",
                    str(reports / "provenance-report.md"),
                ],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertIn(
                consistency_validation.returncode,
                (0, 1),
                consistency_validation.stderr or consistency_validation.stdout,
            )
            self.assertIn(json.loads(consistency_validation.stdout)["status"], ("PASS", "CAUTION"))
            rendered = reports / "rendered"
            rendered.mkdir()
            write_minimal_pdf(rendered / "manual.pdf", "manual render")
            write_minimal_pdf(rendered / "code.pdf", "code render")
            manual_record = {
                "input": "03-正式资料/示例业务系统_操作手册.docx",
                "input_sha256": hashlib.sha256(manual_docx_path.read_bytes()).hexdigest(),
                "artifact": "04-校验报告/rendered/manual.pdf",
                "page_count": 1,
                "renderer": "verified-local-renderer",
                "command": "verified local render command",
                "rendered_at": "2026-07-12T12:00:00Z",
            }
            code_record = {
                "input": "03-正式资料/示例业务系统_代码鉴别材料.docx",
                "input_sha256": hashlib.sha256(code_docx_path.read_bytes()).hexdigest(),
                "artifact": "04-校验报告/rendered/code.pdf",
                "page_count": 1,
                "renderer": "verified-local-renderer",
                "command": "verified local render command",
                "rendered_at": "2026-07-12T12:00:00Z",
            }
            (reports / "render-report.md").write_text(
                "status: PASS\n"
                "visual_validation: completed\n"
                "repair_rounds: 1\n"
                f"render_record: {json.dumps(manual_record, ensure_ascii=False)}\n"
                f"render_record: {json.dumps(code_record, ensure_ascii=False)}\n",
                encoding="utf-8",
            )
            advance(
                "render-validation",
                [
                    "04-校验报告/consistency-report.md",
                    "04-校验报告/provenance-report.md",
                    "04-校验报告/render-report.md",
                ],
            )
            (reports / "final-checklist.md").write_text("status: PASS\n", encoding="utf-8")
            report = output_tool.validate_outputs(material_root, write_manifest=True)
            self.assertEqual(report["status"], "CAUTION", report["findings"])
            self.assertFalse(report["submission_ready"])
            final_rule_ids = {item["rule_id"] for item in report["findings"]}
            self.assertIn("OFFICIAL_FORM_NOT_CURRENTLY_VERIFIED", final_rule_ids)
            self.assertIn("VALIDATION_REPORT_CAUTION", final_rule_ids)
            manifest = json.loads((reports / "output-manifest.json").read_text(encoding="utf-8"))
            self.assertNotIn("04-校验报告/output-manifest.json", {item["path"] for item in manifest["files"]})
            completed = subprocess.run(
                [sys.executable, str(SCRIPTS / "validate_outputs.py"), str(material_root)],
                cwd=Path(tmp),
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 1, completed.stdout or completed.stderr)
            self.assertFalse(json.loads(completed.stdout)["submission_ready"])
            updated_state = json.loads((material_root / "workflow-state.json").read_text(encoding="utf-8"))
            self.assertEqual(updated_state["stages"]["final-review"]["status"], "caution")
            self.assertEqual(
                updated_state["stages"]["final-review"]["evidence"],
                ["04-校验报告/final-checklist.md", "04-校验报告/output-manifest.json"],
            )
            state_before_failure = (material_root / "workflow-state.json").read_bytes()
            failed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "validate_outputs.py"),
                    str(material_root),
                    "--output",
                    str(reports),
                ],
                cwd=Path(tmp),
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(failed.returncode, 3)
            self.assertEqual(json.loads(failed.stdout)["status"], "ERROR")
            self.assertEqual((material_root / "workflow-state.json").read_bytes(), state_before_failure)
            self.assertNotIn("Traceback", failed.stderr)


if __name__ == "__main__":
    unittest.main()
