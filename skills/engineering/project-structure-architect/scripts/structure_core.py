"""Deterministic project-structure detection, scaffolding, routing, and audit.

The module deliberately uses only the Python standard library.  All mutating
operations are additive by default: existing files are preserved and no audit
operation moves or rewrites project content.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


SKILL_ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT_ROOT = SKILL_ROOT / "references" / "blueprints"
ASSET_ROOT = SKILL_ROOT / "assets"

BLUEPRINT_IDS = (
    "web-fullstack-separated",
    "web-typescript-monorepo",
    "react-frontend",
    "python-backend",
    "research-step-based",
    "data-science",
    "machine-learning-pipeline",
    "python-library",
    "microservices",
)

STATUS_EXIT_CODES = {"PASS": 0, "CAUTION": 1, "BLOCK": 2, "ERROR": 3}
SOURCE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".swift",
    ".ts",
    ".tsx",
    ".vue",
}
DATA_OR_OUTPUT_SUFFIXES = {
    ".arrow",
    ".avro",
    ".csv",
    ".feather",
    ".gif",
    ".h5",
    ".jpeg",
    ".jpg",
    ".jsonl",
    ".npy",
    ".npz",
    ".parquet",
    ".pdf",
    ".pkl",
    ".png",
    ".svg",
    ".tiff",
    ".webp",
    ".xlsx",
}
AMBIGUOUS_DIRECTORY_NAMES = {
    "backup",
    "common",
    "misc",
    "new",
    "others",
    "temp",
    "tmp",
    "utils",
}
TREE_EXCLUDES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "outputs",
    "target",
    "venv",
}
AUDIT_TRAVERSAL_EXCLUDES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pycache__",
    "coverage",
    "node_modules",
    "target",
    "venv",
}
AUDIT_DECLARATION_EXCLUDES = AUDIT_TRAVERSAL_EXCLUDES | {
    "build",
    "checkpoints",
    "dist",
    "outputs",
}
WINDOWS_RESERVED_NAMES = {
    "con",
    "prn",
    "aux",
    "nul",
    "com1",
    "com2",
    "com3",
    "com4",
    "com5",
    "com6",
    "com7",
    "com8",
    "com9",
    "lpt1",
    "lpt2",
    "lpt3",
    "lpt4",
    "lpt5",
    "lpt6",
    "lpt7",
    "lpt8",
    "lpt9",
}


class StructureError(Exception):
    """Expected, user-actionable structure operation failure."""

    def __init__(self, message: str, code: str = "STRUCTURE_ERROR") -> None:
        super().__init__(message)
        self.code = code


def status_exit_code(status: str) -> int:
    """Map the public status vocabulary to its stable process exit code."""

    return STATUS_EXIT_CODES.get(str(status).upper(), STATUS_EXIT_CODES["ERROR"])


def configure_utf8_stdio() -> None:
    """Emit stable UTF-8 JSON/tree output on Windows and redirected consoles."""

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def _validate_blueprint(payload: Any, expected_id: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise StructureError(f"Blueprint {expected_id!r} must be a JSON object.", "INVALID_BLUEPRINT")
    if payload.get("id") != expected_id:
        raise StructureError(
            f"Blueprint id mismatch: expected {expected_id!r}.", "INVALID_BLUEPRINT"
        )
    classification = payload.get("classification")
    if not isinstance(classification, dict) or not str(classification.get("purpose", "")).strip():
        raise StructureError(
            f"Blueprint {expected_id!r} has no classification purpose.", "INVALID_BLUEPRINT"
        )
    directories = payload.get("directories")
    if not isinstance(directories, list) or not directories:
        raise StructureError(f"Blueprint {expected_id!r} has no directories.", "INVALID_BLUEPRINT")
    for item in directories:
        if not isinstance(item, dict) or not str(item.get("path", "")).strip() or not str(
            item.get("purpose", "")
        ).strip():
            raise StructureError(
                f"Blueprint {expected_id!r} contains an invalid directory entry.",
                "INVALID_BLUEPRINT",
            )
        item.setdefault("required", True)
    return payload


def _load_markdown_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"```json\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        raise StructureError(
            f"Blueprint Markdown has no fenced JSON block: {path}", "INVALID_BLUEPRINT"
        )
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise StructureError(
            f"Blueprint JSON is invalid in {path.name}: {exc}", "INVALID_BLUEPRINT"
        ) from exc


def load_blueprint(blueprint_id: str) -> dict[str, Any]:
    """Load one supported blueprint from its required Markdown/JSON resource."""

    if blueprint_id not in BLUEPRINT_IDS:
        raise StructureError(f"Unknown blueprint: {blueprint_id}", "UNKNOWN_BLUEPRINT")
    markdown_path = BLUEPRINT_ROOT / f"{blueprint_id}.md"
    json_path = BLUEPRINT_ROOT / f"{blueprint_id}.json"
    if markdown_path.is_file():
        payload = _load_markdown_json(markdown_path)
    elif json_path.is_file():
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise StructureError(
                f"Blueprint JSON is invalid in {json_path.name}: {exc}", "INVALID_BLUEPRINT"
            ) from exc
    else:
        raise StructureError(
            f"Blueprint resource not found for {blueprint_id!r}.",
            "BLUEPRINT_NOT_FOUND",
        )
    return _validate_blueprint(payload, blueprint_id)


def _root_path(root: str | Path, *, must_exist: bool = True) -> Path:
    path = Path(root).expanduser()
    if must_exist and not path.exists():
        raise StructureError(f"Project root does not exist: {path}", "ROOT_NOT_FOUND")
    if must_exist and not path.is_dir():
        raise StructureError(f"Project root is not a directory: {path}", "ROOT_NOT_DIRECTORY")
    return path.resolve()


def _read_small_text(path: Path, limit: int = 1_000_000) -> str:
    try:
        if not path.is_file() or path.stat().st_size > limit:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _read_json_object(path: Path) -> dict[str, Any]:
    text = _read_small_text(path)
    if not text:
        return {}
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _structure_manifest_schema_errors(manifest: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []

    def string_values(value: Any) -> Iterable[str]:
        if isinstance(value, str):
            yield value
        elif isinstance(value, Mapping):
            for child in value.values():
                yield from string_values(child)
        elif isinstance(value, list):
            for child in value:
                yield from string_values(child)

    if any(
        re.search(r"\{[A-Za-z_][A-Za-z0-9_]*\}", value)
        for value in string_values(manifest)
    ):
        errors.append("manifest contains an unresolved placeholder")
    if manifest.get("schema_version") != "1.0":
        errors.append("schema_version must equal '1.0'")
    for key in ("project_name", "package_name"):
        if not isinstance(manifest.get(key), str) or not str(manifest.get(key)).strip():
            errors.append(f"{key} must be a non-empty string")
    blueprint_id = manifest.get("blueprint")
    if blueprint_id not in BLUEPRINT_IDS:
        errors.append("blueprint must name a supported blueprint")
    classification = manifest.get("classification")
    if not isinstance(classification, dict):
        errors.append("classification must be an object")
    elif not isinstance(classification.get("purpose"), str) or not classification[
        "purpose"
    ].strip():
        errors.append("classification.purpose must be a non-empty string")
    directories = manifest.get("directories")
    if not isinstance(directories, list) or not directories:
        errors.append("directories must be a non-empty array")
    else:
        seen_paths: set[str] = set()
        for index, item in enumerate(directories):
            if not isinstance(item, dict):
                errors.append(f"directories[{index}] must be an object")
                continue
            try:
                normalized_path = _validate_relative_path(
                    str(item.get("path", "")),
                    "manifest path",
                )
                path_key = normalized_path.casefold()
                if path_key in seen_paths:
                    errors.append(f"directories[{index}].path is duplicated")
                seen_paths.add(path_key)
            except StructureError:
                errors.append(f"directories[{index}].path is unsafe or empty")
            if not isinstance(item.get("purpose"), str) or not item["purpose"].strip():
                errors.append(f"directories[{index}].purpose must be non-empty")
            if not isinstance(item.get("required"), bool):
                errors.append(f"directories[{index}].required must be boolean")
    options = manifest.get("options")
    if not isinstance(options, dict) or any(
        not isinstance(value, bool) for value in options.values()
    ):
        errors.append("options must be an object of booleans")
    elif blueprint_id in BLUEPRINT_IDS:
        allowed_options = {
            str(item["conditional"])
            for item in load_blueprint(str(blueprint_id))["directories"]
            if item.get("conditional")
        }
        unknown_options = sorted(set(options) - allowed_options)
        if unknown_options:
            errors.append(
                "options contain unsupported key(s): " + ", ".join(unknown_options)
            )
    for key in ("adaptations", "exceptions"):
        if not isinstance(manifest.get(key), list) or any(
            not isinstance(item, str) for item in manifest.get(key, [])
        ):
            errors.append(f"{key} must be an array")
    return errors


def _load_structure_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    text = _read_small_text(path)
    try:
        manifest = json.loads(text)
    except json.JSONDecodeError as exc:
        raise StructureError(
            "The structure manifest is not valid JSON.",
            "INVALID_STRUCTURE_MANIFEST",
        ) from exc
    if not isinstance(manifest, dict):
        raise StructureError(
            "The structure manifest must be a JSON object.",
            "INVALID_STRUCTURE_MANIFEST",
        )
    errors = _structure_manifest_schema_errors(manifest)
    if errors:
        raise StructureError(
            "Invalid structure manifest schema: " + "; ".join(errors),
            "INVALID_STRUCTURE_MANIFEST_SCHEMA",
        )
    return manifest


def _has_any(root: Path, relative_paths: Iterable[str]) -> bool:
    return any((root / item).exists() for item in relative_paths)


def _first_src_package(root: Path) -> str | None:
    src = root / "src"
    if not src.is_dir():
        return None
    try:
        candidates = sorted(
            item.name
            for item in src.iterdir()
            if item.is_dir() and not item.name.startswith(".") and item.name != "__pycache__"
        )
    except OSError:
        return None
    return candidates[0] if candidates else None


def detect_project(root: str | Path) -> dict[str, Any]:
    """Classify a repository conservatively and expose all decision evidence."""

    project_root = _root_path(root)
    scores = {blueprint_id: 0 for blueprint_id in BLUEPRINT_IDS}
    evidence: dict[str, list[str]] = {blueprint_id: [] for blueprint_id in BLUEPRINT_IDS}

    def add(blueprint_id: str, points: int, reason: str) -> None:
        scores[blueprint_id] += points
        evidence[blueprint_id].append(reason)

    manifest = _read_json_object(project_root / ".project-structure.yaml")
    manifest_blueprint = manifest.get("blueprint")
    manifest_bonus = 12
    if manifest_blueprint in BLUEPRINT_IDS:
        add(
            str(manifest_blueprint),
            manifest_bonus,
            ".project-structure.yaml manifest declares this blueprint",
        )

    root_package = _read_json_object(project_root / "package.json")
    root_package_text = _read_small_text(project_root / "package.json").lower()
    root_python_text = "\n".join(
        text
        for text in (
            _read_small_text(project_root / name).lower()
            for name in ("pyproject.toml", "requirements.txt", "setup.cfg")
        )
        if text
    )
    frontend_package_text = _read_small_text(project_root / "frontend/package.json").lower()
    backend_python_text = "\n".join(
        text
        for text in (
            _read_small_text(project_root / f"backend/{name}").lower()
            for name in ("pyproject.toml", "requirements.txt")
        )
        if text
    )
    backend_jvm_text = "\n".join(
        text
        for text in (
            _read_small_text(project_root / f"backend/{name}").lower()
            for name in ("pom.xml", "build.gradle", "build.gradle.kts")
        )
        if text
    )

    frontend_dir = (project_root / "frontend").is_dir() or (project_root / "front").is_dir()
    backend_dir = (project_root / "backend").is_dir()
    if frontend_dir:
        add("web-fullstack-separated", 6, "frontend/ or front/ directory exists")
    if backend_dir:
        add("web-fullstack-separated", 6, "backend/ directory exists")
    if frontend_package_text and any(key in frontend_package_text for key in ("react", "vue", "svelte")):
        add("web-fullstack-separated", 3, "frontend package manifest declares a UI framework")
    if backend_python_text and any(key in backend_python_text for key in ("fastapi", "django", "flask")):
        add("web-fullstack-separated", 3, "backend Python manifest declares a web framework")
    if backend_jvm_text and any(
        key in backend_jvm_text
        for key in ("spring-boot", "org.springframework", "springframework")
    ):
        add("web-fullstack-separated", 3, "backend JVM manifest declares Spring")
    root_has_frontend = bool(root_package_text) and any(
        key in root_package_text for key in ("react", "vue", "svelte", "vite")
    )
    root_has_non_react_frontend = bool(root_package_text) and any(
        key in root_package_text for key in ("vue", "svelte")
    ) and "react" not in root_package_text
    root_has_backend = bool(root_python_text) and any(
        key in root_python_text for key in ("fastapi", "django", "flask")
    )
    if root_has_frontend and root_has_backend:
        add("web-fullstack-separated", 5, "root manifests contain both frontend and backend stacks")

    workspaces = root_package.get("workspaces")
    if workspaces:
        add("web-typescript-monorepo", 8, "package.json declares workspaces")
    if (project_root / "turbo.json").is_file():
        add("web-typescript-monorepo", 5, "turbo.json exists")
    if (project_root / "apps").is_dir():
        add("web-typescript-monorepo", 3, "apps/ directory exists")
    if (project_root / "packages").is_dir():
        add("web-typescript-monorepo", 3, "packages/ directory exists")

    if root_has_frontend:
        add("react-frontend", 6, "root package manifest declares a frontend framework")
    if "vite" in root_package_text or any(project_root.glob("vite.config.*")):
        add("react-frontend", 2, "Vite marker exists")
    if (project_root / "src/features").is_dir():
        add("react-frontend", 2, "src/features/ directory exists")

    if root_has_backend:
        add("python-backend", 8, "root Python manifest declares a web framework")
    if (project_root / "app/api").is_dir() or (project_root / "app/services").is_dir():
        add("python-backend", 3, "layered app/ backend directories exist")

    research_markers = ("data", "steps", "src", "experiments", "outputs", "paper")
    research_count = sum((project_root / name).is_dir() for name in research_markers)
    if research_count:
        add("research-step-based", research_count, f"{research_count}/6 research lifecycle roots exist")
    if (project_root / "steps").is_dir():
        add("research-step-based", 4, "numbered steps/ workflow exists")
    if (project_root / "paper").is_dir():
        add("research-step-based", 2, "paper/ publication boundary exists")

    lifecycle_markers = ("data/raw", "data/interim", "data/processed")
    lifecycle_count = sum((project_root / name).is_dir() for name in lifecycle_markers)
    if lifecycle_count:
        add("data-science", lifecycle_count * 2, f"{lifecycle_count}/3 data lifecycle layers exist")
    for name, reason in (
        ("notebooks", "notebooks/ exists"),
        ("models", "models/ exists"),
        ("reports", "reports/ exists"),
    ):
        if (project_root / name).is_dir():
            add("data-science", 2, reason)

    pipeline_training = any(project_root.glob("src/*/pipelines/training"))
    if pipeline_training:
        add("machine-learning-pipeline", 8, "src package contains pipelines/training")
    if (project_root / "experiments").is_dir():
        add("machine-learning-pipeline", 2, "experiments/ exists")
    if (project_root / "checkpoints").is_dir():
        add("machine-learning-pipeline", 4, "checkpoints/ exists")
    if (project_root / "Snakefile").is_file():
        add("machine-learning-pipeline", 4, "Snakefile is a scientific-pipeline candidate")
        add("research-step-based", 3, "Snakefile is a scientific-workflow candidate")

    if (project_root / "pyproject.toml").is_file():
        add("python-library", 2, "pyproject.toml exists")
    if _first_src_package(project_root):
        add("python-library", 5, "src-layout Python package exists")
    if (project_root / "tests").is_dir():
        add("python-library", 2, "tests/ exists")

    dockerfiles = sorted(project_root.glob("services/*/Dockerfile"))
    if len(dockerfiles) >= 2:
        add("microservices", 10, "multiple service Dockerfiles exist")
    if (project_root / "services").is_dir():
        add("microservices", 3, "services/ boundary exists")
    if _has_any(project_root, ("infra", "infrastructure")):
        add("microservices", 2, "infrastructure boundary exists")

    technology_stack: list[str] = []
    manifest_classification = manifest.get("classification")
    if isinstance(manifest_classification, dict):
        manifest_stacks = manifest_classification.get("stacks")
        if isinstance(manifest_stacks, list):
            technology_stack.extend(
                str(item).strip()
                for item in manifest_stacks
                if isinstance(item, str) and item.strip()
            )
    if workspaces or (project_root / "turbo.json").is_file() or (project_root / "tsconfig.json").is_file():
        technology_stack.append("TypeScript")
    elif root_package_text:
        technology_stack.append("JavaScript")
    if "react" in root_package_text or "react" in frontend_package_text:
        technology_stack.append("React")
    if "vue" in root_package_text or "vue" in frontend_package_text:
        technology_stack.append("Vue")
    if "svelte" in root_package_text or "svelte" in frontend_package_text:
        technology_stack.append("Svelte")
    if "next" in root_package_text or "next" in frontend_package_text:
        technology_stack.append("Next.js")
    if "vite" in root_package_text or "vite" in frontend_package_text:
        technology_stack.append("Vite")
    if root_python_text or backend_python_text or any(project_root.glob("src/**/*.py")):
        technology_stack.append("Python")
    for framework, label in (("fastapi", "FastAPI"), ("django", "Django"), ("flask", "Flask")):
        if framework in root_python_text or framework in backend_python_text:
            technology_stack.append(label)
    if backend_jvm_text or (project_root / "backend/src/main/java").is_dir():
        technology_stack.append("Java")
    if any(
        key in backend_jvm_text
        for key in ("spring-boot", "org.springframework", "springframework")
    ):
        technology_stack.append("Spring")
    if dockerfiles:
        technology_stack.append("Docker")
    if (project_root / "Snakefile").is_file():
        technology_stack.append("Snakemake")
    technology_stack = list(dict.fromkeys(technology_stack))

    existing_conventions: list[str] = []
    if (project_root / "apps").is_dir() and (project_root / "packages").is_dir():
        existing_conventions.append("apps/packages")
    if frontend_dir and backend_dir:
        existing_conventions.append("frontend/backend")
    if _first_src_package(project_root):
        existing_conventions.append("src-layout")
    if (project_root / "steps").is_dir():
        existing_conventions.append("numbered-steps")
    if lifecycle_count == len(lifecycle_markers):
        existing_conventions.append("data-lifecycle")
    if (project_root / "services").is_dir():
        existing_conventions.append("services")

    manifest_conflict = False
    if manifest_blueprint in BLUEPRINT_IDS:
        structural_scores = dict(scores)
        structural_scores[str(manifest_blueprint)] -= manifest_bonus
        structural_ranked = sorted(
            structural_scores.items(),
            key=lambda item: (-item[1], BLUEPRINT_IDS.index(item[0])),
        )
        structural_top, structural_score = structural_ranked[0]
        if structural_score >= 8 and structural_top != manifest_blueprint:
            manifest_conflict = True
            scores[str(manifest_blueprint)] -= manifest_bonus

    ranked = sorted(scores.items(), key=lambda item: (-item[1], BLUEPRINT_IDS.index(item[0])))
    top_id, top_score = ranked[0]
    positive = [(item_id, score) for item_id, score in ranked if score > 0]
    if not positive:
        return {
            "status": "CAUTION",
            "root": str(project_root),
            "selected_blueprint": None,
            "classification": {"purpose": "unknown"},
            "evidence": ["No recognized project markers were found."],
            "alternatives": [],
            "ambiguities": ["The directory is empty or lacks enough structural markers."],
            "needs_confirmation": True,
            "scores": scores,
            "technology_stack": technology_stack,
            "existing_conventions": existing_conventions,
        }

    second_score = positive[1][1] if len(positive) > 1 else 0
    ambiguities: list[str] = []
    needs_confirmation = False
    if top_score < 4:
        needs_confirmation = True
        ambiguities.append("The available markers are too weak for automatic selection.")
    if second_score and top_score - second_score <= 1:
        needs_confirmation = True
        ambiguities.append("Two or more blueprints have nearly equal evidence.")
    if root_has_frontend and root_has_backend and not (frontend_dir and backend_dir):
        needs_confirmation = True
        ambiguities.append(
            "Frontend and backend dependencies share the root; confirm a single tree or separated deployables."
        )
    if manifest_conflict:
        needs_confirmation = True
        ambiguities.append(
            "The recorded manifest blueprint conflicts with strong existing repository conventions."
        )
    if top_id == "react-frontend" and root_has_non_react_frontend:
        needs_confirmation = True
        ambiguities.append(
            "The closest frontend blueprint is React-specific; adapt it explicitly for the detected framework."
        )

    alternatives = [
        {"blueprint": item_id, "score": score, "evidence": evidence[item_id]}
        for item_id, score in positive[1:4]
    ]
    blueprint = load_blueprint(top_id)
    classification = dict(blueprint["classification"])
    if top_id == "react-frontend" and root_has_non_react_frontend:
        classification["stacks"] = [
            stack for stack in technology_stack if stack in {"Vue", "Svelte"}
        ]
        classification["purpose"] = "single frontend application requiring blueprint adaptation"
    return {
        "status": "CAUTION" if needs_confirmation else "PASS",
        "root": str(project_root),
        "selected_blueprint": top_id,
        "classification": classification,
        "evidence": evidence[top_id],
        "alternatives": alternatives,
        "ambiguities": ambiguities,
        "needs_confirmation": needs_confirmation,
        "scores": scores,
        "technology_stack": technology_stack,
        "existing_conventions": existing_conventions,
    }


def render_tree(
    root: str | Path,
    max_depth: int = 4,
    exclude: Iterable[str] | None = None,
) -> str:
    """Render a stable, sorted tree without traversing generated directories."""

    project_root = _root_path(root)
    if max_depth < 0:
        raise StructureError("max_depth must be zero or greater.", "INVALID_MAX_DEPTH")
    excluded = set(TREE_EXCLUDES)
    if exclude:
        excluded.update(str(item) for item in exclude)
    lines = [project_root.name + "/"]

    def walk(directory: Path, prefix: str, depth: int) -> None:
        if depth >= max_depth:
            return
        try:
            children = [
                item
                for item in directory.iterdir()
                if item.name not in excluded and not item.is_symlink()
            ]
        except (OSError, PermissionError):
            lines.append(prefix + "└── [unreadable]")
            return
        children.sort(key=lambda item: (not item.is_dir(), item.name.casefold(), item.name))
        for index, child in enumerate(children):
            last = index == len(children) - 1
            connector = "└── " if last else "├── "
            suffix = "/" if child.is_dir() else ""
            lines.append(prefix + connector + child.name + suffix)
            if child.is_dir():
                walk(child, prefix + ("    " if last else "│   "), depth + 1)

    walk(project_root, "", 0)
    return "\n".join(lines)


def _validate_relative_path(value: str, label: str = "path") -> str:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise StructureError(f"Invalid {label}.", "UNSAFE_PATH")
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise StructureError(f"Unsafe {label}: {value}", "UNSAFE_PATH")
    if re.match(r"^[A-Za-z]:", normalized):
        raise StructureError(f"Unsafe {label}: {value}", "UNSAFE_PATH")
    for part in path.parts:
        if (
            part.endswith((" ", "."))
            or any(character in '<>:"|?*' for character in part)
            or any(ord(character) < 32 for character in part)
        ):
            raise StructureError(f"Unsafe {label}: {value}", "UNSAFE_PATH")
        stem = part.rstrip(" .").split(".", 1)[0].casefold()
        if stem in WINDOWS_RESERVED_NAMES:
            raise StructureError(f"Reserved name in {label}: {value}", "UNSAFE_PATH")
    return path.as_posix()


def _validate_file_name(name: str) -> str:
    try:
        normalized = _validate_relative_path(name, "file name")
    except StructureError as exc:
        raise StructureError(f"Invalid file name: {name}", "UNSAFE_FILE_NAME") from exc
    if "/" in normalized:
        raise StructureError(f"Invalid file name: {name}", "UNSAFE_FILE_NAME")
    return normalized


def _validate_display_name(value: str, *, label: str, code: str) -> str:
    display_name = str(value or "").strip()
    if (
        not display_name
        or len(display_name) > 200
        or any(ord(character) < 32 for character in display_name)
        or "{{" in display_name
        or "}}" in display_name
    ):
        raise StructureError(f"Invalid {label}: {value!r}", code)
    return display_name


def _slug(value: str, *, label: str, default: str | None = None) -> str:
    raw = str(value or "").strip()
    if not raw and default is not None:
        raw = default
    if not raw or "/" in raw or "\\" in raw or ".." in raw:
        raise StructureError(f"Invalid {label}: {value!r}", "INVALID_NAME")
    result: list[str] = []
    underscore = False
    for character in raw.casefold():
        if character.isalnum():
            result.append(character)
            underscore = False
        elif not underscore:
            result.append("_")
            underscore = True
    slug = "".join(result).strip("_")
    if not slug or slug[0].isdigit() and label == "package name":
        if label == "package name" and slug:
            slug = "project_" + slug
        else:
            raise StructureError(f"Invalid {label}: {value!r}", "INVALID_NAME")
    return slug


def _safe_join(root: Path, relative: str) -> Path:
    normalized = _validate_relative_path(relative)
    destination = (root / PurePosixPath(normalized)).resolve(strict=False)
    if destination != root and root not in destination.parents:
        raise StructureError(f"Path escapes project root: {relative}", "UNSAFE_PATH")
    return destination


def _render_blueprint_path(raw_path: str, package_name: str, project_slug: str) -> str:
    rendered = raw_path.replace("{package_name}", package_name).replace(
        "{project_name_slug}", project_slug
    )
    if "{" in rendered or "}" in rendered:
        raise StructureError(
            f"Unsupported placeholder in blueprint path: {raw_path}", "INVALID_BLUEPRINT"
        )
    return _validate_relative_path(rendered, "blueprint path")


def _condition_enabled(condition: Any, options: Mapping[str, bool]) -> bool:
    if condition in (None, "", False):
        return True
    if condition is True:
        return True
    if isinstance(condition, str):
        return bool(options.get(condition, False))
    if isinstance(condition, list):
        return all(isinstance(item, str) and options.get(item, False) for item in condition)
    return False


def _planned_tree(
    directory_paths: Iterable[str],
    file_paths: Iterable[str],
    root_name: str,
) -> str:
    tree: dict[str, Any] = {}
    directory_set = set(directory_paths)
    all_paths = directory_set | set(file_paths)
    for raw_path in sorted(all_paths, key=lambda value: (value.count("/"), value.casefold())):
        node = tree
        for part in PurePosixPath(raw_path).parts:
            node = node.setdefault(part, {})
    lines = [root_name + "/"]

    def walk(node: dict[str, Any], prefix: str, parent_parts: tuple[str, ...]) -> None:
        entries = sorted(node.items(), key=lambda item: item[0].casefold())
        for index, (name, child) in enumerate(entries):
            last = index == len(entries) - 1
            current_parts = parent_parts + (name,)
            current_path = PurePosixPath(*current_parts).as_posix()
            lines.append(
                prefix
                + ("└── " if last else "├── ")
                + name
                + ("/" if current_path in directory_set else "")
            )
            if child:
                walk(
                    child,
                    prefix + ("    " if last else "│   "),
                    current_parts,
                )

    walk(tree, "", ())
    return "\n".join(lines)


def _template_text(names: Sequence[str]) -> str:
    for name in names:
        path = ASSET_ROOT / name
        if path.is_file():
            return path.read_text(encoding="utf-8")
    raise StructureError(
        "Required asset not found; expected one of: " + ", ".join(names),
        "ASSET_NOT_FOUND",
    )


def _render_template(template: str, values: Mapping[str, Any]) -> str:
    rendered = template
    for key, value in values.items():
        text_value = str(value)
        for token_key in {key, key.lower(), key.upper()}:
            rendered = rendered.replace("{{" + token_key + "}}", text_value)
    unresolved = sorted(set(re.findall(r"\{\{\s*[^{}]+?\s*\}\}", rendered)))
    if unresolved:
        raise StructureError(
            "Unresolved template token(s): " + ", ".join(unresolved),
            "TEMPLATE_TOKEN_UNRESOLVED",
        )
    return rendered


def _project_structure_document(
    *,
    project_name: str,
    package_name: str,
    blueprint: Mapping[str, Any],
    directories: Sequence[Mapping[str, Any]],
    tree: str,
    adaptations: Sequence[str],
) -> str:
    classification = blueprint["classification"]
    directory_table = "\n".join(
        ["| 目录 | 职责 | 必选 |", "|---|---|---|"]
        + [
            f"| `{item['path']}/` | {item['purpose']} | {'是' if item.get('required', True) else '条件启用'} |"
            for item in directories
        ]
    )
    values = {
        "project_name": project_name,
        "package_name": package_name,
        "classification": json.dumps(classification, ensure_ascii=False, sort_keys=True),
        "blueprint": blueprint["id"],
        "directory_tree": tree,
        "directory_responsibilities": directory_table,
        "file_placement_rules": (
            "Keep feature-local code with its owner; put reusable implementation in the narrowest "
            "explicit shared boundary; never use unscoped misc/common/utils/temp directories."
        ),
        "naming_conventions": (
            "Use descriptive lowercase directory names; use snake_case for Python packages and "
            "numbered `NN_name` directories only for ordered research steps."
        ),
        "dependency_directions": (
            "Entry points may depend on reusable implementation; reusable implementation must not "
            "depend on generated outputs or workflow entry-point directories."
        ),
        "extension_guides": (
            "Before adding a feature, API, service, experiment, or research step, run the path "
            "suggestion command and document any new architectural boundary."
        ),
        "generated_and_ignored": (
            "Generated artifacts belong in output/build/checkpoint/report artifact directories and "
            "must not contain source-of-truth implementation."
        ),
        "decisions_and_exceptions": (
            "; ".join(adaptations)
            if adaptations
            else "No blueprint exceptions were introduced during scaffolding."
        ),
        "directories_json": json.dumps(list(directories), ensure_ascii=False, indent=2),
    }
    template = _template_text(("PROJECT_STRUCTURE.md.template", "project-structure.md.template"))
    return _render_template(template, values).rstrip() + "\n"


def _agents_document(project_name: str, blueprint_id: str, scope: str, scope_rules: str) -> str:
    values = {
        "project_name": project_name,
        "blueprint": blueprint_id,
        "scope": scope,
        "scope_rules": scope_rules,
    }
    template = _template_text(("AGENTS.md.template", "agents.md.template"))
    return _render_template(template, values).rstrip() + "\n"


def _manifest_document(
    *,
    project_name: str,
    package_name: str,
    blueprint_id: str,
    classification: Mapping[str, Any],
    directories: Sequence[Mapping[str, Any]],
    options: Mapping[str, bool],
    adaptations: Sequence[str],
) -> tuple[str, dict[str, Any]]:
    template = _template_text(("project-structure.yaml.template",))
    values = {
        "project_name_json": json.dumps(project_name, ensure_ascii=False),
        "package_name_json": json.dumps(package_name, ensure_ascii=False),
        "blueprint_json": json.dumps(blueprint_id, ensure_ascii=False),
        "classification_json": json.dumps(classification, ensure_ascii=False, indent=2),
        "directories_json": json.dumps(list(directories), ensure_ascii=False, indent=2),
        "options_json": json.dumps(dict(options), ensure_ascii=False, indent=2),
        "adaptations_json": json.dumps(list(adaptations), ensure_ascii=False, indent=2),
    }
    rendered = _render_template(template, values)
    try:
        payload = json.loads(rendered)
    except json.JSONDecodeError as exc:
        raise StructureError(
            f"Rendered manifest asset is not valid JSON: {exc}",
            "INVALID_ASSET_TEMPLATE",
        ) from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != "1.0":
        raise StructureError(
            "Rendered manifest asset must be a schema_version 1.0 object.",
            "INVALID_ASSET_TEMPLATE",
        )
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n", payload


def scaffold_project(
    target: str | Path,
    blueprint_id: str,
    project_name: str,
    package_name: str | None = None,
    *,
    shared_contracts: bool = False,
    allow_existing: bool = False,
    dry_run: bool = False,
    with_infrastructure: bool = False,
    technology_stack: Sequence[str] | None = None,
    enabled_options: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Additively create a project from one blueprint without overwriting files."""

    project_display_name = _validate_display_name(
        project_name,
        label="project name",
        code="INVALID_PROJECT_NAME",
    )
    target_input = Path(target).expanduser()
    if target_input.exists() and not target_input.is_dir():
        raise StructureError(f"Target is not a directory: {target_input}", "TARGET_NOT_DIRECTORY")
    if target_input.is_symlink():
        raise StructureError("Scaffolding into a symbolic-link root is not allowed.", "UNSAFE_TARGET")
    root = target_input.resolve(strict=False)
    preexisting_paths: list[str] = []
    target_was_nonempty = False
    if target_input.exists():
        try:
            nonempty = next(target_input.iterdir(), None) is not None
            target_was_nonempty = nonempty
            preexisting_paths = [
                relative
                for _path, relative in _relative_files(
                    target_input,
                    excluded=TREE_EXCLUDES,
                )
            ]
        except OSError as exc:
            raise StructureError(f"Cannot inspect target: {exc}", "TARGET_UNREADABLE") from exc
        if nonempty and not allow_existing:
            raise StructureError(
                "Refusing to scaffold into a non-empty target without allow_existing.",
                "NONEMPTY_TARGET",
            )
        if nonempty and allow_existing:
            _load_structure_manifest(target_input / ".project-structure.yaml")
            existing_detection = detect_project(target_input)
            existing_blueprint = existing_detection.get("selected_blueprint")
            if existing_blueprint and existing_blueprint != blueprint_id:
                raise StructureError(
                    "Refusing to add a blueprint that conflicts with the coherent existing "
                    f"structure ({existing_blueprint!r} != {blueprint_id!r}).",
                    "BLUEPRINT_CONFLICT",
                )
            if existing_blueprint and existing_detection.get("needs_confirmation"):
                raise StructureError(
                    "Existing structure is ambiguous; resolve its blueprint before adding scaffold content.",
                    "AMBIGUOUS_EXISTING_STRUCTURE",
                )

    project_slug = _slug(project_display_name, label="project name")
    package = _slug(package_name or project_slug, label="package name")
    blueprint = load_blueprint(blueprint_id)
    normalized_technologies: list[str] = []
    for raw_technology in technology_stack or ():
        technology = str(raw_technology).strip()
        if (
            not technology
            or len(technology) > 100
            or any(ord(character) < 32 for character in technology)
            or "{{" in technology
            or "}}" in technology
        ):
            raise StructureError(
                f"Invalid technology label: {raw_technology!r}",
                "INVALID_TECHNOLOGY",
            )
        if technology.casefold() not in {
            existing.casefold() for existing in normalized_technologies
        }:
            normalized_technologies.append(technology)
    effective_blueprint = dict(blueprint)
    effective_classification = dict(blueprint["classification"])
    adaptations: list[str] = []
    if normalized_technologies:
        effective_classification["stacks"] = normalized_technologies
        adaptations.append(
            "Explicit technology stack: " + ", ".join(normalized_technologies)
        )
    effective_blueprint["classification"] = effective_classification
    available_options = {
        str(item["conditional"])
        for item in blueprint["directories"]
        if item.get("conditional")
    }
    requested_options = {
        str(item).strip() for item in enabled_options or () if str(item).strip()
    }
    if shared_contracts:
        requested_options.add("shared_contracts")
    if with_infrastructure:
        requested_options.add("with_infrastructure")
    unknown_options = sorted(requested_options - available_options)
    if unknown_options:
        raise StructureError(
            "Blueprint option(s) are not supported by this blueprint: "
            + ", ".join(unknown_options),
            "UNKNOWN_BLUEPRINT_OPTION",
        )
    options = {
        option: option in requested_options for option in sorted(available_options)
    }
    directories: list[dict[str, Any]] = []
    for raw_item in blueprint["directories"]:
        if not _condition_enabled(raw_item.get("conditional"), options):
            continue
        item = dict(raw_item)
        item["path"] = _render_blueprint_path(str(item["path"]), package, project_slug)
        if isinstance(item.get("purpose"), str):
            item["purpose"] = str(item["purpose"]).replace(
                "{package_name}", package
            ).replace("{project_name_slug}", project_slug)
        if isinstance(item.get("local_rules"), list):
            item["local_rules"] = [
                str(rule).replace("{package_name}", package).replace(
                    "{project_name_slug}", project_slug
                )
                for rule in item["local_rules"]
            ]
        elif isinstance(item.get("local_rules"), str):
            item["local_rules"] = str(item["local_rules"]).replace(
                "{package_name}", package
            ).replace("{project_name_slug}", project_slug)
        directories.append(item)

    directory_paths = [str(item["path"]) for item in directories]
    local_rule_entries = {
        str(item["path"]): item.get("local_rules")
        for item in directories
        if item.get("local_rules") and "/" not in str(item["path"])
    }
    local_rule_roots = sorted(local_rule_entries)
    tree = _planned_tree(
        directory_paths,
        ["PROJECT_STRUCTURE.md", ".project-structure.yaml", "AGENTS.md"]
        + [f"{scope}/AGENTS.md" for scope in local_rule_roots],
        root.name or project_slug,
    )
    manifest_text, _manifest = _manifest_document(
        project_name=project_display_name,
        package_name=package,
        blueprint_id=blueprint_id,
        classification=effective_classification,
        directories=directories,
        options=options,
        adaptations=adaptations,
    )
    files: dict[str, str] = {".project-structure.yaml": manifest_text}
    files["PROJECT_STRUCTURE.md"] = _project_structure_document(
        project_name=project_display_name,
        package_name=package,
        blueprint=effective_blueprint,
        directories=directories,
        tree=tree,
        adaptations=adaptations,
    )
    files["AGENTS.md"] = _agents_document(
        project_display_name,
        blueprint_id,
        ".",
        "Apply the documented project tree and route every new file by responsibility and owner.",
    )
    for scope in local_rule_roots:
        declared_rules = local_rule_entries[scope]
        if isinstance(declared_rules, list) and declared_rules:
            rules = "\n".join(f"- {rule}" for rule in declared_rules)
        elif isinstance(declared_rules, str) and declared_rules.strip():
            rules = declared_rules.strip()
        elif scope in {"frontend", "front"}:
            rules = "Keep feature-local code in src/features and shared integrations in src/services or src/lib."
        elif scope == "backend":
            rules = "Keep routes, business services, repositories, schemas, models, and database code separated."
        elif scope == "steps":
            rules = "Keep steps thin: orchestration, configuration, inputs, outputs, and calls into reusable src code."
        elif scope == "apps":
            rules = "Each child is an independently runnable application; application-specific code stays here."
        elif scope == "packages":
            rules = "Only explicit shared libraries belong here; application-specific code is prohibited."
        elif scope == "services":
            rules = "Each child is independently deployable and owns its local dependencies and tests."
        else:
            rules = "Preserve this boundary's documented responsibility."
        files[f"{scope}/AGENTS.md"] = _agents_document(
            project_display_name,
            blueprint_id,
            scope,
            rules,
        )

    # Preflight all paths before the first mutation so type conflicts cannot leave a partial tree.
    requested_directories = set(directory_paths)
    requested_directories.update(str(PurePosixPath(path).parent) for path in files if "/" in path)
    all_directories: set[str] = set()
    for relative in requested_directories:
        pure = PurePosixPath(relative)
        all_directories.add(pure.as_posix())
        all_directories.update(parent.as_posix() for parent in pure.parents)
    all_directories.discard(".")
    for relative in sorted(all_directories, key=lambda value: value.count("/")):
        destination = _safe_join(root, relative)
        if destination.exists() and not destination.is_dir():
            raise StructureError(
                f"A file blocks required directory {relative!r}.", "PATH_TYPE_CONFLICT"
            )
    for relative in files:
        destination = _safe_join(root, relative)
        if destination.exists() and destination.is_dir():
            raise StructureError(
                f"A directory blocks required file {relative!r}.", "PATH_TYPE_CONFLICT"
            )

    preserved_set = (
        set(preexisting_paths)
        | {relative for relative in files if _safe_join(root, relative).exists()}
    )
    created_directories = sorted(
        relative for relative in directory_paths if not _safe_join(root, relative).exists()
    )
    created_files = sorted(relative for relative in files if not _safe_join(root, relative).exists())
    if not dry_run:
        created_directory_paths: list[Path] = []
        created_file_paths: list[Path] = []
        actual_created_directories: list[str] = []
        actual_created_files: list[str] = []
        try:
            missing_root_chain: list[Path] = []
            cursor = root
            while not cursor.exists():
                missing_root_chain.append(cursor)
                if cursor.parent == cursor:
                    break
                cursor = cursor.parent
            for directory in reversed(missing_root_chain):
                try:
                    directory.mkdir()
                    created_directory_paths.append(directory)
                except FileExistsError:
                    if not directory.is_dir():
                        raise
            for relative in sorted(
                all_directories | set(directory_paths),
                key=lambda value: (value.count("/"), value),
            ):
                destination = _safe_join(root, relative)
                try:
                    destination.mkdir()
                    created_directory_paths.append(destination)
                    if relative in directory_paths:
                        actual_created_directories.append(relative)
                except FileExistsError:
                    if not destination.is_dir():
                        raise
            for relative, content in sorted(files.items()):
                destination = _safe_join(root, relative)
                try:
                    handle = destination.open(
                        "x",
                        encoding="utf-8",
                        newline="\n",
                    )
                except FileExistsError:
                    preserved_set.add(relative)
                    continue
                created_file_paths.append(destination)
                with handle:
                    handle.write(content)
                actual_created_files.append(relative)
        except Exception:
            for created_file in reversed(created_file_paths):
                try:
                    created_file.unlink(missing_ok=True)
                except OSError:
                    pass
            for created_directory in sorted(
                created_directory_paths,
                key=lambda item: len(item.parts),
                reverse=True,
            ):
                try:
                    created_directory.rmdir()
                except OSError:
                    pass
            raise
        created_directories = sorted(actual_created_directories)
        created_files = sorted(actual_created_files)

    preserved = sorted(preserved_set)
    status = "CAUTION" if preserved or target_was_nonempty else "PASS"
    return {
        "status": status,
        "target": str(root),
        "blueprint": blueprint_id,
        "project_name": project_display_name,
        "package_name": package,
        "technology_stack": normalized_technologies or effective_classification.get("stacks", []),
        "adaptations": adaptations,
        "options": options,
        "dry_run": dry_run,
        "created_directories": created_directories,
        "created_files": created_files,
        "preserved_paths": preserved,
        "actions": [
            {"action": "create_directory", "path": path} for path in created_directories
        ]
        + [{"action": "create_file", "path": path} for path in created_files],
    }


def _existing_step_numbers(steps_root: Path) -> list[int]:
    if not steps_root.is_dir():
        return []
    numbers: list[int] = []
    try:
        children = list(steps_root.iterdir())
    except OSError as exc:
        raise StructureError(f"Cannot inspect steps directory: {exc}", "STEPS_UNREADABLE") from exc
    for child in children:
        if not child.is_dir():
            continue
        match = re.match(r"^(\d+)_", child.name)
        if match:
            numbers.append(int(match.group(1)))
    return numbers


def add_research_step(
    root: str | Path,
    name: str,
    sequence: int | None = None,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Append one numbered, thin research step without renumbering old steps."""

    project_root = _root_path(root)
    manifest = _load_structure_manifest(project_root / ".project-structure.yaml")
    manifest_blueprint = manifest.get("blueprint")
    if manifest_blueprint and manifest_blueprint != "research-step-based":
        raise StructureError(
            "The recorded project blueprint does not allow a steps/ boundary.",
            "RESEARCH_STEP_NOT_ALLOWED",
        )
    if not (project_root / "steps").is_dir():
        detection = detect_project(project_root)
        if detection.get("selected_blueprint") != "research-step-based":
            raise StructureError(
                "No research-step convention exists in this project.",
                "RESEARCH_STEP_NOT_ALLOWED",
            )
    step_display_name = _validate_display_name(
        name,
        label="step name",
        code="INVALID_STEP_NAME",
    )
    step_slug = _slug(step_display_name, label="step name")
    existing_numbers = _existing_step_numbers(project_root / "steps")
    if sequence is None:
        number = max(existing_numbers, default=0) + 1
    else:
        if sequence < 1 or sequence > 999:
            raise StructureError("Step number must be between 1 and 999.", "INVALID_STEP_NUMBER")
        if sequence in existing_numbers:
            raise StructureError(
                f"Research step number already exists: {sequence}",
                "STEP_NUMBER_EXISTS",
            )
        number = sequence
    width = max(2, len(str(number)))
    relative_root = f"steps/{number:0{width}d}_{step_slug}"
    destination = _safe_join(project_root, relative_root)
    if destination.exists():
        raise StructureError(f"Research step already exists: {relative_root}", "STEP_EXISTS")
    files = {
        f"{relative_root}/README.md": (
            f"# Step {number:0{width}d}: {step_display_name}\n\n"
            "## Inputs\n\nDocument required inputs here.\n\n"
            "## Outputs\n\nDocument generated outputs here.\n\n"
            "## Dependencies\n\nReusable implementation must live under `src/`.\n\n"
            "## Run\n\n```powershell\npython run.py\n```\n"
        ),
        f"{relative_root}/config.yaml": "# Step-specific configuration only.\n{}\n",
        f"{relative_root}/run.py": (
            '"""Validate this thin step contract; reusable logic belongs under src/."""\n\n'
            "from __future__ import annotations\n\n"
            "import json\n"
            "from pathlib import Path\n\n\n"
            "def main() -> int:\n"
            "    step_root = Path(__file__).resolve().parent\n"
            "    required = (\"README.md\", \"config.yaml\")\n"
            "    missing = [name for name in required if not (step_root / name).is_file()]\n"
            "    status = \"PASS\" if not missing else \"ERROR\"\n"
            "    payload = {\n"
            "        \"status\": status,\n"
            "        \"step\": step_root.name,\n"
            "        \"contract_files\": list(required),\n"
            "        \"missing\": missing,\n"
            "        \"message\": \"Step contract is ready for orchestration.\" if not missing else \"Step contract is incomplete.\",\n"
            "    }\n"
            "    print(json.dumps(payload, ensure_ascii=False, indent=2))\n"
            "    return 0 if not missing else 3\n\n\n"
            "if __name__ == \"__main__\":\n"
            "    raise SystemExit(main())\n"
        ),
    }
    if not dry_run:
        destination.mkdir(parents=True, exist_ok=False)
        created_files: list[Path] = []
        try:
            for relative, content in files.items():
                file_path = _safe_join(project_root, relative)
                handle = file_path.open("x", encoding="utf-8", newline="\n")
                created_files.append(file_path)
                with handle:
                    handle.write(content)
        except Exception:
            for created_file in reversed(created_files):
                try:
                    created_file.unlink(missing_ok=True)
                except OSError:
                    pass
            try:
                destination.rmdir()
            except OSError:
                pass
            raise
    return {
        "status": "PASS",
        "root": str(project_root),
        "step_number": number,
        "step_path": relative_root,
        "created_files": sorted(files),
        "dry_run": dry_run,
    }


def _frontend_base(
    root: Path,
    application: str | None = None,
) -> tuple[str | None, str, list[str]]:
    if application:
        application_name = _validate_file_name(application)
        prefix = f"apps/{application_name}"
        if not (root / prefix).is_dir():
            raise StructureError(
                f"Requested application does not exist: {prefix}",
                "UNKNOWN_APPLICATION",
            )
        return (
            prefix,
            f"Selected the explicit monorepo application {prefix}/.",
            [],
        )

    fixed_candidates = [
        prefix
        for prefix in ("front", "frontend")
        if (root / prefix / "src").is_dir() or (root / prefix).is_dir()
    ]
    if len(fixed_candidates) == 1:
        prefix = fixed_candidates[0]
        return (
            prefix,
            f"Preserved existing convention: the repository uses {prefix}/.",
            [],
        )
    if len(fixed_candidates) > 1:
        return (
            None,
            "Multiple equivalent frontend roots exist; select one after resolving the structural conflict.",
            fixed_candidates,
        )
    if (root / "apps/web").is_dir():
        return (
            "apps/web",
            "Preserved existing convention: the monorepo uses apps/web/.",
            [],
        )

    apps_root = root / "apps"
    app_candidates: list[str] = []
    if apps_root.is_dir():
        try:
            app_candidates = sorted(
                f"apps/{child.name}"
                for child in apps_root.iterdir()
                if child.is_dir() and (child / "src").is_dir() and not child.is_symlink()
            )
        except OSError as exc:
            raise StructureError(
                f"Cannot inspect monorepo applications: {exc}",
                "APPLICATIONS_UNREADABLE",
            ) from exc
    if len(app_candidates) == 1:
        return (
            app_candidates[0],
            "Preserved the repository's only existing application source boundary.",
            [],
        )
    if len(app_candidates) > 1:
        return (
            None,
            "Multiple applications can own this frontend artifact; pass an explicit application.",
            app_candidates,
        )
    return (
        "",
        "Placed in the root frontend source tree selected by the current convention.",
        [],
    )


def _join_relative(*parts: str) -> str:
    return _validate_relative_path(PurePosixPath(*[part for part in parts if part]).as_posix())


def suggest_path(
    root: str | Path,
    *,
    artifact: str,
    name: str,
    owner: str | None = None,
    scope: str = "local",
    sequence: int | None = None,
    application: str | None = None,
) -> dict[str, Any]:
    """Return one responsibility-based path; never create it."""

    project_root = _root_path(root)
    artifact_key = str(artifact).strip().casefold()
    if scope not in {"local", "shared"}:
        raise StructureError("scope must be 'local' or 'shared'.", "INVALID_SCOPE")
    owner_slug = _slug(owner, label="owner") if owner else None
    route_manifest_error: StructureError | None = None
    try:
        route_manifest = _load_structure_manifest(
            project_root / ".project-structure.yaml"
        )
    except StructureError as exc:
        route_manifest = {}
        route_manifest_error = exc
    route_manifest_directories = route_manifest.get("directories")
    route_blueprint = str(route_manifest.get("blueprint") or "")
    declared_route_paths = [
        PurePosixPath(str(item.get("path", "")))
        for item in route_manifest_directories
        if isinstance(item, dict) and str(item.get("path", "")).strip()
    ] if isinstance(route_manifest_directories, list) else []

    def routed(
        *,
        status: str,
        path: str | None,
        responsibility: str,
        reason: str,
        rule_id: str,
        companions: Sequence[str] = (),
        alternatives: Sequence[str] = (),
    ) -> dict[str, Any]:
        companion_paths = list(companions)
        candidate_paths = ([path] if path else []) + companion_paths
        if status == "PASS" and declared_route_paths:
            undeclared = [
                candidate
                for candidate in candidate_paths
                if not any(
                    PurePosixPath(candidate) == declared
                    or declared in PurePosixPath(candidate).parents
                    for declared in declared_route_paths
                )
            ]
            if undeclared:
                status = "BLOCK"
                path = None
                companion_paths = []
                reason = (
                    "The structure manifest does not declare the target boundary for: "
                    + ", ".join(undeclared)
                )
                rule_id = "UNDECLARED_TARGET_BOUNDARY"
        existing_equivalent_directories: list[str] = []
        inferred_owner = owner_slug
        if path:
            pure_path = PurePosixPath(path)
            if inferred_owner is None and pure_path.parts:
                owner_parts = pure_path.parts[:2] if pure_path.parts[0] in {"data", "outputs"} else pure_path.parts[:1]
                inferred_owner = "/".join(owner_parts)
            parent = pure_path.parent
            while parent.as_posix() not in {"", "."}:
                if _safe_join(project_root, parent.as_posix()).is_dir():
                    existing_equivalent_directories.append(parent.as_posix())
                    break
                parent = parent.parent
        return {
            "status": status,
            "path": path,
            "artifact": artifact_key,
            "file_category": artifact_key,
            "responsibility": responsibility,
            "owner": inferred_owner,
            "reuse_scope": scope,
            "existing_equivalent_directories": existing_equivalent_directories,
            "inputs": {
                "project_root": str(project_root),
                "artifact": artifact_key,
                "name": name,
                "owner": owner_slug,
                "scope": scope,
                "application": application,
            },
            "outputs": ([path] if path else []) + companion_paths,
            "alternatives": list(alternatives),
            "reason": reason,
            "rule_id": rule_id,
            "companion_paths": companion_paths,
            "needs_confirmation": status != "PASS",
        }

    if route_manifest_error is not None:
        return routed(
            status="BLOCK",
            path=None,
            responsibility="Repair the recorded structure contract before routing files.",
            reason=str(route_manifest_error),
            rule_id=route_manifest_error.code,
        )

    if artifact_key == "directory":
        directory_name = _validate_file_name(name)
        if directory_name.casefold() in AMBIGUOUS_DIRECTORY_NAMES:
            return routed(
                status="BLOCK",
                path=None,
                responsibility="Create only directories with a bounded owner and purpose.",
                reason="The requested directory has no bounded responsibility or owner.",
                rule_id="UNSCOPED_AMBIGUOUS_DIRECTORY",
            )
        if owner_slug is None:
            return routed(
                status="BLOCK",
                path=None,
                responsibility="A new directory must have an explicit bounded owner.",
                reason="No owner was supplied for the proposed directory.",
                rule_id="OWNER_REQUIRED_FOR_DIRECTORY",
            )
        return routed(
            status="PASS",
            path=directory_name,
            responsibility="Bounded directory responsibility.",
            reason="The directory name states a bounded responsibility.",
            rule_id="RESPONSIBILITY_ROUTED",
        )

    if artifact_key == "research-step":
        step_slug = _slug(name, label="step name")
        if sequence is None:
            sequence = max(_existing_step_numbers(project_root / "steps"), default=0) + 1
        if sequence < 1 or sequence > 999:
            raise StructureError("Step number must be between 1 and 999.", "INVALID_STEP_NUMBER")
        width = max(2, len(str(sequence)))
        base = f"steps/{sequence:0{width}d}_{step_slug}"
        return routed(
            status="PASS",
            path=f"{base}/run.py",
            responsibility="Ordered research-step orchestration.",
            reason="A research step is a numbered orchestration entry point; reusable logic stays in src/.",
            rule_id="RESEARCH_STEP_ORCHESTRATION",
            companions=[f"{base}/README.md", f"{base}/config.yaml"],
        )

    file_name = _validate_file_name(name)
    frontend_prefix, frontend_reason, frontend_candidates = _frontend_base(
        project_root,
        application=application,
    )
    frontend_artifacts = {
        "frontend-feature",
        "frontend-api",
        "frontend-component",
        "frontend-ui",
    }
    if frontend_prefix is None and artifact_key in frontend_artifacts:
        return routed(
            status="BLOCK",
            path=None,
            responsibility="Select one owning frontend application before routing this artifact.",
            reason=frontend_reason,
            rule_id="AMBIGUOUS_FRONTEND_APP",
            alternatives=[f"{candidate}/src" for candidate in frontend_candidates],
        )
    frontend_src = _join_relative(frontend_prefix or "", "src")

    path: str
    reason: str
    responsibility: str
    companions: list[str] = []
    data_layers = {
        "data-external": "external",
        "data-raw": "raw",
        "data-interim": "interim",
        "data-processed": "processed",
    }
    output_layers = {
        "output-model": "models",
        "output-figure": "figures",
        "output-table": "tables",
        "output-log": "logs",
    }
    if artifact_key in data_layers:
        if artifact_key == "data-raw" and PurePosixPath(file_name).suffix.casefold() in SOURCE_SUFFIXES:
            return routed(
                status="BLOCK",
                path=None,
                responsibility="Raw data is immutable input and must not contain executable source.",
                reason="Executable source cannot be routed into data/raw.",
                rule_id="RAW_DATA_SOURCE_FORBIDDEN",
            )
        path = _join_relative("data", data_layers[artifact_key], file_name)
        responsibility = f"{data_layers[artifact_key]} data lifecycle storage."
        reason = "Data is routed to the lifecycle layer matching its provenance and mutability."
    elif artifact_key in output_layers:
        output_prefixes: dict[str, dict[str, str]] = {
            "data-science": {
                "output-model": "models",
                "output-figure": "reports/figures",
                "output-table": "reports/tables",
            },
            "machine-learning-pipeline": {
                "output-model": "checkpoints",
                "output-figure": "outputs/figures",
                "output-table": "outputs/metrics",
            },
        }
        selected_output_prefix = output_prefixes.get(route_blueprint, {}).get(
            artifact_key,
            _join_relative("outputs", output_layers[artifact_key]),
        )
        path = _join_relative(selected_output_prefix, file_name)
        responsibility = f"Generated {output_layers[artifact_key]} artifact storage."
        reason = (
            "Generated artifacts follow the selected blueprint's declared artifact boundary "
            "and never become source-of-truth code."
        )
    elif artifact_key == "notebook":
        if not owner_slug:
            raise StructureError("owner is required for a notebook phase.", "OWNER_REQUIRED")
        path = _join_relative("notebooks", owner_slug, file_name)
        responsibility = "Exploration or analysis notebook scoped to one phase."
        reason = "Notebooks are grouped by analysis phase and do not replace reusable src code."
    elif artifact_key in {"pipeline", "python-module"}:
        package = _first_src_package(project_root)
        if package is None:
            manifest = _read_json_object(project_root / ".project-structure.yaml")
            package = str(manifest.get("package_name") or _slug(project_root.name, label="package name"))
        if not owner_slug:
            raise StructureError(f"owner is required for {artifact_key}.", "OWNER_REQUIRED")
        if artifact_key == "pipeline":
            path = _join_relative("src", package, "pipelines", owner_slug, file_name)
            companions = [
                _join_relative("tests", "unit", "pipelines", owner_slug, f"test_{PurePosixPath(file_name).stem}.py")
            ]
            responsibility = "Reusable pipeline nodes and composition."
        else:
            path = _join_relative("src", package, owner_slug, file_name)
            companions = [
                _join_relative("tests", "unit", owner_slug, f"test_{PurePosixPath(file_name).stem}.py")
            ]
            responsibility = "Reusable Python implementation module."
        reason = "Reusable implementation belongs in the package src tree with a mirrored unit test."
    elif artifact_key == "script":
        path = _join_relative("scripts", file_name)
        responsibility = "Thin repository automation entry point."
        reason = "Scripts orchestrate reusable code and must stay small and bounded."
    elif artifact_key == "paper":
        if not owner_slug:
            raise StructureError("owner is required for a paper artifact.", "OWNER_REQUIRED")
        path = _join_relative("paper", owner_slug, file_name)
        responsibility = "Publication source or supplementary material."
        reason = "Publication artifacts are routed to their explicit paper phase."
    elif artifact_key in {"app", "package", "service"}:
        boundary = {"app": "apps", "package": "packages", "service": "services"}[artifact_key]
        boundary_name = _slug(file_name, label=f"{artifact_key} name")
        path = _join_relative(boundary, boundary_name)
        responsibility = f"Explicit {artifact_key} architectural boundary."
        reason = f"The {artifact_key} is routed to the repository's {boundary}/ boundary."
    elif artifact_key == "frontend-feature":
        if not owner_slug:
            raise StructureError("owner is required for a frontend feature.", "OWNER_REQUIRED")
        path = _join_relative(frontend_src, "features", owner_slug, "components", file_name)
        responsibility = "Feature-owned frontend component."
        reason = frontend_reason + " Feature-owned UI stays with its business owner."
    elif artifact_key == "frontend-api":
        if scope == "shared":
            path = _join_relative(frontend_src, "services", file_name)
            responsibility = "Cross-feature frontend service adapter."
            reason = frontend_reason + " A cross-feature API client belongs in shared services."
        else:
            if not owner_slug:
                raise StructureError("owner is required for a local frontend API.", "OWNER_REQUIRED")
            path = _join_relative(frontend_src, "features", owner_slug, "api", file_name)
            responsibility = "Feature-owned frontend API adapter."
            reason = frontend_reason + " A feature-local API client stays with its owner."
    elif artifact_key in {"frontend-component", "frontend-ui"}:
        layer = "ui" if scope == "shared" else "common"
        path = _join_relative(frontend_src, "components", layer, file_name)
        responsibility = "Frontend component routed by reuse scope."
        reason = frontend_reason + " The component is routed by its declared reuse scope."
    elif artifact_key in {"backend-service", "backend-route", "backend-schema", "backend-model", "backend-repository"}:
        if route_blueprint == "microservices":
            if not owner_slug:
                raise StructureError(
                    "owner must identify the target service in a microservices project.",
                    "OWNER_REQUIRED",
                )
            if not (project_root / "services" / owner_slug).is_dir():
                return routed(
                    status="BLOCK",
                    path=None,
                    responsibility="Select an existing owning service before routing backend code.",
                    reason=f"The service services/{owner_slug}/ does not exist.",
                    rule_id="UNKNOWN_SERVICE",
                )
            backend_base = f"services/{owner_slug}/src"
            backend_test_base = f"services/{owner_slug}/tests"
        elif (project_root / "backend/app").is_dir():
            backend_base = "backend/app"
            backend_test_base = "backend/tests"
        elif (project_root / "apps/api/src").is_dir():
            backend_base = "apps/api/src"
            backend_test_base = "apps/api/tests"
        else:
            backend_base = "app"
            backend_test_base = "tests"
        layers = {
            "backend-service": "services",
            "backend-route": "api/routes",
            "backend-schema": "schemas",
            "backend-model": "models",
            "backend-repository": "repositories",
        }
        path = _join_relative(backend_base, layers[artifact_key], file_name)
        responsibility = f"Backend {layers[artifact_key]} implementation."
        companions = [
            _join_relative(
                backend_test_base,
                "unit",
                layers[artifact_key].split("/")[-1],
                f"test_{PurePosixPath(file_name).stem}.py",
            )
        ]
        reason = "Backend code is routed to the narrow layer matching its responsibility."
    elif artifact_key == "research-code":
        package = _first_src_package(project_root)
        if package is None:
            manifest = _read_json_object(project_root / ".project-structure.yaml")
            package = str(manifest.get("package_name") or _slug(project_root.name, label="package name"))
        if not owner_slug:
            raise StructureError("owner is required for reusable research code.", "OWNER_REQUIRED")
        path = _join_relative("src", package, owner_slug, file_name)
        companions = [
            _join_relative("tests", "unit", owner_slug, f"test_{PurePosixPath(file_name).stem}.py")
        ]
        responsibility = "Reusable research implementation."
        reason = "Reusable research implementation belongs in the package src tree, not in steps/."
    elif artifact_key == "experiment":
        if not owner_slug:
            raise StructureError("owner is required for an experiment.", "OWNER_REQUIRED")
        path = _join_relative("experiments", owner_slug, file_name)
        responsibility = "Experiment-specific configuration or record."
        reason = "Experiment-specific configuration and records stay under experiments/."
    elif artifact_key in {"documentation", "doc"}:
        path = _join_relative("docs", file_name)
        responsibility = "Repository documentation."
        reason = "Repository documentation belongs in the explicit docs boundary."
    elif artifact_key == "test":
        path = _join_relative("tests", owner_slug or "unit", file_name)
        responsibility = "Automated correctness or reproducibility test."
        reason = "Tests stay in the test boundary and mirror the closest explicit owner."
    elif artifact_key == "configuration":
        path = _join_relative("configs", owner_slug or "default", file_name)
        responsibility = "Versioned runtime configuration."
        reason = "Versioned runtime configuration belongs under configs/."
    else:
        raise StructureError(f"Unsupported artifact type: {artifact}", "UNKNOWN_ARTIFACT")

    return routed(
        status="PASS",
        path=path,
        responsibility=responsibility,
        reason=reason,
        rule_id="RESPONSIBILITY_ROUTED",
        companions=companions,
    )


def _finding(rule_id: str, severity: str, path: str, message: str, recommendation: str) -> dict[str, str]:
    return {
        "rule_id": rule_id,
        "severity": severity,
        "path": path,
        "message": message,
        "recommendation": recommendation,
    }


def _relative_files(
    root: Path,
    excluded: Iterable[str] = AUDIT_TRAVERSAL_EXCLUDES,
) -> list[tuple[Path, str]]:
    result: list[tuple[Path, str]] = []
    excluded_names = {str(item).casefold() for item in excluded}
    try:
        for current, directory_names, file_names in os.walk(
            root,
            topdown=True,
            followlinks=False,
        ):
            current_path = Path(current)
            retained_directories: list[str] = []
            for directory_name in sorted(directory_names, key=str.casefold):
                candidate = current_path / directory_name
                if directory_name.casefold() in excluded_names:
                    continue
                try:
                    if candidate.is_symlink():
                        continue
                except OSError:
                    continue
                retained_directories.append(directory_name)
            directory_names[:] = retained_directories
            for file_name in sorted(file_names, key=str.casefold):
                path = current_path / file_name
                try:
                    if path.is_symlink() or not path.is_file():
                        continue
                except OSError:
                    continue
                result.append((path, path.relative_to(root).as_posix()))
    except OSError as exc:
        raise StructureError(f"Cannot inspect project tree: {exc}", "ROOT_UNREADABLE") from exc
    return sorted(result, key=lambda item: item[1].casefold())


def audit_structure(root: str | Path, blueprint_id: str | None = None) -> dict[str, Any]:
    """Audit structural drift without applying filesystem changes."""

    project_root = _root_path(root)
    detection = detect_project(project_root)
    findings: list[dict[str, str]] = []
    manifest_path = project_root / ".project-structure.yaml"
    manifest: dict[str, Any] = {}
    manifest_is_valid = False
    if manifest_path.exists():
        try:
            manifest = _load_structure_manifest(manifest_path)
            manifest_is_valid = True
        except StructureError as exc:
            findings.append(
                _finding(
                    exc.code,
                    "BLOCK",
                    ".project-structure.yaml",
                    str(exc),
                    "Repair the manifest from the required asset and re-audit before relying on it.",
                )
            )
    documented_blueprint = (
        manifest.get("blueprint")
        if manifest_is_valid and manifest.get("blueprint") in BLUEPRINT_IDS
        else None
    )
    selected_blueprint = (
        blueprint_id or documented_blueprint or detection.get("selected_blueprint")
    )
    if selected_blueprint is not None and selected_blueprint not in BLUEPRINT_IDS:
        raise StructureError(f"Unknown blueprint: {selected_blueprint}", "UNKNOWN_BLUEPRINT")

    if detection.get("needs_confirmation"):
        ambiguities = detection.get("ambiguities") or [
            "The project structure could not be classified with sufficient confidence."
        ]
        findings.append(
            _finding(
                "DETECTION_NEEDS_CONFIRMATION",
                "CAUTION",
                ".",
                " ".join(str(item) for item in ambiguities),
                "Confirm the project blueprint before structural writes or a PASS audit.",
            )
        )

    if blueprint_id and detection.get("selected_blueprint") and blueprint_id != detection["selected_blueprint"]:
        findings.append(
            _finding(
                "BLUEPRINT_CONFLICT",
                "CAUTION",
                ".",
                f"Requested blueprint {blueprint_id!r} conflicts with detected convention {detection['selected_blueprint']!r}.",
                "Preserve the coherent existing convention or document and explicitly approve a migration.",
            )
        )

    # Only root-level catch-all directories are unambiguously unscoped. Package-local
    # utils/common directories may have a documented bounded responsibility.
    try:
        root_children = list(project_root.iterdir())
    except OSError as exc:
        raise StructureError(f"Cannot inspect root directory: {exc}", "ROOT_UNREADABLE") from exc
    for child in sorted(root_children, key=lambda item: item.name.casefold()):
        if child.is_dir() and child.name.casefold() in AMBIGUOUS_DIRECTORY_NAMES:
            findings.append(
                _finding(
                    "AMBIGUOUS_DIRECTORY",
                    "BLOCK",
                    child.name,
                    "Top-level catch-all directory has no bounded responsibility.",
                    "Replace it with an owner- or responsibility-specific directory; do not move files automatically.",
                )
            )

    root_directory_names = {
        child.name.casefold() for child in root_children if child.is_dir() and not child.is_symlink()
    }
    synonym_groups = (
        {"front", "frontend"},
        {"back", "backend"},
        {"infra", "infrastructure"},
        {"test", "tests"},
        {"doc", "docs", "documentation"},
    )
    for group in synonym_groups:
        present = sorted(group & root_directory_names)
        if len(present) > 1:
            findings.append(
                _finding(
                    "SYNONYMOUS_DIRECTORY",
                    "BLOCK",
                    ",".join(present),
                    "Multiple top-level directories represent the same responsibility.",
                    "Choose the established convention and plan a minimal migration explicitly; do not auto-move.",
                )
            )

    declared_directory_items: list[Mapping[str, Any]] = []
    undeclared_severity = "BLOCK"
    if manifest_is_valid and isinstance(manifest.get("directories"), list):
        declared_directory_items = [
            item for item in manifest["directories"] if isinstance(item, dict)
        ]
    elif selected_blueprint and not detection.get("needs_confirmation"):
        declared_directory_items = list(load_blueprint(selected_blueprint)["directories"])
        undeclared_severity = "CAUTION"

    if declared_directory_items:
        declared_roots = {
            PurePosixPath(str(item.get("path", ""))).parts[0].casefold()
            for item in declared_directory_items
            if str(item.get("path", "")).strip()
        }
        for child in sorted(root_children, key=lambda item: item.name.casefold()):
            if (
                child.is_dir()
                and not child.is_symlink()
                and not child.name.startswith(".")
                and child.name.casefold() not in AUDIT_DECLARATION_EXCLUDES
                and child.name.casefold() not in declared_roots
            ):
                findings.append(
                    _finding(
                        "UNDECLARED_TOP_LEVEL",
                        undeclared_severity,
                        child.name,
                        "Top-level directory is outside the selected structure boundary.",
                        "Document a bounded responsibility in the manifest before keeping this boundary.",
                    )
                )

    if not manifest_is_valid and selected_blueprint and not detection.get("needs_confirmation"):
        required_roots = {
            PurePosixPath(str(item["path"])).parts[0].casefold()
            for item in load_blueprint(selected_blueprint)["directories"]
            if item.get("required", True) and not item.get("conditional")
        }
        for missing_root in sorted(required_roots - root_directory_names):
            findings.append(
                _finding(
                    "MISSING_BLUEPRINT_ROOT",
                    "CAUTION",
                    missing_root,
                    "A required top-level boundary from the detected blueprint is absent.",
                    "Confirm the blueprint, then document or add the missing boundary without moving unrelated files.",
                )
            )

    files = _relative_files(project_root)
    root_source_exceptions = {"setup.py", "manage.py", "conftest.py"}
    for path, relative in files:
        pure = PurePosixPath(relative)
        parts = pure.parts
        lower_parts = [part.casefold() for part in parts]
        suffix = path.suffix.casefold()
        in_source_boundary = bool(
            lower_parts
            and (
                lower_parts[0] in {"src", "app"}
                or (
                    lower_parts[0] in {"front", "frontend"}
                    and len(lower_parts) >= 2
                    and lower_parts[1] == "src"
                )
                or (
                    lower_parts[0] == "backend"
                    and len(lower_parts) >= 2
                    and lower_parts[1] == "app"
                )
                or (
                    lower_parts[0] in {"apps", "packages", "services"}
                    and "src" in lower_parts[:4]
                )
            )
        )
        if in_source_boundary and suffix in DATA_OR_OUTPUT_SUFFIXES:
            findings.append(
                _finding(
                    "DATA_OR_OUTPUT_IN_SOURCE",
                    "BLOCK",
                    relative,
                    "Data or generated output is mixed into a source-code boundary.",
                    "Route data to data/ and generated artifacts to the blueprint's artifact boundary.",
                )
            )
        if (
            in_source_boundary
            and suffix in {".md", ".rst", ".adoc"}
            and path.name.casefold() not in {"agents.md", "readme.md"}
        ):
            findings.append(
                _finding(
                    "DOCUMENTATION_IN_SOURCE",
                    "CAUTION",
                    relative,
                    "Repository documentation is mixed into a source-code boundary.",
                    "Keep implementation documentation in docs/ unless the nearest package explicitly owns it.",
                )
            )
        if lower_parts and lower_parts[0] in {"doc", "docs", "documentation"} and suffix in SOURCE_SUFFIXES:
            findings.append(
                _finding(
                    "SOURCE_IN_DOCUMENTATION",
                    "BLOCK",
                    relative,
                    "Executable source-of-truth code is mixed into documentation.",
                    "Move implementation to its owning source boundary through an explicit migration.",
                )
            )
        if (
            selected_blueprint == "web-typescript-monorepo"
            and lower_parts
            and lower_parts[0] == "src"
            and suffix in SOURCE_SUFFIXES
        ):
            findings.append(
                _finding(
                    "ROOT_SOURCE_DIRECTORY",
                    "BLOCK",
                    relative,
                    "Root src/ bypasses the monorepo's apps/ and packages/ ownership boundaries.",
                    "Route the file to one explicit app or package; do not keep a parallel root source tree.",
                )
            )
        if len(parts) == 1 and suffix in SOURCE_SUFFIXES and path.name.casefold() not in root_source_exceptions:
            findings.append(
                _finding(
                    "ROOT_SOURCE_FILE",
                    "BLOCK",
                    relative,
                    "Source implementation is placed at repository root.",
                    "Route it to the owning app, package, service, or src layer.",
                )
            )
        if parts and parts[0].casefold() in {"outputs", "dist", "build", "checkpoints"} and suffix in SOURCE_SUFFIXES:
            findings.append(
                _finding(
                    "SOURCE_IN_GENERATED_OUTPUT",
                    "BLOCK",
                    relative,
                    "Source-of-truth implementation is mixed with generated output.",
                    "Keep source in src/app/package boundaries and regenerate outputs from it.",
                )
            )
        if len(parts) >= 2 and parts[0].casefold() == "data" and parts[1].casefold() == "raw" and suffix in SOURCE_SUFFIXES:
            findings.append(
                _finding(
                    "RAW_DATA_CONTAMINATION",
                    "BLOCK",
                    relative,
                    "Executable source is mixed into immutable raw data.",
                    "Move implementation to src/ through an explicitly approved migration.",
                )
            )
        if parts and parts[0].casefold() == "steps":
            if suffix in DATA_OR_OUTPUT_SUFFIXES:
                findings.append(
                    _finding(
                        "DATA_OR_OUTPUT_IN_STEP",
                        "BLOCK",
                        relative,
                        "Data or generated output is stored inside an orchestration step.",
                        "Store data under data/ and generated artifacts under outputs/.",
                    )
                )
            if suffix in SOURCE_SUFFIXES and path.name.casefold() != "__init__.py":
                line_count = len(_read_small_text(path).splitlines())
                if line_count >= 100:
                    findings.append(
                        _finding(
                            "REUSABLE_LOGIC_IN_STEP",
                            "BLOCK",
                            relative,
                            "A large implementation file is trapped inside a workflow step.",
                            "Keep the step as a thin entry point and move reusable logic to src/ only with explicit approval.",
                        )
                    )
        if (
            parts
            and parts[0].casefold() == "scripts"
            and suffix in SOURCE_SUFFIXES
            and path.name.casefold() != "__init__.py"
            and len(_read_small_text(path).splitlines()) >= 100
        ):
            findings.append(
                _finding(
                    "REUSABLE_LOGIC_IN_SCRIPT",
                    "BLOCK",
                    relative,
                    "A large reusable implementation is trapped in a script entry point.",
                    "Keep scripts thin and place reusable implementation in the owning src/app/package boundary.",
                )
            )
        if len(parts) >= 5 and lower_parts[0] == "packages" and "src" in lower_parts:
            src_index = lower_parts.index("src")
            if src_index + 1 < len(parts) and lower_parts[src_index + 1] in {"app", "apps"}:
                findings.append(
                    _finding(
                        "APP_CODE_IN_SHARED_PACKAGE",
                        "BLOCK",
                        relative,
                        "Application-specific code is nested inside a shared package.",
                        "Keep it in the owning app or define a genuinely reusable package boundary.",
                    )
                )

    root_src = project_root / "src"
    if root_src.is_dir():
        root_src_files = [(path, relative) for path, relative in files if relative.startswith("src/")]
        has_frontend_source = any(path.suffix.casefold() in {".js", ".jsx", ".ts", ".tsx", ".vue"} for path, _ in root_src_files)
        has_backend_source = any(path.suffix.casefold() in {".py", ".java", ".cs", ".go", ".rs"} for path, _ in root_src_files)
        has_deployment = any(
            path.name.casefold() in {"deployment.yaml", "deployment.yml", "dockerfile", "compose.yaml", "compose.yml"}
            or "deployment" in path.name.casefold()
            for path, _ in root_src_files
        )
        if has_frontend_source and has_backend_source and has_deployment:
            findings.append(
                _finding(
                    "MIXED_ROOT_SOURCE",
                    "BLOCK",
                    "src",
                    "Frontend, backend, and deployment responsibilities are mixed in one root source directory.",
                    "Define separate application and infrastructure boundaries; do not mass-move automatically.",
                )
            )

    if manifest_is_valid and selected_blueprint:
        manifest_directories = manifest.get("directories", [])
        if isinstance(manifest_directories, list):
            for item in manifest_directories:
                if not isinstance(item, dict) or not item.get("required", True):
                    continue
                relative = str(item.get("path", ""))
                if not relative:
                    continue
                try:
                    exists = _safe_join(project_root, relative).is_dir()
                except StructureError:
                    findings.append(
                        _finding(
                            "INVALID_MANIFEST_PATH",
                            "BLOCK",
                            relative,
                            "The manifest contains an unsafe directory path.",
                            "Repair the manifest after confirming the intended boundary.",
                        )
                    )
                    continue
                if not exists:
                    findings.append(
                        _finding(
                            "MISSING_REQUIRED_DIRECTORY",
                            "CAUTION",
                            relative,
                            "A directory required by the recorded blueprint is missing.",
                            "Confirm whether the directory was intentionally removed before restoring it.",
                        )
                    )

    # De-duplicate stable findings in case one file matched equivalent traversal paths.
    unique: dict[tuple[str, str], dict[str, str]] = {}
    for item in findings:
        unique[(item["rule_id"], item["path"])] = item
    findings = sorted(
        unique.values(),
        key=lambda item: (
            0 if item["severity"] == "BLOCK" else 1,
            item["rule_id"],
            item["path"].casefold(),
        ),
    )
    block_count = sum(item["severity"] == "BLOCK" for item in findings)
    caution_count = sum(item["severity"] == "CAUTION" for item in findings)
    status = "BLOCK" if block_count else "CAUTION" if caution_count else "PASS"
    return {
        "status": status,
        "root": str(project_root),
        "selected_blueprint": selected_blueprint,
        "detected_blueprint": detection.get("selected_blueprint"),
        "classification": (
            load_blueprint(selected_blueprint)["classification"]
            if selected_blueprint
            else detection.get("classification", {"purpose": "unknown"})
        ),
        "findings": findings,
        "summary": {
            "block": block_count,
            "caution": caution_count,
            "total": len(findings),
        },
        "actions_applied": [],
        "needs_confirmation": detection.get("needs_confirmation", False),
    }


def error_payload(exc: BaseException) -> dict[str, Any]:
    """Build the CLI's stable JSON error envelope."""

    if isinstance(exc, StructureError):
        code = exc.code
        message = str(exc)
    else:
        code = "INTERNAL_ERROR"
        message = str(exc) or exc.__class__.__name__
    blocking_codes = {
        "AMBIGUOUS_EXISTING_STRUCTURE",
        "BLUEPRINT_CONFLICT",
        "INVALID_STRUCTURE_MANIFEST",
        "INVALID_STRUCTURE_MANIFEST_SCHEMA",
        "RESEARCH_STEP_NOT_ALLOWED",
    }
    return {
        "status": "BLOCK" if code in blocking_codes else "ERROR",
        "error_code": code,
        "message": message,
    }


__all__ = [
    "BLUEPRINT_IDS",
    "StructureError",
    "add_research_step",
    "audit_structure",
    "configure_utf8_stdio",
    "detect_project",
    "error_payload",
    "load_blueprint",
    "render_tree",
    "scaffold_project",
    "status_exit_code",
    "suggest_path",
]
