from __future__ import annotations

import json
from pathlib import Path

from structure_core import (
    add_research_step,
    audit_structure,
    detect_project,
    scaffold_project,
    suggest_path,
)


def write(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def file_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file()
    }


def test_pass_react_fastapi_generates_frontend_backend(tmp_path: Path) -> None:
    root = tmp_path / "fullstack"
    scaffold_project(root, "web-fullstack-separated", "Portal")
    assert (root / "frontend/src/features").is_dir()
    assert (root / "backend/app/api/routes").is_dir()
    assert audit_structure(root)["status"] == "PASS"


def test_pass_typescript_multi_app_generates_apps_packages(tmp_path: Path) -> None:
    root = tmp_path / "suite"
    scaffold_project(root, "web-typescript-monorepo", "Suite")
    assert (root / "apps/web").is_dir()
    assert (root / "apps/admin").is_dir()
    assert (root / "packages/ui").is_dir()
    assert audit_structure(root)["status"] == "PASS"


def test_pass_research_generates_required_lifecycle_tree(tmp_path: Path) -> None:
    root = tmp_path / "study"
    scaffold_project(root, "research-step-based", "Study", package_name="study")
    for directory in ("data", "steps", "src", "experiments", "outputs", "paper"):
        assert (root / directory).is_dir()


def test_pass_steps_only_orchestrate_and_core_logic_lives_in_src(tmp_path: Path) -> None:
    root = tmp_path / "study"
    scaffold_project(root, "research-step-based", "Study", package_name="study")
    write(root / "steps/01_train/run.py", "from study.models.training import train\ntrain()")
    write(root / "src/study/models/training.py", "def train():\n    return 1\n")
    assert audit_structure(root)["status"] == "PASS"


def test_pass_new_react_feature_has_one_feature_path(tmp_path: Path) -> None:
    root = tmp_path / "web"
    scaffold_project(root, "react-frontend", "Web")
    result = suggest_path(
        root,
        artifact="frontend-feature",
        name="LoginForm.tsx",
        owner="authentication",
    )
    assert result["status"] == "PASS"
    assert result["path"] == "src/features/authentication/components/LoginForm.tsx"


def test_pass_new_research_stage_gets_number_and_readme(tmp_path: Path) -> None:
    root = tmp_path / "study"
    scaffold_project(root, "research-step-based", "Study", package_name="study")
    add_research_step(root, "data acquisition")
    second = add_research_step(root, "data cleaning")
    assert second["step_path"] == "steps/02_data_cleaning"
    assert (root / "steps/02_data_cleaning/README.md").is_file()


def test_pass_existing_apps_packages_is_not_rewritten(tmp_path: Path) -> None:
    root = tmp_path / "existing"
    write(root / "package.json", '{"workspaces":["apps/*","packages/*"]}')
    write(root / "turbo.json", "{}")
    write(root / "apps/web/src/index.ts", "export {}")
    write(root / "packages/ui/src/index.ts", "export {}")
    before = file_snapshot(root)
    detection = detect_project(root)
    report = audit_structure(root)
    after = file_snapshot(root)
    assert detection["selected_blueprint"] == "web-typescript-monorepo"
    assert report["actions_applied"] == []
    assert before == after
    assert not (root / "frontend").exists()


def test_pass_every_important_directory_has_a_responsibility(tmp_path: Path) -> None:
    root = tmp_path / "service"
    scaffold_project(root, "python-backend", "Service", package_name="service")
    manifest = json.loads((root / ".project-structure.yaml").read_text(encoding="utf-8"))
    required = [item for item in manifest["directories"] if item["required"]]
    assert required
    assert all(item["purpose"].strip() for item in required)


def test_pass_file_responsibility_yields_one_recommended_path(tmp_path: Path) -> None:
    root = tmp_path / "service"
    scaffold_project(root, "python-backend", "Service", package_name="service")
    result = suggest_path(
        root,
        artifact="backend-service",
        name="billing.py",
        owner="billing",
    )
    assert result["status"] == "PASS"
    assert result["path"] == "app/services/billing.py"
    assert result["alternatives"] == []


def test_fail_different_projects_do_not_receive_one_universal_tree(tmp_path: Path) -> None:
    web = tmp_path / "web"
    research = tmp_path / "research"
    scaffold_project(web, "react-frontend", "Web")
    scaffold_project(research, "research-step-based", "Research", package_name="research")
    web_dirs = {path.relative_to(web).parts[0] for path in web.iterdir()}
    research_dirs = {path.relative_to(research).parts[0] for path in research.iterdir()}
    assert web_dirs != research_dirs
    assert (web / "src/features").is_dir()
    assert (research / "steps").is_dir()


def test_fail_web_frontend_backend_and_deployment_mixed_in_root_src(tmp_path: Path) -> None:
    root = tmp_path / "mixed"
    scaffold_project(root, "web-fullstack-separated", "Mixed")
    write(root / "src/App.tsx", "export default function App() {}")
    write(root / "src/main.py", "from fastapi import FastAPI")
    write(root / "src/deployment.yaml", "kind: Deployment")
    report = audit_structure(root)
    assert report["status"] == "BLOCK"
    assert "MIXED_ROOT_SOURCE" in {item["rule_id"] for item in report["findings"]}


def test_fail_research_code_models_data_and_figures_all_in_steps(tmp_path: Path) -> None:
    root = tmp_path / "study"
    scaffold_project(root, "research-step-based", "Study", package_name="study")
    write(root / "steps/01_everything/model.py", "\n".join(["x = 1"] * 220))
    write(root / "steps/01_everything/data.csv", "x,y\n1,2")
    write(root / "steps/01_everything/figure.png", "not-a-real-png")
    report = audit_structure(root)
    rule_ids = {item["rule_id"] for item in report["findings"]}
    assert report["status"] == "BLOCK"
    assert "REUSABLE_LOGIC_IN_STEP" in rule_ids
    assert "DATA_OR_OUTPUT_IN_STEP" in rule_ids


def test_fail_common_utils_misc_temp_without_reason(tmp_path: Path) -> None:
    root = tmp_path / "bad"
    scaffold_project(root, "python-library", "Bad", package_name="bad")
    for name in ("common", "utils", "misc", "temp"):
        write(root / name / "file.txt", "x")
    report = audit_structure(root)
    findings = [item for item in report["findings"] if item["rule_id"] == "AMBIGUOUS_DIRECTORY"]
    assert report["status"] == "BLOCK"
    assert {item["path"] for item in findings} == {"common", "utils", "misc", "temp"}


def test_fail_clear_existing_structure_is_not_mass_reorganized(tmp_path: Path) -> None:
    root = tmp_path / "existing"
    write(root / "apps/web/src/main.ts", "export {}")
    write(root / "apps/api/src/main.ts", "export {}")
    write(root / "packages/types/src/index.ts", "export type Id = string")
    write(root / "package.json", '{"workspaces":["apps/*","packages/*"]}')
    write(root / "turbo.json", "{}")
    before = file_snapshot(root)

    report = audit_structure(root, blueprint_id="web-fullstack-separated")

    assert report["status"] in {"CAUTION", "BLOCK"}
    assert report["actions_applied"] == []
    assert file_snapshot(root) == before
    assert not (root / "frontend").exists()

