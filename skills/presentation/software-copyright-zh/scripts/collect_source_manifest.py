#!/usr/bin/env python3
"""Collect a traceable manifest of real source files without executing project code."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


CONTRACT_VERSION = "software-copyright-cli/v1"
STATUS_EXIT_CODES = {"PASS": 0, "CAUTION": 1, "BLOCK": 2, "ERROR": 3}

SOURCE_EXTENSIONS = {
    ".py": "Python",
    ".pyw": "Python",
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".mts": "TypeScript",
    ".cts": "TypeScript",
    ".tsx": "TypeScript",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".c": "C",
    ".h": "C/C++ Header",
    ".cc": "C++",
    ".cpp": "C++",
    ".cxx": "C++",
    ".hpp": "C++ Header",
    ".hh": "C++ Header",
    ".go": "Go",
    ".cs": "C#",
    ".php": "PHP",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".swift": "Swift",
    ".m": "Objective-C/MATLAB",
    ".mm": "Objective-C++",
    ".scala": "Scala",
    ".dart": "Dart",
    ".r": "R",
    ".sql": "SQL",
    ".sh": "Shell",
    ".ps1": "PowerShell",
}

EXCLUDED_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "coverage",
    ".coverage",
    ".next",
    ".nuxt",
    ".cache",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "__pycache__",
    "target",
    "out",
}

THIRD_PARTY_DIR_NAMES = {
    "node_modules",
    "vendor",
    ".venv",
    "venv",
    "site-packages",
    "third_party",
    "third-party",
    "external",
}

LOCK_FILE_NAMES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "uv.lock",
    "pipfile.lock",
    "composer.lock",
    "cargo.lock",
    "go.sum",
}


class JsonArgumentParser(argparse.ArgumentParser):
    """Turn argument errors into exceptions so callers receive JSON diagnostics."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # argparse can render help before a CLI reaches emit_json(). Configure
        # both streams before the parser formats anything so Windows code pages
        # cannot corrupt Chinese paths or help text.
        configure_utf8_stdio()
        super().__init__(*args, **kwargs)

    def error(self, message: str) -> None:  # pragma: no cover - exercised through CLIs
        raise ValueError(message)


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def configure_utf8_stdout() -> None:
    """Backward-compatible alias used by emit_json()."""

    configure_utf8_stdio()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def make_result(tool: str, status: str, summary: Any, **extra: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "tool": tool,
        "status": status,
        "summary": summary,
        "findings": [],
    }
    result.update(extra)
    return result


def make_finding(
    rule_id: str,
    severity: str,
    path: str,
    message: str,
    *,
    line: int | None = None,
) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "severity": severity,
        "path": path,
        "line": line,
        "message": message,
    }


def emit_json(result: dict[str, Any]) -> int:
    configure_utf8_stdout()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return STATUS_EXIT_CODES.get(str(result.get("status", "ERROR")).upper(), 3)


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        Path(temp_name).replace(path)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise


def atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(payload)
        Path(temp_name).replace(path)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise


def write_json(path: Path, payload: Any) -> None:
    atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as stream:
        return json.load(stream)


def validate_source_manifest_payload(payload: Any, *, context: str = "source manifest") -> dict[str, Any]:
    """Validate the nested shape consumed by count/selection tools.

    This intentionally checks only fields those tools rely on. It prevents a
    syntactically valid JSON value such as ``{"files": ["bad-shape"]}`` from
    escaping as AttributeError/TypeError and breaking the JSON CLI contract.
    """

    if not isinstance(payload, dict):
        raise ValueError(f"{context} must contain a JSON object")
    files = payload.get("files")
    if not isinstance(files, list):
        raise ValueError(f"{context}.files must be an array")
    for index, item in enumerate(files):
        item_path = f"{context}.files[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{item_path} must be an object")
        path = item.get("path")
        if not isinstance(path, str) or not path.strip():
            raise ValueError(f"{item_path}.path must be a non-empty string")
        language = item.get("language")
        if language is not None and not isinstance(language, str):
            raise ValueError(f"{item_path}.language must be a string or null")
        line_count = item.get("line_count")
        if isinstance(line_count, bool) or not isinstance(line_count, int) or line_count < 0:
            raise ValueError(f"{item_path}.line_count must be a non-negative integer")
        sha256 = item.get("sha256")
        if sha256 is not None and not isinstance(sha256, str):
            raise ValueError(f"{item_path}.sha256 must be a string or null")
        category = item.get("category")
        if category is not None and not isinstance(category, str):
            raise ValueError(f"{item_path}.category must be a string or null")
        third_party = item.get("is_third_party")
        if third_party is not None and not isinstance(third_party, bool):
            raise ValueError(f"{item_path}.is_third_party must be a boolean or null")
    return payload


def resolve_existing_root(path: str | Path) -> Path:
    root = Path(path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Project root does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Project root is not a directory: {root}")
    return root


def is_within_root(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve(strict=False).relative_to(root.resolve())
        return True
    except (ValueError, OSError):
        return False


def ensure_within_root(root: Path, candidate: Path) -> Path:
    resolved = candidate.expanduser().resolve(strict=False)
    if not is_within_root(root, resolved):
        raise ValueError(f"Path is outside project root: {candidate}")
    return resolved


def relative_posix(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def language_for_path(path: Path) -> str | None:
    return SOURCE_EXTENSIONS.get(path.suffix.lower())


def is_generated_or_lock_file(path: Path) -> bool:
    name = path.name.lower()
    if name in LOCK_FILE_NAMES:
        return True
    return (
        name.endswith((".min.js", ".min.css", ".map"))
        or ".generated." in name
        or name.endswith((".g.cs", ".designer.cs"))
    )


def is_source_file(path: Path) -> bool:
    return language_for_path(path) is not None and not is_generated_or_lock_file(path)


def is_third_party_path(path: str | Path, root: Path | None = None) -> bool:
    candidate = Path(path)
    if root is not None and not candidate.is_absolute():
        candidate = root / candidate
    parts = {part.lower() for part in candidate.parts}
    return bool(parts & THIRD_PARTY_DIR_NAMES)


def count_text_lines(path: Path) -> int:
    """Count physical lines; LF, CRLF and CR are equal and a trailing newline adds no line."""

    data = path.read_bytes()
    if not data:
        return 0
    return len(data.splitlines())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sha256(path: Path, expected: str) -> bool:
    return bool(expected) and sha256_file(path).lower() == expected.lower()


def categorize_source(path: Path, root: Path) -> str:
    rel = relative_posix(path, root).lower()
    parts = set(Path(rel).parts)
    stem = path.stem.lower()
    if stem in {"main", "app", "index", "server", "application", "manage"}:
        return "entry"
    if parts & {"routes", "router", "routers", "urls"} or "route" in stem or "router" in stem:
        return "route"
    if parts & {"pages", "views", "screens"}:
        return "page"
    if parts & {"components", "widgets"}:
        return "component"
    if parts & {"api", "clients", "controllers"}:
        return "api"
    if parts & {"state", "store", "stores"}:
        return "state"
    if parts & {"services", "service", "usecases", "use_cases"} or stem.endswith("service"):
        return "service"
    if parts & {"repositories", "repository", "data"}:
        return "data"
    if parts & {"models", "model", "entities", "schemas"} or stem.endswith("model"):
        return "model"
    if parts & {"algorithms", "algorithm", "solvers", "engine"}:
        return "algorithm"
    return "source"


def iter_source_files(root: Path) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    excluded: set[str] = set()
    for current, dir_names, file_names in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        kept_dirs: list[str] = []
        for name in dir_names:
            candidate = current_path / name
            if name.lower() in EXCLUDED_DIR_NAMES or candidate.is_symlink():
                excluded.add(name)
                continue
            if is_within_root(root, candidate):
                kept_dirs.append(name)
        dir_names[:] = kept_dirs
        for name in file_names:
            candidate = current_path / name
            if candidate.is_symlink() or not is_within_root(root, candidate):
                continue
            if is_source_file(candidate):
                files.append(candidate)
    files.sort(key=lambda item: relative_posix(item, root).lower())
    return files, sorted(excluded, key=str.lower)


def collect_source_manifest(project_root: str | Path) -> dict[str, Any]:
    root = resolve_existing_root(project_root)
    files, excluded = iter_source_files(root)
    entries: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    for path in files:
        rel = relative_posix(path, root)
        try:
            entry = {
                "path": rel,
                "language": language_for_path(path) or "Unknown",
                "line_count": count_text_lines(path),
                "sha256": sha256_file(path),
                "category": categorize_source(path, root),
                "is_third_party": is_third_party_path(path, root),
                "selection_reason": "",
            }
            entries.append(entry)
        except OSError as exc:
            findings.append(make_finding("SOURCE_FILE_UNREADABLE", "CAUTION", rel, str(exc)))
    by_language: dict[str, int] = {}
    total_lines = 0
    for entry in entries:
        language = str(entry["language"])
        by_language[language] = by_language.get(language, 0) + int(entry["line_count"])
        total_lines += int(entry["line_count"])
    status = "PASS" if entries else "CAUTION"
    if not entries:
        findings.append(
            make_finding(
                "NO_SOURCE_FILES_FOUND",
                "CAUTION",
                ".",
                "No recognized source files were found; use generic project evidence and confirm the root.",
            )
        )
    result = make_result(
        "collect_source_manifest",
        status,
        {"source_files": len(entries), "total_source_lines": total_lines},
        schema_version=1,
        generated_at=utc_now(),
        project_root=str(root),
        files=entries,
        by_language=dict(sorted(by_language.items())),
        excluded_directories=excluded,
        line_count_definition="Physical lines; LF/CRLF/CR supported; comments and blank lines count; trailing newline adds no line.",
    )
    result["findings"] = findings
    return result


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = JsonArgumentParser(description="Collect source paths, line counts and SHA-256 hashes.")
    parser.add_argument("project_root", help="Root directory of the real project")
    parser.add_argument("--output", type=Path, help="Optional JSON output path within the project root")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        root = resolve_existing_root(args.project_root)
        result = collect_source_manifest(root)
        if args.output:
            output = ensure_within_root(root, args.output)
            write_json(output, result)
            result["outputs"] = [relative_posix(output, root)]
        return emit_json(result)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = make_result("collect_source_manifest", "ERROR", "Source manifest collection failed")
        result["findings"] = [make_finding("SOURCE_MANIFEST_ERROR", "ERROR", ".", str(exc))]
        return emit_json(result)


if __name__ == "__main__":
    raise SystemExit(main())
