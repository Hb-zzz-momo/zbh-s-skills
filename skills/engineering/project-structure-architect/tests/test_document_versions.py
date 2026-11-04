"""Exercise actual topic/role routing without moving any user files."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from structure_core import scaffold_project, suggest_path


@pytest.mark.parametrize("role,folder", [("draft", "编辑稿"), ("snapshot", "发布快照"), ("history", "历史版本"), ("records", "制作与核对记录")])
def test_topic_roles_are_physical_and_routing_is_readonly(tmp_path, role, folder):
    revision = "2026-11-04_v1.0" if role in {"snapshot", "history"} else None
    result = suggest_path(tmp_path, artifact="doc", name="活动推文.md", topic="活动宣传", document_role=role, revision=revision)
    filename = f"活动推文_{revision}.md" if revision else "活动推文.md"
    assert result["status"] == "PASS", result
    assert result["path"] == f"活动宣传/{folder}/{filename}"
    assert list(tmp_path.iterdir()) == []


def test_parallel_uses_have_separate_versions_without_slugging_chinese(tmp_path):
    paths = [suggest_path(tmp_path, artifact="doc", name="主持稿.docx", topic="主持稿", document_role="draft", variant=variant)["path"] for variant in ("上午场", "下午场")]
    assert paths == ["主持稿/并列用途/上午场/编辑稿/主持稿.docx", "主持稿/并列用途/下午场/编辑稿/主持稿.docx"]


def test_editable_source_and_frozen_export_can_coexist(tmp_path):
    draft = suggest_path(tmp_path, artifact="doc", name="报告.docx", topic="调研报告")
    path = tmp_path / draft["path"]
    path.parent.mkdir(parents=True)
    path.write_bytes(b"editable source")
    again = suggest_path(tmp_path, artifact="doc", name="报告.docx", topic="调研报告", document_role="draft")
    snapshot = suggest_path(tmp_path, artifact="doc", name="报告.pdf", topic="调研报告", document_role="snapshot", revision="v1.0")
    assert again["status"] == snapshot["status"] == "PASS"
    assert again["path"] == draft["path"]
    assert snapshot["path"] == "调研报告/发布快照/报告_v1.0.pdf"
    assert path.read_bytes() == b"editable source"


@pytest.mark.parametrize("role", ["snapshot", "history"])
def test_frozen_roles_require_revision_and_never_overwrite(tmp_path, role):
    missing = suggest_path(tmp_path, artifact="doc", name="方案.md", topic="赛事方案", document_role=role)
    assert missing["status"] == "BLOCK" and missing["path"] is None
    first = suggest_path(tmp_path, artifact="doc", name="方案.md", topic="赛事方案", document_role=role, revision="v1.0")
    target = tmp_path / first["path"]
    target.parent.mkdir(parents=True)
    target.write_text("frozen", encoding="utf-8")
    again = suggest_path(tmp_path, artifact="doc", name="方案.md", topic="赛事方案", document_role=role, revision="v1.0")
    assert again["status"] == "BLOCK" and again["path"] is None
    assert target.read_text(encoding="utf-8") == "frozen"


@pytest.mark.parametrize("topic", ["../outside", "skill-outputs/活动宣传", "活动宣传/SKILL-OUTPUTS", "活动宣传/../报告", "C:/outside"])
def test_topics_cannot_escape_or_reintroduce_skill_buckets(tmp_path, topic):
    result = suggest_path(tmp_path, artifact="doc", name="方案.md", topic=topic)
    assert result["status"] == "BLOCK" and result["path"] is None
    assert list(tmp_path.iterdir()) == []


def test_role_without_topic_is_not_silently_put_in_generic_docs(tmp_path):
    result = suggest_path(tmp_path, artifact="doc", name="报告.md", document_role="draft")
    assert result["status"] == "BLOCK" and result["path"] is None


def test_existing_manifest_boundary_is_still_enforced(tmp_path):
    scaffold_project(tmp_path, "document-workspace", "项目")
    result = suggest_path(tmp_path, artifact="doc", name="报告.md", topic="报告")
    assert result["status"] == "BLOCK"
    manifest = tmp_path / ".project-structure.yaml"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["directories"].append({"path": "报告", "purpose": "用户报告", "required": False})
    manifest.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    assert suggest_path(tmp_path, artifact="doc", name="报告.md", topic="报告")["status"] == "PASS"


def test_long_full_path_is_caution_not_proof_of_application_support(tmp_path):
    result = suggest_path(tmp_path, artifact="doc", name="a" * 180 + ".docx", topic="活动宣传")
    assert result["status"] == "CAUTION", result
    assert result["path_checks"]["full_path_utf16_units"] >= 240
    assert result["path_checks"]["application_open_verified"] is False
    assert result["path_checks"]["cloud_sync_verified"] is False


def test_cli_exposes_topic_variant_and_revision_without_writing(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts/suggest_path.py"
    command = [sys.executable, str(script), str(tmp_path), "--artifact", "doc", "--name", "主持稿.md", "--topic", "主持稿", "--variant", "上午场", "--document-role", "snapshot", "--revision", "2026-11-04_v1.0"]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["path"] == "主持稿/并列用途/上午场/发布快照/主持稿_上午场_2026-11-04_v1.0.md"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("topic", [".", "./活动宣传", "活动宣传/发布快照", "活动宣传/编辑稿", "活动宣传/并列用途/上午场", "活动宣传/历史版本", "活动宣传/制作与核对记录"])
def test_topic_must_not_be_a_role_or_normalized_root_alias(tmp_path, topic):
    result = suggest_path(tmp_path, artifact="doc", name="方案.md", topic=topic)
    assert result["status"] == "BLOCK" and result["path"] is None


@pytest.mark.parametrize("variant", ["编辑稿", "发布快照", "历史版本", "制作与核对记录", "并列用途", "."])
def test_parallel_use_must_not_be_a_version_role(tmp_path, variant):
    result = suggest_path(tmp_path, artifact="doc", name="方案.md", topic="赛事方案", variant=variant)
    assert result["status"] == "BLOCK" and result["path"] is None


def test_snapshot_name_keeps_use_and_does_not_repeat_revision(tmp_path):
    result = suggest_path(tmp_path, artifact="doc", name="主持稿_v1.0.md", topic="主持稿", document_role="snapshot", revision="v1.0", variant="上午场")
    assert result["path"] == "主持稿/并列用途/上午场/发布快照/主持稿_上午场_v1.0.md"
    repeated = suggest_path(tmp_path, artifact="doc", name="主持稿_上午场_v1.0.md", topic="主持稿", document_role="snapshot", revision="v1.0", variant="上午场")
    assert repeated["path"] == result["path"]


@pytest.mark.parametrize("field", ["--name", "--variant", "--revision"])
@pytest.mark.parametrize("value", ["./", ".\\", "上午场/"])
def test_cli_single_name_fields_reject_normalized_path_aliases(tmp_path, field, value):
    script = Path(__file__).resolve().parents[1] / "scripts/suggest_path.py"
    command = [sys.executable, str(script), str(tmp_path), "--artifact", "doc", "--name", "方案.md", "--topic", "活动宣传"]
    if field == "--revision":
        command += ["--document-role", "snapshot"]
    result = subprocess.run(command + [field, value], capture_output=True, text=True, encoding="utf-8")
    assert result.returncode != 0, result.stdout
    assert json.loads(result.stdout).get("path") is None
    assert list(tmp_path.iterdir()) == []
