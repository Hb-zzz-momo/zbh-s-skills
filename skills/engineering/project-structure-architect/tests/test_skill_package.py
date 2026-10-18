from __future__ import annotations

import re
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


def test_skill_entry_is_concise_complete_and_has_no_placeholders() -> None:
    content = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8-sig")
    lines = content.splitlines()
    assert len(lines) < 500
    assert "TODO" not in content
    assert lines[0] == "---"
    assert lines[1] == "name: project-structure-architect"
    closing = lines.index("---", 1)
    frontmatter_keys = {
        line.split(":", 1)[0]
        for line in lines[1:closing]
        if ":" in line and not line.startswith(" ")
    }
    assert frontmatter_keys == {"name", "description"}
    assert "新建项目" in content
    assert "运行期" in content
    assert "PASS / CAUTION / BLOCK" in content


def test_openai_metadata_matches_skill_creator_contract() -> None:
    content = (SKILL_ROOT / "agents/openai.yaml").read_text(encoding="utf-8-sig")
    assert 'display_name: "项目结构架构师"' in content
    assert "short_description:" in content
    assert "$project-structure-architect" in content


def test_required_references_assets_and_scripts_are_present() -> None:
    expected = {
        "references/project-detection.md",
        "references/structure-decision-matrix.md",
        "references/file-placement-rules.md",
        "references/naming-conventions.md",
        "references/source-provenance.md",
        "references/blueprints/web-fullstack-separated.md",
        "references/blueprints/web-typescript-monorepo.md",
        "references/blueprints/react-frontend.md",
        "references/blueprints/python-backend.md",
        "references/blueprints/research-step-based.md",
        "references/blueprints/data-science.md",
        "references/blueprints/machine-learning-pipeline.md",
        "references/blueprints/python-library.md",
        "references/blueprints/microservices.md",
        "scripts/detect_project.py",
        "scripts/render_tree.py",
        "scripts/scaffold_project.py",
        "scripts/suggest_path.py",
        "scripts/audit_structure.py",
        "assets/PROJECT_STRUCTURE.md.template",
        "assets/project-structure.yaml.template",
        "assets/AGENTS.md.template",
    }
    missing = sorted(path for path in expected if not (SKILL_ROOT / path).is_file())
    assert missing == []


def test_every_reference_longer_than_100_lines_has_a_toc() -> None:
    for path in (SKILL_ROOT / "references").rglob("*.md"):
        content = path.read_text(encoding="utf-8-sig")
        if len(content.splitlines()) > 100:
            assert re.search(r"(?im)^## (目录|Table of Contents)$", content), path


def test_source_provenance_has_commit_license_and_borrowing_boundary() -> None:
    content = (SKILL_ROOT / "references/source-provenance.md").read_text(
        encoding="utf-8-sig"
    )
    for source in (
        "github/awesome-copilot",
        "vercel/turborepo",
        "agentskills/agentskills",
        "microsoft/skills",
        "addyosmani/agent-skills",
    ):
        assert source in content
    assert "commit" in content.lower()
    assert "license" in content.lower() or "许可证" in content
    assert "借鉴边界" in content


def test_templates_expose_no_unresolved_todo_markers() -> None:
    for name in (
        "PROJECT_STRUCTURE.md.template",
        "project-structure.yaml.template",
        "AGENTS.md.template",
    ):
        content = (SKILL_ROOT / "assets" / name).read_text(encoding="utf-8-sig")
        assert "TODO" not in content
        assert content.strip()
