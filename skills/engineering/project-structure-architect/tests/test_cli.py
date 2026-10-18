from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
CLI_NAMES = (
    "detect_project.py",
    "render_tree.py",
    "scaffold_project.py",
    "suggest_path.py",
    "audit_structure.py",
)


def run_cli(name: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )


def test_every_documented_cli_has_working_help() -> None:
    for name in CLI_NAMES:
        result = run_cli(name, "--help")
        assert result.returncode == 0, (name, result.stderr)
        assert "usage:" in result.stdout.lower()


def test_cli_new_project_to_runtime_audit_end_to_end(tmp_path: Path) -> None:
    root = tmp_path / "portal"
    scaffold = run_cli(
        "scaffold_project.py",
        str(root),
        "--blueprint",
        "web-fullstack-separated",
        "--project-name",
        "Portal",
        "--technology",
        "React",
        "--technology",
        "FastAPI",
    )
    assert scaffold.returncode == 0, scaffold.stderr

    detection = run_cli("detect_project.py", str(root))
    assert detection.returncode == 0, detection.stderr
    detection_payload = json.loads(detection.stdout)
    assert detection_payload["selected_blueprint"] == "web-fullstack-separated"
    assert {"React", "FastAPI"}.issubset(detection_payload["technology_stack"])

    suggestion = run_cli(
        "suggest_path.py",
        str(root),
        "--artifact",
        "frontend-feature",
        "--name",
        "LoginForm.tsx",
        "--owner",
        "authentication",
    )
    assert suggestion.returncode == 0, suggestion.stderr
    relative_path = json.loads(suggestion.stdout)["path"]
    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("export default function LoginForm() {}", encoding="utf-8")

    audit = run_cli("audit_structure.py", str(root))
    assert audit.returncode == 0, audit.stdout + audit.stderr
    assert json.loads(audit.stdout)["status"] == "PASS"


def test_cli_drift_returns_block_exit_code(tmp_path: Path) -> None:
    root = tmp_path / "library"
    scaffold = run_cli(
        "scaffold_project.py",
        str(root),
        "--blueprint",
        "python-library",
        "--project-name",
        "Library",
        "--package-name",
        "library",
    )
    assert scaffold.returncode == 0
    (root / "misc").mkdir()
    (root / "misc/file.txt").write_text("x", encoding="utf-8")

    audit = run_cli("audit_structure.py", str(root))
    assert audit.returncode == 2
    payload = json.loads(audit.stdout)
    assert payload["status"] == "BLOCK"
    assert "AMBIGUOUS_DIRECTORY" in {item["rule_id"] for item in payload["findings"]}


def test_cli_missing_root_returns_error_contract(tmp_path: Path) -> None:
    result = run_cli("detect_project.py", str(tmp_path / "missing"))
    assert result.returncode == 3
    payload = json.loads(result.stdout)
    assert payload["status"] == "ERROR"
    assert payload["error_code"] == "ROOT_NOT_FOUND"


def test_cli_forces_utf8_when_parent_requests_ascii(tmp_path: Path) -> None:
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "ascii"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "scaffold_project.py"),
            str(tmp_path / "unicode"),
            "--blueprint",
            "python-library",
            "--project-name",
            "中文项目",
            "--dry-run",
        ],
        capture_output=True,
        check=False,
        env=environment,
    )

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    payload = json.loads(result.stdout.decode("utf-8"))
    assert payload["project_name"] == "中文项目"


def test_cli_invalid_manifest_stops_runtime_write_with_block_exit(tmp_path: Path) -> None:
    root = tmp_path / "research"
    created = run_cli(
        "scaffold_project.py",
        str(root),
        "--blueprint",
        "research-step-based",
        "--project-name",
        "Study",
        "--package-name",
        "study",
    )
    assert created.returncode == 0
    (root / ".project-structure.yaml").write_text("{broken", encoding="utf-8")

    result = run_cli("scaffold_project.py", str(root), "--add-step", "training")

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "BLOCK"
    assert payload["error_code"] == "INVALID_STRUCTURE_MANIFEST"
    assert not any(path.name.endswith("training") for path in (root / "steps").iterdir())
