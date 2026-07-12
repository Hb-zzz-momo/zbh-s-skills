from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
SKILLS_ROOT = REPO_ROOT / "skills"
START = "<!-- project-structure-architect:gate:v1:start -->"
END = "<!-- project-structure-architect:gate:v1:end -->"

REQUIRED = {
    "api-and-interface-design",
    "browser-testing-with-devtools",
    "ci-cd-and-automation",
    "code-simplification",
    "context-engineering",
    "debugging-and-error-recovery",
    "deprecation-and-migration",
    "documentation-and-adrs",
    "frontend-ui-engineering",
    "idea-refine",
    "incremental-implementation",
    "performance-optimization",
    "planning-and-task-breakdown",
    "security-and-hardening",
    "shipping-and-launch",
    "source-driven-development",
    "spec-driven-development",
    "test-driven-development",
    "using-agent-skills",
    "exam-answer-zh",
    "lab-report-coach-zh",
    "engineering-skill-flow-zh",
    "project-dev-zh",
    "project-handoff-zh",
    "project-kickoff-delivery-zh",
    "web-design-workflow-zh",
    "iteration-reflection-guard-zh",
    "plan-faithful-execution-zh",
    "skill-router-zh",
    "subagent-orchestration-zh",
    "workflow-forge-zh",
    "info-evidence-chain-zh",
    "knowledge-digest-zh",
    "project-docs-knowledge-log-zh",
    "agent-wait-monitor-zh",
    "artifact-curator-zh",
    "ppt-data-storytelling-zh",
    "ppt-reference-library-zh",
    "ppt-render-qa-zh",
    "ppt-speaker-delivery-zh",
    "ppt-story-design-zh",
    "ppt-visual-system-zh",
    "ppt-workflow-orchestrator-zh",
    "pptx-builder-zh",
    "pptx-ci-zh",
    "pptx-template-editor-zh",
    "software-copyright-zh",
    "decisive-result-audit-zh",
    "research-coach-zh",
    "research-experiment-ops-zh",
    "research-figure-generation-zh",
    "research-iteration-audit-zh",
    "research-skill-flow-zh",
    "research-statistics-reporting-zh",
    "paper-format-fixer-zh",
    "paper-writing-zh",
    "translation-zh",
}
EXEMPTIONS = {
    "code-review-and-quality",
    "doubt-driven-development",
    "git-workflow-and-versioning",
}
PROVIDER = "project-structure-architect"


def skill_files() -> dict[str, Path]:
    result: dict[str, Path] = {}
    for path in SKILLS_ROOT.rglob("SKILL.md"):
        if "scripts" in path.parts or "references" in path.parts:
            continue
        content = path.read_text(encoding="utf-8-sig")
        match = re.search(r"(?m)^name:\s*[\"']?([^\n\"']+)", content)
        assert match, path
        result[match.group(1).strip()] = path
    return result


def test_every_workflow_is_classified_required_exempt_or_provider() -> None:
    names = set(skill_files())
    assert names == REQUIRED | EXEMPTIONS | {PROVIDER}
    assert len(REQUIRED) == 57


def test_required_workflows_have_exactly_one_gate_after_h1() -> None:
    files = skill_files()
    for name in sorted(REQUIRED):
        content = files[name].read_text(encoding="utf-8-sig")
        assert content.count(START) == 1, (name, "start")
        assert content.count(END) == 1, (name, "end")
        h1 = re.search(r"(?m)^# .+$", content)
        assert h1, name
        start = content.index(START)
        end = content.index(END)
        assert h1.start() < start < end
        assert not re.search(r"(?m)^## .+$", content[h1.end() : start]), name
        assert "project-structure-architect" in content[start:end]


def test_exemptions_and_provider_do_not_get_recursive_gate() -> None:
    files = skill_files()
    for name in sorted(EXEMPTIONS | {PROVIDER}):
        content = files[name].read_text(encoding="utf-8-sig")
        assert START not in content, name
        assert END not in content, name


def test_global_router_and_registry_generator_contain_structure_route() -> None:
    agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8-sig")
    routing = (SKILLS_ROOT / "SKILL_ROUTING.zh-CN.md").read_text(encoding="utf-8-sig")
    router = (SKILLS_ROOT / "guardrail/skill-router-zh/SKILL.md").read_text(
        encoding="utf-8-sig"
    )
    generator = (SKILLS_ROOT / "scripts/Update-SkillsReadme.ps1").read_text(
        encoding="utf-8-sig"
    )
    readme = (SKILLS_ROOT / "README.md").read_text(encoding="utf-8-sig")
    assert "全局项目结构门禁" in agents
    assert "project-structure-architect" in routing
    assert "项目结构 / 文件树" in routing
    assert "project-structure-architect" in router
    assert "'project-structure-architect'" in generator
    assert "initializes or restructures a project" in generator
    assert "engineering/project-structure-architect/" in readme
    assert "initializes or restructures a project" in readme
    assert "node_modules" in generator
    assert not re.search(r"(?m)^\s+node_modules/$", readme)
