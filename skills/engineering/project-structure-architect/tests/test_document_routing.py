from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from structure_core import audit_structure, detect_project, scaffold_project, suggest_path


@pytest.mark.parametrize("blueprint", ["competition-workspace", "document-workspace"])
def test_pre_code_workspace_can_bootstrap_and_route_documents(tmp_path: Path, blueprint: str) -> None:
    root = tmp_path / "workspace"
    result = scaffold_project(root, blueprint, "项目或比赛")
    assert result["status"] == "PASS"
    assert detect_project(root)["selected_blueprint"] == blueprint
    assert (root / "README.md").is_file()
    assert not (root / "src").exists()
    assert not (root / "skill-outputs").exists()
    route = suggest_path(root, artifact="documentation", document_kind="guide", name="赛题入门指南.md")
    assert route["status"] == "PASS"
    assert route["path"] == "docs/guides/赛题入门指南.md"
    target = root / route["path"]
    target.parent.mkdir(parents=True)
    target.write_text("# 赛题说明", encoding="utf-8")
    assert audit_structure(root)["status"] == "PASS"


def test_document_routing_preserves_existing_chinese_root(tmp_path: Path) -> None:
    (tmp_path / "文档").mkdir()
    route = suggest_path(tmp_path, artifact="doc", document_kind="plan", name="参赛计划.md")
    assert route["path"] == "文档/plans/参赛计划.md"
    assert not (tmp_path / "docs").exists()


def test_document_roots_with_equal_ownership_are_not_silently_chosen(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "文档").mkdir()
    route = suggest_path(tmp_path, artifact="doc", document_kind="guide", name="入门.md")
    assert route["status"] == "BLOCK"
    assert route["path"] is None


def test_document_route_can_follow_an_explicit_project_contract(tmp_path: Path) -> None:
    root = tmp_path / "project"
    scaffold_project(root, "competition-workspace", "比赛")
    manifest_path = root / ".project-structure.yaml"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["directories"].append({"path": "比赛文档", "purpose": "参赛说明", "required": False})
    manifest["document_routes"] = {"guide": "比赛文档/入门"}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    route = suggest_path(root, artifact="documentation", document_kind="guide", name="赛题.md")
    assert route["path"] == "比赛文档/入门/赛题.md"


@pytest.mark.parametrize("destination", ["../outside", "/outside", "skill-outputs/new", "skill-output/new"])
def test_document_contract_cannot_escape_or_reintroduce_skill_buckets(tmp_path: Path, destination: str) -> None:
    scaffold_project(tmp_path, "competition-workspace", "比赛")
    path = tmp_path / ".project-structure.yaml"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["document_routes"] = {"guide": destination}
    path.write_text(json.dumps(manifest), encoding="utf-8")
    route = suggest_path(tmp_path, artifact="doc", document_kind="guide", name="入门.md")
    assert route["status"] == "BLOCK"
    assert route["path"] is None


def test_existing_reports_boundary_is_reused(tmp_path: Path) -> None:
    (tmp_path / "reports").mkdir()
    route = suggest_path(tmp_path, artifact="doc", document_kind="report", name="结果分析.md")
    assert route["path"] == "reports/结果分析.md"


def test_report_owner_precedes_ambiguity_in_general_document_roots(tmp_path: Path) -> None:
    for name in ("docs", "文档", "reports"):
        (tmp_path / name).mkdir()
    route = suggest_path(tmp_path, artifact="doc", document_kind="report", name="报告.md")
    assert route["status"] == "PASS"
    assert route["path"] == "reports/报告.md"


def test_new_skill_bucket_is_rejected_but_legacy_files_are_preserved(tmp_path: Path) -> None:
    scaffold_project(tmp_path, "competition-workspace", "比赛")
    legacy = tmp_path / "skill-outputs/project-dev-zh/旧说明.md"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("历史说明", encoding="utf-8")
    route = suggest_path(tmp_path, artifact="directory", name="skill-outputs", owner="project")
    assert route["status"] == "BLOCK"
    audit = audit_structure(tmp_path)
    assert audit["status"] == "CAUTION"
    assert any(item["rule_id"] == "LEGACY_SKILL_OUTPUTS" for item in audit["findings"])
    assert legacy.read_text(encoding="utf-8") == "历史说明"


def test_cli_routes_a_guide_without_writing_it(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts/suggest_path.py"
    result = subprocess.run(
        [sys.executable, str(script), str(tmp_path), "--artifact", "documentation",
         "--document-kind", "guide", "--name", "入门指南.md"],
        capture_output=True, text=True, encoding="utf-8", check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["path"] == "docs/guides/入门指南.md"
    assert list(tmp_path.iterdir()) == []
