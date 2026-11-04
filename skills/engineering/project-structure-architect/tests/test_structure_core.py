from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

import structure_core

from structure_core import (
    BLUEPRINT_IDS,
    StructureError,
    add_research_step,
    audit_structure,
    detect_project,
    load_blueprint,
    render_tree,
    scaffold_project,
    status_exit_code,
    suggest_path,
)


EXPECTED_BLUEPRINTS = {
    "web-fullstack-separated",
    "web-typescript-monorepo",
    "react-frontend",
    "python-backend",
    "research-step-based",
    "data-science",
    "machine-learning-pipeline",
    "python-library",
    "microservices",
    "competition-workspace",
    "document-workspace",
}


def write(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def file_snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_all_documented_blueprints_are_machine_loadable() -> None:
    assert set(BLUEPRINT_IDS) == EXPECTED_BLUEPRINTS
    for blueprint_id in sorted(EXPECTED_BLUEPRINTS):
        blueprint = load_blueprint(blueprint_id)
        assert blueprint["id"] == blueprint_id
        assert blueprint["classification"]["purpose"]
        assert blueprint["directories"]
        assert all(item["path"] and item["purpose"] for item in blueprint["directories"])


def test_missing_blueprint_resource_is_not_masked_by_a_builtin_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(structure_core, "BLUEPRINT_ROOT", tmp_path)
    with pytest.raises(StructureError) as exc_info:
        load_blueprint("react-frontend")
    assert exc_info.value.code == "BLUEPRINT_NOT_FOUND"


@pytest.mark.parametrize(
    ("marker_builder", "expected"),
    [
        (
            lambda root: (
                write(root / "frontend/package.json", '{"dependencies":{"react":"latest"}}'),
                write(root / "backend/pyproject.toml", 'dependencies=["fastapi"]'),
            ),
            "web-fullstack-separated",
        ),
        (
            lambda root: (
                write(root / "package.json", '{"workspaces":["apps/*","packages/*"]}'),
                write(root / "turbo.json", "{}"),
                (root / "apps/web").mkdir(parents=True),
                (root / "packages/ui").mkdir(parents=True),
            ),
            "web-typescript-monorepo",
        ),
        (
            lambda root: write(
                root / "package.json",
                '{"dependencies":{"react":"latest"},"devDependencies":{"vite":"latest"}}',
            ),
            "react-frontend",
        ),
        (
            lambda root: write(root / "pyproject.toml", 'dependencies=["fastapi"]'),
            "python-backend",
        ),
        (
            lambda root: [
                (root / name).mkdir(parents=True)
                for name in ("data", "steps", "src", "experiments", "outputs", "paper")
            ],
            "research-step-based",
        ),
        (
            lambda root: [
                (root / name).mkdir(parents=True)
                for name in ("data/raw", "data/interim", "data/processed", "notebooks", "models", "reports")
            ],
            "data-science",
        ),
        (
            lambda root: (
                (root / "src/demo/pipelines/training").mkdir(parents=True),
                (root / "experiments").mkdir(),
                (root / "checkpoints").mkdir(),
            ),
            "machine-learning-pipeline",
        ),
        (
            lambda root: (
                write(root / "pyproject.toml", "[project]\nname='demo'"),
                (root / "src/demo").mkdir(parents=True),
                (root / "tests").mkdir(),
            ),
            "python-library",
        ),
        (
            lambda root: (
                write(root / "services/api/Dockerfile", "FROM python:3.14"),
                write(root / "services/worker/Dockerfile", "FROM python:3.14"),
                (root / "infra").mkdir(),
            ),
            "microservices",
        ),
    ],
)
def test_detection_selects_the_closest_blueprint(
    tmp_path: Path, marker_builder, expected: str
) -> None:
    marker_builder(tmp_path)
    result = detect_project(tmp_path)
    assert result["selected_blueprint"] == expected
    assert result["evidence"]
    assert result["classification"]["purpose"]


def test_ambiguous_detection_is_explicit_and_conservative(tmp_path: Path) -> None:
    write(tmp_path / "package.json", '{"dependencies":{"react":"latest"}}')
    write(tmp_path / "pyproject.toml", 'dependencies=["fastapi"]')

    result = detect_project(tmp_path)

    assert result["status"] == "CAUTION"
    assert result["needs_confirmation"] is True
    assert result["selected_blueprint"] in {
        "react-frontend",
        "python-backend",
        "web-fullstack-separated",
    }
    assert result["alternatives"]
    assert result["ambiguities"]


@pytest.mark.parametrize(("framework", "label"), [("vue", "Vue"), ("svelte", "Svelte")])
def test_non_react_frontend_is_labeled_and_requires_blueprint_adaptation(
    tmp_path: Path,
    framework: str,
    label: str,
) -> None:
    write(
        tmp_path / "package.json",
        json.dumps({"dependencies": {framework: "latest"}, "devDependencies": {"vite": "latest"}}),
    )

    result = detect_project(tmp_path)

    assert result["selected_blueprint"] == "react-frontend"
    assert result["status"] == "CAUTION"
    assert result["needs_confirmation"] is True
    assert label in result["technology_stack"]
    assert result["classification"]["stacks"] == [label]
    assert any("adapt" in item.lower() for item in result["ambiguities"])
    assert "Python" not in result["technology_stack"]


def test_snakefile_alone_is_an_ambiguous_scientific_workflow_candidate(tmp_path: Path) -> None:
    write(tmp_path / "Snakefile", "rule all:\n    input: 'outputs/result.csv'")

    result = detect_project(tmp_path)

    assert result["selected_blueprint"] in {
        "machine-learning-pipeline",
        "research-step-based",
    }
    assert result["status"] == "CAUTION"
    assert result["needs_confirmation"] is True
    assert "Snakemake" in result["technology_stack"]
    assert any("Snakefile" in item for item in result["evidence"])
    assert result["alternatives"]


def test_detection_reports_react_and_spring_java_stack(tmp_path: Path) -> None:
    write(tmp_path / "frontend/package.json", '{"dependencies":{"react":"latest"}}')
    write(
        tmp_path / "backend/pom.xml",
        "<dependency><groupId>org.springframework.boot</groupId>"
        "<artifactId>spring-boot-starter-web</artifactId></dependency>",
    )
    write(tmp_path / "backend/src/main/java/com/example/Application.java", "class Application {}")

    result = detect_project(tmp_path)

    assert result["selected_blueprint"] == "web-fullstack-separated"
    assert result["status"] == "PASS"
    assert {"React", "Java", "Spring"}.issubset(result["technology_stack"])


def test_detection_reports_stack_conventions_and_preserves_existing_over_manifest(
    tmp_path: Path,
) -> None:
    write(tmp_path / "package.json", '{"workspaces":["apps/*","packages/*"]}')
    write(tmp_path / "turbo.json", "{}")
    (tmp_path / "apps/web").mkdir(parents=True)
    (tmp_path / "packages/ui").mkdir(parents=True)
    write(
        tmp_path / ".project-structure.yaml",
        json.dumps(
            {
                "schema_version": "1.0",
                "blueprint": "web-fullstack-separated",
                "directories": [],
            }
        ),
    )

    result = detect_project(tmp_path)

    assert result["status"] == "CAUTION"
    assert result["selected_blueprint"] == "web-typescript-monorepo"
    assert "TypeScript" in result["technology_stack"]
    assert "apps/packages" in result["existing_conventions"]
    assert any("manifest" in item.lower() for item in result["ambiguities"])


def test_empty_directory_requires_confirmation(tmp_path: Path) -> None:
    result = detect_project(tmp_path)
    assert result["status"] == "CAUTION"
    assert result["selected_blueprint"] is None
    assert result["needs_confirmation"] is True
    assert result["technology_stack"] == []


def test_render_tree_is_sorted_and_excludes_generated_content(tmp_path: Path) -> None:
    write(tmp_path / "src/z.py")
    write(tmp_path / "src/a.py")
    write(tmp_path / "node_modules/pkg/index.js")
    write(tmp_path / "dist/bundle.js")

    tree = render_tree(tmp_path, max_depth=4)

    assert tree.index("a.py") < tree.index("z.py")
    assert "node_modules" not in tree
    assert "dist" not in tree


def test_scaffold_renders_manifest_docs_and_nested_agents(tmp_path: Path) -> None:
    target = tmp_path / "portal"
    result = scaffold_project(
        target,
        blueprint_id="web-fullstack-separated",
        project_name="Portal",
        package_name="portal",
        shared_contracts=True,
    )

    assert result["status"] == "PASS"
    assert (target / "frontend/src/features").is_dir()
    assert (target / "backend/app/services").is_dir()
    assert (target / "contracts").is_dir()
    assert (target / "PROJECT_STRUCTURE.md").is_file()
    assert (target / "AGENTS.md").is_file()
    assert (target / "frontend/AGENTS.md").is_file()
    assert (target / "backend/AGENTS.md").is_file()

    manifest = json.loads((target / ".project-structure.yaml").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "1.0"
    assert manifest["blueprint"] == "web-fullstack-separated"
    assert manifest["project_name"] == "Portal"
    assert isinstance(manifest["classification"], dict)
    assert manifest["adaptations"] == []
    assert manifest["exceptions"] == []
    assert "| 目录 |" in (target / "PROJECT_STRUCTURE.md").read_text(encoding="utf-8")
    assert "{{" not in (target / "PROJECT_STRUCTURE.md").read_text(encoding="utf-8")


def test_scaffold_uses_required_assets_and_does_not_invent_dependency_versions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "web"
    scaffold_project(target, "web-fullstack-separated", "Web")
    assert not (target / "frontend/package.json").exists()
    assert not (target / "backend/pyproject.toml").exists()
    assert not (target / "infrastructure").exists()

    missing_assets = tmp_path / "missing-assets"
    missing_assets.mkdir()
    monkeypatch.setattr(structure_core, "ASSET_ROOT", missing_assets)
    with pytest.raises(StructureError) as exc_info:
        scaffold_project(tmp_path / "blocked", "python-library", "Blocked")
    assert exc_info.value.code == "ASSET_NOT_FOUND"
    assert not (tmp_path / "blocked").exists()


def test_scaffold_dry_run_does_not_write(tmp_path: Path) -> None:
    target = tmp_path / "dry-run"
    result = scaffold_project(
        target,
        blueprint_id="python-library",
        project_name="Demo",
        dry_run=True,
    )
    assert result["status"] == "PASS"
    assert result["dry_run"] is True
    assert not target.exists()


def test_scaffold_refuses_nonempty_target_and_preserves_existing_file(tmp_path: Path) -> None:
    target = tmp_path / "existing"
    write(target / "README.md", "user content")

    with pytest.raises(StructureError, match="non-empty"):
        scaffold_project(target, "python-library", "Demo")

    assert (target / "README.md").read_text(encoding="utf-8") == "user content"


def test_scaffold_allow_existing_only_adds_missing_files(tmp_path: Path) -> None:
    target = tmp_path / "existing"
    write(target / "README.md", "keep me")

    result = scaffold_project(
        target,
        blueprint_id="python-library",
        project_name="Demo",
        allow_existing=True,
    )

    assert result["status"] == "CAUTION"
    assert (target / "README.md").read_text(encoding="utf-8") == "keep me"
    assert "README.md" in result["preserved_paths"]


def test_scaffold_existing_inventory_prunes_generated_dependency_trees(
    tmp_path: Path,
) -> None:
    target = tmp_path / "existing"
    write(target / "README.md", "keep me")
    for index in range(200):
        write(target / f"node_modules/pkg-{index}/index.js", "export {}")

    result = scaffold_project(
        target,
        blueprint_id="python-library",
        project_name="Demo",
        allow_existing=True,
        dry_run=True,
    )

    assert result["status"] == "CAUTION"
    assert result["preserved_paths"] == ["README.md"]


def test_scaffold_allow_existing_blocks_conflicting_coherent_structure(tmp_path: Path) -> None:
    target = tmp_path / "monorepo"
    write(target / "package.json", '{"workspaces":["apps/*","packages/*"]}')
    write(target / "turbo.json", "{}")
    write(target / "apps/web/src/index.ts", "export {}")
    write(target / "packages/ui/src/index.ts", "export {}")
    before = file_snapshot(target)

    with pytest.raises(StructureError) as error:
        scaffold_project(
            target,
            blueprint_id="web-fullstack-separated",
            project_name="Existing",
            allow_existing=True,
        )

    assert error.value.code == "BLUEPRINT_CONFLICT"
    assert file_snapshot(target) == before
    assert not (target / "frontend").exists()
    assert not (target / "backend").exists()


def test_scaffold_records_explicit_technology_adaptation(tmp_path: Path) -> None:
    root = tmp_path / "portal"
    scaffold_project(
        root,
        "web-fullstack-separated",
        "Portal",
        technology_stack=["React", "FastAPI"],
    )

    manifest = json.loads((root / ".project-structure.yaml").read_text(encoding="utf-8"))
    assert manifest["classification"]["stacks"] == ["React", "FastAPI"]
    assert manifest["adaptations"] == ["Explicit technology stack: React, FastAPI"]
    assert "React" in (root / "PROJECT_STRUCTURE.md").read_text(encoding="utf-8")
    assert {"React", "FastAPI"}.issubset(detect_project(root)["technology_stack"])


def test_project_structure_tree_marks_leaf_directories(tmp_path: Path) -> None:
    root = tmp_path / "library"
    scaffold_project(root, "python-library", "Library", package_name="library")
    document = (root / "PROJECT_STRUCTURE.md").read_text(encoding="utf-8")

    assert re.search(r"(?m)[├└]── unit/$", document)
    assert re.search(r"(?m)[├└]── development/$", document)


def test_every_blueprint_conditional_can_be_enabled(tmp_path: Path) -> None:
    for blueprint_id in BLUEPRINT_IDS:
        blueprint = load_blueprint(blueprint_id)
        conditions = sorted(
            {
                str(item["conditional"])
                for item in blueprint["directories"]
                if item.get("conditional")
            }
        )
        result = scaffold_project(
            tmp_path / blueprint_id,
            blueprint_id,
            blueprint_id,
            package_name="sample",
            enabled_options=conditions,
            dry_run=True,
        )
        for item in blueprint["directories"]:
            if not item.get("conditional"):
                continue
            expected = str(item["path"]).replace("{package_name}", "sample")
            expected = expected.replace("{project_name_slug}", blueprint_id.replace("-", "_"))
            assert expected in result["created_directories"], (blueprint_id, expected)
        assert all(result["options"][condition] for condition in conditions)


def test_scaffold_rejects_unknown_blueprint_option(tmp_path: Path) -> None:
    with pytest.raises(StructureError) as error:
        scaffold_project(
            tmp_path / "library",
            "python-library",
            "Library",
            enabled_options=["not_a_real_option"],
        )
    assert error.value.code == "UNKNOWN_BLUEPRINT_OPTION"


def test_scaffold_rolls_back_its_own_new_files_on_write_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "rollback"
    original_open = Path.open
    exclusive_open_count = 0

    def failing_open(path: Path, mode: str = "r", *args: object, **kwargs: object):
        nonlocal exclusive_open_count
        if mode == "x":
            exclusive_open_count += 1
            if exclusive_open_count == 2:
                raise OSError("injected write failure")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", failing_open)

    with pytest.raises(OSError, match="injected write failure"):
        scaffold_project(root, "python-library", "Rollback", package_name="rollback")

    assert not root.exists()


def test_research_step_creation_uses_next_number_without_renumbering(tmp_path: Path) -> None:
    (tmp_path / "steps/01_data_acquisition").mkdir(parents=True)
    (tmp_path / "steps/03_model_training").mkdir()

    result = add_research_step(tmp_path, "statistical analysis")

    assert result["status"] == "PASS"
    assert result["step_path"] == "steps/04_statistical_analysis"
    assert (tmp_path / result["step_path"] / "README.md").is_file()
    assert (tmp_path / result["step_path"] / "config.yaml").is_file()
    assert (tmp_path / result["step_path"] / "run.py").is_file()
    assert (tmp_path / "steps/03_model_training").is_dir()
    run = subprocess.run(
        [sys.executable, "run.py"],
        cwd=tmp_path / result["step_path"],
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    assert run.returncode == 0, run.stderr
    assert json.loads(run.stdout)["status"] == "PASS"


def test_suggest_path_routes_feature_local_and_shared_frontend_api(tmp_path: Path) -> None:
    write(tmp_path / "package.json", '{"dependencies":{"react":"latest"}}')

    local = suggest_path(
        tmp_path,
        artifact="frontend-api",
        name="users.ts",
        owner="authentication",
        scope="local",
    )
    shared = suggest_path(
        tmp_path,
        artifact="frontend-api",
        name="http-client.ts",
        owner="authentication",
        scope="shared",
    )

    assert local["status"] == "PASS"
    assert local["path"] == "src/features/authentication/api/users.ts"
    assert shared["path"] == "src/services/http-client.ts"
    assert local["path"] != shared["path"]


def test_suggest_path_preserves_existing_front_abbreviation(tmp_path: Path) -> None:
    (tmp_path / "front/src/features").mkdir(parents=True)
    (tmp_path / "backend/app").mkdir(parents=True)

    result = suggest_path(
        tmp_path,
        artifact="frontend-feature",
        name="LoginForm.tsx",
        owner="authentication",
    )

    assert result["path"] == "front/src/features/authentication/components/LoginForm.tsx"
    assert "existing convention" in result["reason"].lower()


def test_suggest_path_for_research_logic_and_step_is_unique(tmp_path: Path) -> None:
    for directory in ("steps", "src/demo", "experiments"):
        (tmp_path / directory).mkdir(parents=True)
    write(tmp_path / "pyproject.toml", "[project]\nname='demo'")

    logic = suggest_path(
        tmp_path,
        artifact="research-code",
        name="trainer.py",
        owner="models",
    )
    step = suggest_path(
        tmp_path,
        artifact="research-step",
        name="validation",
        sequence=9,
    )

    assert logic["path"] == "src/demo/models/trainer.py"
    assert step["path"] == "steps/09_validation/run.py"
    assert "steps/09_validation/README.md" in step["companion_paths"]


@pytest.mark.parametrize(
    ("artifact", "name", "owner", "expected"),
    [
        ("data-external", "source.csv", None, "data/external/source.csv"),
        ("data-raw", "observations.csv", None, "data/raw/observations.csv"),
        ("data-interim", "joined.parquet", None, "data/interim/joined.parquet"),
        ("data-processed", "training.parquet", None, "data/processed/training.parquet"),
        ("output-model", "model.pkl", None, "outputs/models/model.pkl"),
        ("output-figure", "overview.png", None, "outputs/figures/overview.png"),
        ("output-table", "metrics.csv", None, "outputs/tables/metrics.csv"),
        ("output-log", "formal.log", None, "outputs/logs/formal.log"),
        ("notebook", "analysis.ipynb", "01_exploration", "notebooks/01_exploration/analysis.ipynb"),
        ("pipeline", "nodes.py", "training", "src/study/pipelines/training/nodes.py"),
        ("python-module", "metrics.py", "evaluation", "src/study/evaluation/metrics.py"),
        ("script", "run_report.py", None, "scripts/run_report.py"),
        ("paper", "main.tex", "manuscript", "paper/manuscript/main.tex"),
        ("app", "admin", None, "apps/admin"),
        ("package", "validation", None, "packages/validation"),
        ("service", "api", None, "services/api"),
    ],
)
def test_suggest_path_covers_all_documented_persistent_artifact_categories(
    tmp_path: Path, artifact: str, name: str, owner: str | None, expected: str
) -> None:
    for directory in ("steps", "src/study", "experiments", "outputs", "paper"):
        (tmp_path / directory).mkdir(parents=True, exist_ok=True)
    write(tmp_path / "pyproject.toml", "[project]\nname='study'")

    result = suggest_path(tmp_path, artifact=artifact, name=name, owner=owner)

    assert result["status"] == "PASS"
    assert result["path"] == expected
    assert result["artifact"] == artifact
    assert "responsibility" in result


def test_suggest_path_blocks_source_code_in_raw_data(tmp_path: Path) -> None:
    (tmp_path / "data/raw").mkdir(parents=True)
    result = suggest_path(tmp_path, artifact="data-raw", name="generate.py")
    assert result["status"] == "BLOCK"
    assert result["path"] is None
    assert result["rule_id"] == "RAW_DATA_SOURCE_FORBIDDEN"


def test_suggest_path_returns_companion_tests_for_implementation(tmp_path: Path) -> None:
    (tmp_path / "app/services").mkdir(parents=True)
    service = suggest_path(
        tmp_path,
        artifact="backend-service",
        name="billing.py",
        owner="billing",
    )
    assert "tests/unit/services/test_billing.py" in service["companion_paths"]

    (tmp_path / "src/study/models").mkdir(parents=True)
    research = suggest_path(
        tmp_path,
        artifact="research-code",
        name="trainer.py",
        owner="models",
    )
    assert "tests/unit/models/test_trainer.py" in research["companion_paths"]

    assert service["owner"] == "billing"
    assert service["reuse_scope"] == "local"
    assert service["file_category"] == "backend-service"
    assert service["existing_equivalent_directories"] == ["app/services"]
    assert service["inputs"]
    assert service["outputs"] == [service["path"], *service["companion_paths"]]
    assert service["needs_confirmation"] is False


def test_web_backend_companion_test_stays_inside_backend_boundary(tmp_path: Path) -> None:
    root = tmp_path / "web"
    scaffold_project(root, "web-fullstack-separated", "Web")

    route = suggest_path(
        root,
        artifact="backend-route",
        name="health.py",
        owner="health",
    )

    assert route["path"] == "backend/app/api/routes/health.py"
    assert route["companion_paths"] == ["backend/tests/unit/routes/test_health.py"]
    write(root / route["path"], "def health(): return {'status': 'ok'}")
    write(root / route["companion_paths"][0], "def test_health(): assert True")
    assert audit_structure(root)["status"] == "PASS"


def test_monorepo_api_companion_test_stays_inside_api_app(tmp_path: Path) -> None:
    (tmp_path / "apps/api/src/services").mkdir(parents=True)

    service = suggest_path(
        tmp_path,
        artifact="backend-service",
        name="billing.py",
        owner="billing",
    )

    assert service["path"] == "apps/api/src/services/billing.py"
    assert service["companion_paths"] == ["apps/api/tests/unit/services/test_billing.py"]


def test_multi_app_frontend_route_requires_explicit_application(tmp_path: Path) -> None:
    write(tmp_path / "package.json", '{"workspaces":["apps/*","packages/*"]}')
    write(tmp_path / "turbo.json", "{}")
    write(tmp_path / "apps/customer-portal/src/index.ts", "export {}")
    write(tmp_path / "apps/operations-console/src/index.ts", "export {}")
    write(tmp_path / "packages/ui/src/index.ts", "export {}")

    ambiguous = suggest_path(
        tmp_path,
        artifact="frontend-feature",
        name="BillingPage.tsx",
        owner="billing",
    )
    selected = suggest_path(
        tmp_path,
        artifact="frontend-feature",
        name="BillingPage.tsx",
        owner="billing",
        application="customer-portal",
    )

    assert ambiguous["status"] == "BLOCK"
    assert ambiguous["path"] is None
    assert ambiguous["rule_id"] == "AMBIGUOUS_FRONTEND_APP"
    assert ambiguous["alternatives"] == [
        "apps/customer-portal/src",
        "apps/operations-console/src",
    ]
    assert selected["status"] == "PASS"
    assert selected["path"] == (
        "apps/customer-portal/src/features/billing/components/BillingPage.tsx"
    )
    assert not (tmp_path / "src").exists()


def test_suggest_path_rejects_traversal_and_unscoped_common(tmp_path: Path) -> None:
    with pytest.raises(StructureError, match="file name"):
        suggest_path(tmp_path, artifact="documentation", name="../secrets.md")

    result = suggest_path(
        tmp_path,
        artifact="directory",
        name="common",
        scope="shared",
    )
    assert result["status"] == "BLOCK"
    assert result["path"] is None
    assert result["rule_id"] == "UNSCOPED_AMBIGUOUS_DIRECTORY"

    ownerless = suggest_path(
        tmp_path,
        artifact="directory",
        name="domain-adapters",
    )
    assert ownerless["status"] == "BLOCK"
    assert ownerless["rule_id"] == "OWNER_REQUIRED_FOR_DIRECTORY"


@pytest.mark.parametrize(
    "unsafe_name",
    ["file.txt:stream", "bad?.py", "bad*.py", "bad<name>.py", "trailing. ", "control\x01.py"],
)
def test_suggest_path_rejects_windows_unsafe_names(
    tmp_path: Path, unsafe_name: str
) -> None:
    with pytest.raises(StructureError) as error:
        suggest_path(tmp_path, artifact="documentation", name=unsafe_name)
    assert error.value.code == "UNSAFE_FILE_NAME"


def test_scaffold_rejects_display_name_template_injection(tmp_path: Path) -> None:
    target = tmp_path / "injected"
    with pytest.raises(StructureError) as error:
        scaffold_project(target, "python-library", "Safe\n## Injected")
    assert error.value.code == "INVALID_PROJECT_NAME"
    assert not target.exists()


def test_research_step_rejects_wrong_blueprint_and_display_injection(tmp_path: Path) -> None:
    web = tmp_path / "web"
    scaffold_project(web, "react-frontend", "Web")
    with pytest.raises(StructureError) as wrong_blueprint:
        add_research_step(web, "training")
    assert wrong_blueprint.value.code == "RESEARCH_STEP_NOT_ALLOWED"
    assert not (web / "steps").exists()

    research = tmp_path / "research"
    scaffold_project(research, "research-step-based", "Research", package_name="study")
    with pytest.raises(StructureError) as injection:
        add_research_step(research, "Safe\n## Injected")
    assert injection.value.code == "INVALID_STEP_NAME"
    assert not any(path.name.endswith("injected") for path in (research / "steps").iterdir())


def test_manifest_contract_blocks_route_to_undeclared_boundary(tmp_path: Path) -> None:
    root = tmp_path / "library"
    scaffold_project(root, "python-library", "Library", package_name="library")

    result = suggest_path(root, artifact="app", name="admin")
    step = suggest_path(root, artifact="research-step", name="training")

    assert result["status"] == "BLOCK"
    assert result["path"] is None
    assert result["rule_id"] == "UNDECLARED_TARGET_BOUNDARY"
    assert step["status"] == "BLOCK"
    assert step["rule_id"] == "UNDECLARED_TARGET_BOUNDARY"


def test_invalid_manifest_blocks_route_step_and_existing_scaffold(tmp_path: Path) -> None:
    root = tmp_path / "research"
    scaffold_project(root, "research-step-based", "Study", package_name="study")
    write(root / ".project-structure.yaml", "{broken")
    before = file_snapshot(root)

    route = suggest_path(
        root,
        artifact="research-code",
        name="model.py",
        owner="models",
    )
    with pytest.raises(StructureError) as step_error:
        add_research_step(root, "training")
    with pytest.raises(StructureError) as scaffold_error:
        scaffold_project(
            root,
            "research-step-based",
            "Study",
            package_name="study",
            allow_existing=True,
        )

    assert route["status"] == "BLOCK"
    assert route["rule_id"] == "INVALID_STRUCTURE_MANIFEST"
    assert step_error.value.code == "INVALID_STRUCTURE_MANIFEST"
    assert scaffold_error.value.code == "INVALID_STRUCTURE_MANIFEST"
    assert file_snapshot(root) == before


def test_microservice_backend_route_requires_existing_service(tmp_path: Path) -> None:
    root = tmp_path / "services"
    scaffold_project(root, "microservices", "Services")

    result = suggest_path(
        root,
        artifact="backend-service",
        name="billing.py",
        owner="billing",
    )

    assert result["status"] == "BLOCK"
    assert result["rule_id"] == "UNKNOWN_SERVICE"
    assert result["path"] is None


@pytest.mark.parametrize(
    ("blueprint", "artifact", "name", "owner", "expected"),
    [
        (
            "web-fullstack-separated",
            "frontend-feature",
            "LoginPanel.tsx",
            "authentication",
            "frontend/src/features/authentication/components/LoginPanel.tsx",
        ),
        (
            "web-typescript-monorepo",
            "frontend-feature",
            "LoginPanel.tsx",
            "authentication",
            "apps/web/src/features/authentication/components/LoginPanel.tsx",
        ),
        (
            "react-frontend",
            "frontend-feature",
            "LoginPanel.tsx",
            "authentication",
            "src/features/authentication/components/LoginPanel.tsx",
        ),
        (
            "python-backend",
            "backend-service",
            "billing.py",
            "billing",
            "app/services/billing.py",
        ),
        (
            "research-step-based",
            "research-code",
            "model.py",
            "models",
            "src/sample/models/model.py",
        ),
        (
            "data-science",
            "output-figure",
            "overview.png",
            None,
            "reports/figures/overview.png",
        ),
        (
            "machine-learning-pipeline",
            "pipeline",
            "nodes.py",
            "training",
            "src/sample/pipelines/training/nodes.py",
        ),
        (
            "python-library",
            "python-module",
            "api.py",
            "core",
            "src/sample/core/api.py",
        ),
        (
            "microservices",
            "backend-service",
            "health.py",
            "api",
            "services/api/src/services/health.py",
        ),
    ],
)
def test_all_blueprints_route_create_and_audit_close(
    tmp_path: Path,
    blueprint: str,
    artifact: str,
    name: str,
    owner: str | None,
    expected: str,
) -> None:
    root = tmp_path / blueprint
    scaffold_project(root, blueprint, blueprint, package_name="sample")

    result = suggest_path(root, artifact=artifact, name=name, owner=owner)

    assert result["status"] == "PASS", result
    assert result["path"] == expected
    for relative in result["outputs"]:
        write(root / relative, "")
    assert audit_structure(root)["status"] == "PASS"


def test_audit_clean_scaffold_passes(tmp_path: Path) -> None:
    scaffold_project(tmp_path / "clean", "research-step-based", "Study", package_name="study")
    report = audit_structure(tmp_path / "clean")
    assert report["status"] == "PASS"
    assert report["summary"]["block"] == 0
    assert report["summary"]["caution"] == 0


def test_scaffold_resolves_blueprint_tokens_in_manifest_and_local_agents(
    tmp_path: Path,
) -> None:
    root = tmp_path / "research"
    scaffold_project(root, "research-step-based", "Study", package_name="study")

    checked = [
        root / ".project-structure.yaml",
        root / "PROJECT_STRUCTURE.md",
        root / "steps/AGENTS.md",
    ]
    for path in checked:
        assert "{package_name}" not in path.read_text(encoding="utf-8")


def test_audit_reports_drift_with_stable_rule_ids_and_never_moves_files(tmp_path: Path) -> None:
    root = tmp_path / "drift"
    scaffold_project(root, "research-step-based", "Study", package_name="study")
    write(root / "misc/notes.txt", "unscoped")
    write(root / "model.py", "class Model: pass")
    write(root / "steps/05_training/model.py", "\n".join(["x = 1"] * 220))
    write(root / "outputs/source.py", "print('mixed')")
    write(root / "data/raw/generated.py", "print('not raw data')")
    before = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())

    report = audit_structure(root)
    after = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
    rule_ids = {finding["rule_id"] for finding in report["findings"]}

    assert report["status"] == "BLOCK"
    assert {
        "AMBIGUOUS_DIRECTORY",
        "ROOT_SOURCE_FILE",
        "REUSABLE_LOGIC_IN_STEP",
        "SOURCE_IN_GENERATED_OUTPUT",
        "RAW_DATA_CONTAMINATION",
    }.issubset(rule_ids)
    assert before == after


def test_audit_detects_app_specific_code_in_shared_package(tmp_path: Path) -> None:
    root = tmp_path / "monorepo"
    scaffold_project(root, "web-typescript-monorepo", "Suite")
    write(root / "packages/ui/src/apps/admin-only.ts", "export const value = 1")

    report = audit_structure(root)
    assert "APP_CODE_IN_SHARED_PACKAGE" in {
        finding["rule_id"] for finding in report["findings"]
    }


def test_audit_blocks_large_reusable_logic_in_step_run_entry(tmp_path: Path) -> None:
    root = tmp_path / "research"
    scaffold_project(root, "research-step-based", "Study", package_name="study")
    step = add_research_step(root, "training")
    write(
        root / step["step_path"] / "run.py",
        "\n".join(f"def algorithm_{index}(): return {index}" for index in range(300)),
    )

    report = audit_structure(root)

    assert report["status"] == "BLOCK"
    assert "REUSABLE_LOGIC_IN_STEP" in {
        finding["rule_id"] for finding in report["findings"]
    }


def test_audit_detects_synonyms_unknown_roots_and_reusable_script_logic(tmp_path: Path) -> None:
    root = tmp_path / "library"
    scaffold_project(root, "python-library", "Library", package_name="library")
    (root / "front").mkdir()
    (root / "frontend").mkdir()
    write(root / "random-bucket/file.txt", "unclassified")
    write(
        root / "scripts/everything.py",
        "\n".join([f"def function_{index}(): return {index}" for index in range(220)]),
    )

    report = audit_structure(root)
    rule_ids = {finding["rule_id"] for finding in report["findings"]}

    assert report["status"] == "BLOCK"
    assert "SYNONYMOUS_DIRECTORY" in rule_ids
    assert "UNDECLARED_TOP_LEVEL" in rule_ids
    assert "REUSABLE_LOGIC_IN_SCRIPT" in rule_ids


def test_audit_blocks_invalid_structure_manifest(tmp_path: Path) -> None:
    root = tmp_path / "broken"
    root.mkdir()
    write(root / ".project-structure.yaml", "{ definitely-not-json")
    report = audit_structure(root)
    assert report["status"] == "BLOCK"
    assert "INVALID_STRUCTURE_MANIFEST" in {
        finding["rule_id"] for finding in report["findings"]
    }


def test_audit_blocks_structure_manifest_with_invalid_schema(tmp_path: Path) -> None:
    root = tmp_path / "broken-schema"
    root.mkdir()
    write(root / ".project-structure.yaml", '{"foo":"bar"}')

    report = audit_structure(root)

    assert report["status"] == "BLOCK"
    assert "INVALID_STRUCTURE_MANIFEST_SCHEMA" in {
        finding["rule_id"] for finding in report["findings"]
    }


def test_manifest_schema_rejects_placeholders_duplicates_and_unknown_options(
    tmp_path: Path,
) -> None:
    root = tmp_path / "library"
    scaffold_project(root, "python-library", "Library", package_name="library")
    manifest_path = root / ".project-structure.yaml"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["classification"]["purpose"] = ""
    manifest["directories"][0]["purpose"] = "Own {package_name} source."
    manifest["directories"].append(dict(manifest["directories"][0]))
    manifest["options"]["unknown_option"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = audit_structure(root)
    route = suggest_path(
        root,
        artifact="python-module",
        name="api.py",
        owner="core",
    )
    message = next(
        finding["message"]
        for finding in report["findings"]
        if finding["rule_id"] == "INVALID_STRUCTURE_MANIFEST_SCHEMA"
    )

    assert report["status"] == "BLOCK"
    assert route["status"] == "BLOCK"
    assert route["rule_id"] == "INVALID_STRUCTURE_MANIFEST_SCHEMA"
    assert "unresolved placeholder" in message
    assert "classification.purpose" in message
    assert "duplicated" in message
    assert "unsupported key" in message


def test_audit_detects_data_output_and_documentation_mixed_with_source(
    tmp_path: Path,
) -> None:
    root = tmp_path / "library"
    scaffold_project(root, "python-library", "Library", package_name="library")
    write(root / "src/library/result.csv", "metric,value")
    write(root / "src/library/guide.md", "# misplaced documentation")
    write(root / "docs/reference/generator.py", "print('misplaced source')")

    report = audit_structure(root)
    rule_ids = {finding["rule_id"] for finding in report["findings"]}

    assert report["status"] == "BLOCK"
    assert "DATA_OR_OUTPUT_IN_SOURCE" in rule_ids
    assert "DOCUMENTATION_IN_SOURCE" in rule_ids
    assert "SOURCE_IN_DOCUMENTATION" in rule_ids


def test_audit_propagates_ambiguous_detection_as_caution(tmp_path: Path) -> None:
    root = tmp_path / "empty"
    root.mkdir()

    report = audit_structure(root)

    assert report["status"] == "CAUTION"
    assert report["needs_confirmation"] is True
    assert "DETECTION_NEEDS_CONFIRMATION" in {
        finding["rule_id"] for finding in report["findings"]
    }


def test_audit_prunes_dependency_and_vcs_directories(tmp_path: Path) -> None:
    root = tmp_path / "library"
    scaffold_project(root, "python-library", "Library", package_name="library")
    write(root / "node_modules/vendor/src/index.js", "export const bundled = true")
    write(root / ".git/objects/fake.py", "print('not project source')")

    report = audit_structure(root)

    assert report["status"] == "PASS"
    assert not any(
        finding["path"].startswith(("node_modules", ".git"))
        for finding in report["findings"]
    )


def test_audit_existing_repo_without_manifest_checks_blueprint_roots(tmp_path: Path) -> None:
    root = tmp_path / "monorepo"
    write(root / "package.json", '{"workspaces":["apps/*","packages/*"]}')
    write(root / "turbo.json", "{}")
    write(root / "apps/web/src/index.ts", "export {}")
    write(root / "packages/ui/src/index.ts", "export {}")
    write(root / "random-bucket/file.txt", "unclassified")

    report = audit_structure(root)
    rule_ids = {finding["rule_id"] for finding in report["findings"]}

    assert report["status"] == "CAUTION"
    assert "UNDECLARED_TOP_LEVEL" in rule_ids
    assert "MISSING_BLUEPRINT_ROOT" in rule_ids


@pytest.mark.parametrize(
    ("status", "expected"),
    [("PASS", 0), ("CAUTION", 1), ("BLOCK", 2), ("ERROR", 3)],
)
def test_status_exit_code_contract(status: str, expected: int) -> None:
    assert status_exit_code(status) == expected
