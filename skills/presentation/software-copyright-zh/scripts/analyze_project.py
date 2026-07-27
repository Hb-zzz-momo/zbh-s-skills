#!/usr/bin/env python3
"""Analyze technical project evidence without inferring industry or business value."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from collect_source_manifest import (
    JsonArgumentParser,
    atomic_write_text,
    collect_source_manifest,
    emit_json,
    ensure_within_root,
    load_json,
    make_finding,
    make_result,
    relative_posix,
    resolve_existing_root,
    sha256_file,
    utc_now,
    write_json,
)


ROUTE_PATTERNS = (
    re.compile(r"@(?:app|router|blueprint)\.(?:get|post|put|delete|patch|route)\(\s*['\"]([^'\"]+)"),
    re.compile(r"\bpath\(\s*['\"]([^'\"]+)"),
    re.compile(r"\b(?:router|app)\.(?:get|post|put|delete|patch)\(\s*['\"]([^'\"]+)"),
    re.compile(r"\bpath\s*:\s*['\"]([^'\"]+)"),
    re.compile(r"@(?:Get|Post|Put|Delete|Patch|Request)Mapping\(\s*(?:value\s*=\s*)?['\"]([^'\"]+)"),
)
RUNTIME_SENSITIVE_PATTERN = re.compile(
    r"(?i)\b(?:api[_-]?key|access[_-]?token|password|client[_-]?secret|private[_-]?key)\s*[:=]"
    r"|(?<!\d)1[3-9]\d{9}(?!\d)"
    r"|(?<!\d)[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[0-9Xx](?!\d)"
)


def read_text_safe(path: Path, limit: int = 512_000) -> str:
    data = path.read_bytes()[:limit]
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return ""


def load_package_json(root: Path) -> dict[str, Any]:
    path = root / "package.json"
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("package.json must contain a JSON object")
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        value = payload.get(key)
        if value is not None and not isinstance(value, dict):
            raise ValueError(f"package.json.{key} must be an object")
    version = payload.get("version")
    if version is not None and not isinstance(version, str):
        raise ValueError("package.json.version must be a string")
    return payload


def detect_layout(root: Path) -> str:
    root_dirs = {item.name.lower() for item in root.iterdir() if item.is_dir() and not item.is_symlink()}
    frontend = bool(root_dirs & {"frontend", "front", "client", "web"})
    backend = bool(root_dirs & {"backend", "server", "api"})
    if frontend and backend:
        return "frontend-backend-separated"
    if {"apps", "packages"}.issubset(root_dirs):
        return "monorepo"
    return "single-or-generic"


def detect_technology_stack(root: Path, manifest: dict[str, Any]) -> tuple[list[str], dict[str, list[str]]]:
    detected: set[str] = set()
    evidence: dict[str, set[str]] = {}

    def add(name: str, path: str) -> None:
        detected.add(name)
        evidence.setdefault(name, set()).add(path)

    for item in manifest.get("files", []):
        language = str(item.get("language", ""))
        rel = str(item.get("path", ""))
        if language == "Python":
            add("Python", rel)
        elif language == "JavaScript":
            add("JavaScript", rel)
        elif language == "TypeScript":
            add("TypeScript", rel)
        elif language == "Vue":
            add("Vue", rel)
        elif language == "Java":
            add("Java", rel)
        elif language in {"C", "C++", "C/C++ Header", "C++ Header"}:
            add("C/C++", rel)
        elif language == "Go":
            add("Go", rel)
        elif language:
            add(language, rel)
        suffix = Path(rel).suffix.lower()
        if suffix in {".jsx", ".tsx"}:
            add("React", rel)

    package = load_package_json(root)
    package_deps: dict[str, Any] = {}
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        value = package.get(key, {})
        if isinstance(value, dict):
            package_deps.update({str(k).lower(): v for k, v in value.items()})
    if "react" in package_deps or "next" in package_deps:
        add("React", "package.json")
    if "vue" in package_deps or "nuxt" in package_deps:
        add("Vue", "package.json")

    manifest_texts: list[tuple[str, str]] = []
    for name in (
        "requirements.txt",
        "pyproject.toml",
        "Pipfile",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
    ):
        path = root / name
        if path.is_file():
            manifest_texts.append((name, read_text_safe(path).lower()))
    for name, text in manifest_texts:
        if "flask" in text:
            add("Flask", name)
        if "django" in text:
            add("Django", name)
        if "fastapi" in text:
            add("FastAPI", name)
        if "spring-boot" in text or "org.springframework.boot" in text:
            add("Spring Boot", name)

    for item in manifest.get("files", []):
        rel = str(item.get("path", ""))
        path = root / rel
        if path.suffix.lower() not in {".py", ".java"}:
            continue
        text = read_text_safe(path).lower()
        if not text:
            continue
        if "from flask" in text or "import flask" in text:
            add("Flask", rel)
        if "from django" in text or "import django" in text or "installed_apps" in text:
            add("Django", rel)
        if "from fastapi" in text or "import fastapi" in text:
            add("FastAPI", rel)
        if "@springbootapplication" in text or "org.springframework" in text:
            add("Spring Boot", rel)

    ordered = sorted(detected, key=str.lower)
    return ordered, {key: sorted(values, key=str.lower) for key, values in sorted(evidence.items())}


def extract_routes(root: Path, manifest: dict[str, Any]) -> tuple[list[str], list[dict[str, str]]]:
    routes: set[str] = set()
    route_evidence: list[dict[str, str]] = []
    for item in manifest.get("files", []):
        rel = str(item.get("path", ""))
        path = root / rel
        if path.suffix.lower() not in {".py", ".js", ".jsx", ".ts", ".tsx", ".vue", ".java"}:
            continue
        text = read_text_safe(path)
        if not text:
            continue
        for pattern in ROUTE_PATTERNS:
            for match in pattern.finditer(text):
                route = match.group(1).strip()
                if not route:
                    continue
                routes.add(route)
                route_evidence.append({"path": rel, "route": route})
    unique_evidence = {(item["path"], item["route"]): item for item in route_evidence}
    return sorted(routes), [unique_evidence[key] for key in sorted(unique_evidence)]


def analyze_project(project_root: str | Path) -> dict[str, Any]:
    root = resolve_existing_root(project_root)
    manifest = collect_source_manifest(root)
    stack, technology_evidence = detect_technology_stack(root, manifest)
    routes, route_evidence = extract_routes(root, manifest)
    entry_points = sorted(
        str(item["path"])
        for item in manifest.get("files", [])
        if item.get("category") == "entry"
    )
    detection_mode = "recognized" if stack else "generic"
    status = "PASS" if stack and manifest.get("files") else "CAUTION"
    findings: list[dict[str, Any]] = []
    if not stack:
        findings.append(
            make_finding(
                "UNKNOWN_TECHNOLOGY_STACK",
                "CAUTION",
                ".",
                "No supported technology markers were found; generic file evidence was retained.",
            )
        )
    package = load_package_json(root)
    version_candidate = package.get("version") if isinstance(package.get("version"), str) else None
    result = make_result(
        "analyze_project",
        status,
        {
            "source_files": len(manifest.get("files", [])),
            "total_source_lines": manifest.get("summary", {}).get("total_source_lines", 0),
            "technologies": len(stack),
        },
        schema_version=1,
        project_root=str(root),
        detection_mode=detection_mode,
        project_layout=detect_layout(root),
        technology_stack=stack,
        technology_evidence=technology_evidence,
        entry_points=entry_points,
        routes=routes,
        api_endpoints=[route for route in routes if route.startswith("/")],
        route_evidence=route_evidence,
        version_candidate=version_candidate,
        source_summary=manifest.get("summary", {}),
        source_languages=manifest.get("by_language", {}),
        business_inference_performed=False,
        prohibited_inferences=["industry", "target_users", "core_value", "business_features"],
    )
    result["findings"] = findings
    return result


def validate_runtime_evidence(root: Path, payload: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        return [], [make_finding("RUNTIME_EVIDENCE_INVALID", "BLOCK", ".", "Runtime evidence must be a schema_version 1 object.")]
    checks = payload.get("checks")
    if not isinstance(checks, list) or not checks or any(not isinstance(item, dict) for item in checks):
        return [], [make_finding("RUNTIME_EVIDENCE_INVALID", "BLOCK", "checks", "Runtime checks must be a non-empty array of objects.")]
    observed_kinds: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(checks):
        prefix = f"checks[{index}]"
        kind = item.get("kind")
        if kind not in {"startup", "core-flow", "test"}:
            findings.append(make_finding("RUNTIME_EVIDENCE_INVALID", "BLOCK", prefix, "Check kind must be startup, core-flow or test."))
            continue
        observed_kinds.add(kind)
        command = item.get("command")
        passed = item.get("passed")
        exit_code = item.get("exit_code")
        evidence_paths = item.get("evidence_paths")
        evidence_hashes = item.get("evidence_sha256")
        cwd = item.get("cwd")
        started_at = item.get("started_at")
        finished_at = item.get("finished_at")
        if not isinstance(command, str) or not command.strip() or not isinstance(passed, bool):
            findings.append(make_finding("RUNTIME_EVIDENCE_INVALID", "BLOCK", prefix, "Check command and passed flag are required."))
            continue
        safe_command = command.strip()
        if RUNTIME_SENSITIVE_PATTERN.search(safe_command):
            findings.append(make_finding("SENSITIVE_DATA_IN_RUNTIME_EVIDENCE", "BLOCK", prefix, "Runtime command contains a sensitive-value pattern and was redacted."))
            safe_command = "[redacted]"
        if not isinstance(exit_code, int) or isinstance(exit_code, bool):
            findings.append(make_finding("RUNTIME_EVIDENCE_INVALID", "BLOCK", prefix, "exit_code must be an integer."))
            continue
        if not isinstance(cwd, str) or not cwd.strip():
            findings.append(make_finding("RUNTIME_EVIDENCE_INVALID", "BLOCK", prefix, "cwd is required."))
            continue
        try:
            cwd_path = ensure_within_root(root, root / cwd)
        except ValueError as exc:
            findings.append(make_finding("RUNTIME_EVIDENCE_OUTSIDE_PROJECT", "BLOCK", prefix, str(exc)))
            continue
        if not cwd_path.is_dir():
            findings.append(make_finding("RUNTIME_EVIDENCE_INVALID", "BLOCK", prefix, "cwd must be an existing project directory."))
            continue
        try:
            started = datetime.fromisoformat(str(started_at).replace("Z", "+00:00"))
            finished = datetime.fromisoformat(str(finished_at).replace("Z", "+00:00"))
            if finished < started:
                raise ValueError("finished before started")
        except (TypeError, ValueError):
            findings.append(make_finding("RUNTIME_EVIDENCE_INVALID", "BLOCK", prefix, "started_at and finished_at must be ordered ISO-8601 timestamps."))
            continue
        if not isinstance(evidence_paths, list) or not evidence_paths or any(not isinstance(path, str) or not path.strip() for path in evidence_paths):
            findings.append(make_finding("RUNTIME_EVIDENCE_INVALID", "BLOCK", prefix, "Each check requires evidence_paths."))
            continue
        if not isinstance(evidence_hashes, dict):
            findings.append(make_finding("RUNTIME_EVIDENCE_INVALID", "BLOCK", prefix, "evidence_sha256 must map each evidence path to its SHA-256."))
            continue
        resolved_evidence: list[str] = []
        for raw_path in evidence_paths:
            try:
                evidence_path = ensure_within_root(root, root / raw_path)
            except ValueError as exc:
                findings.append(make_finding("RUNTIME_EVIDENCE_OUTSIDE_PROJECT", "BLOCK", raw_path, str(exc)))
                continue
            if not evidence_path.is_file() or evidence_path.stat().st_size == 0:
                findings.append(make_finding("RUNTIME_EVIDENCE_FILE_MISSING", "BLOCK", raw_path, "Runtime evidence file is missing or empty."))
                continue
            evidence_text = read_text_safe(evidence_path)
            if evidence_text and RUNTIME_SENSITIVE_PATTERN.search(evidence_text):
                findings.append(make_finding("SENSITIVE_DATA_IN_RUNTIME_EVIDENCE", "BLOCK", raw_path, "Runtime evidence file contains a sensitive-value pattern."))
                continue
            recorded_hash = evidence_hashes.get(raw_path)
            if not isinstance(recorded_hash, str) or sha256_file(evidence_path).lower() != recorded_hash.lower():
                findings.append(make_finding("RUNTIME_EVIDENCE_HASH_MISMATCH", "BLOCK", raw_path, "Runtime evidence hash does not match the current file."))
                continue
            resolved_evidence.append(relative_posix(evidence_path, root))
        if not passed or exit_code != 0:
            findings.append(make_finding("RUNTIME_CHECK_FAILED", "BLOCK", prefix, "A recorded runtime check did not pass."))
        normalized.append(
            {
                "kind": kind,
                "command": safe_command,
                "cwd": relative_posix(cwd_path, root) or ".",
                "started_at": started_at,
                "finished_at": finished_at,
                "passed": passed,
                "exit_code": exit_code,
                "evidence_paths": resolved_evidence,
                "evidence_sha256": {path: evidence_hashes[path] for path in resolved_evidence if path in evidence_hashes},
            }
        )
    for required_kind in ("startup", "core-flow", "test"):
        if required_kind not in observed_kinds:
            findings.append(make_finding("RUNTIME_EVIDENCE_INCOMPLETE", "BLOCK", required_kind, "Startup and core-flow evidence are both required."))
    return normalized, findings


def assess_readiness(root: Path, analysis: dict[str, Any], runtime_evidence: Any | None) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    if int(analysis.get("summary", {}).get("source_files", 0)) <= 0:
        findings.append(make_finding("READINESS_SOURCE_MISSING", "BLOCK", ".", "No real source files were found."))
    if not analysis.get("entry_points"):
        findings.append(make_finding("READINESS_ENTRYPOINT_MISSING", "BLOCK", ".", "No runnable entry point was identified."))
    if runtime_evidence is None:
        normalized_checks: list[dict[str, Any]] = []
        findings.append(make_finding("RUNTIME_EVIDENCE_MISSING", "BLOCK", ".", "Real startup and core-flow evidence is required."))
    else:
        normalized_checks, runtime_findings = validate_runtime_evidence(root, runtime_evidence)
        findings.extend(runtime_findings)
        identity = runtime_evidence.get("software_identity", {}) if isinstance(runtime_evidence, dict) else {}
        if (
            not isinstance(identity, dict)
            or not isinstance(identity.get("software_name"), str)
            or not identity.get("software_name", "").strip()
            or not isinstance(identity.get("version"), str)
            or not identity.get("version", "").strip()
            or identity.get("user_confirmed") is not True
        ):
            findings.append(make_finding("SOFTWARE_IDENTITY_UNCONFIRMED", "CAUTION", "software_identity", "Software name and version still require user confirmation."))
    readme = root / "README.md"
    if not readme.is_file() or readme.stat().st_size == 0:
        findings.append(make_finding("README_EVIDENCE_MISSING", "CAUTION", "README.md", "Project usage documentation is missing."))
    if not any((root / name).is_file() for name in ("LICENSE", "LICENSE.txt", "LICENSE.md", "NOTICE", "THIRD_PARTY_NOTICES")):
        findings.append(make_finding("LICENSE_EVIDENCE_MISSING", "CAUTION", ".", "License or third-party notice evidence is missing."))
    test_files = [path for path in root.rglob("test_*.py") if path.is_file()]
    test_files.extend(path for path in root.rglob("*.test.*") if path.is_file())
    if not test_files:
        findings.append(make_finding("TEST_EVIDENCE_MISSING", "CAUTION", ".", "No automated test source was found."))
    errors = sum(item["severity"] in {"BLOCK", "ERROR"} for item in findings)
    warnings = sum(item["severity"] == "CAUTION" for item in findings)
    readiness_status = "BLOCK" if errors else ("CONDITIONAL" if warnings else "READY")
    return {
        "schema_version": 1,
        "tool": "assess_readiness",
        "status": readiness_status,
        "generated_at": utc_now(),
        "project_root": str(root),
        "summary": {"errors": errors, "warnings": warnings, "runtime_checks": len(normalized_checks)},
        "runtime_checks": normalized_checks,
        "formal_generation_authorized": False,
        "findings": findings,
    }


def readiness_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 软件著作权项目准备度报告",
        "",
        f"status: {payload['status']}",
        "formal_generation_authorized: false",
        "",
        "## Findings",
        "",
    ]
    if not payload.get("findings"):
        lines.append("- None")
    else:
        for item in payload["findings"]:
            lines.append(f"- [{item['severity']}] `{item['rule_id']}` `{item['path']}`：{item['message']}")
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = JsonArgumentParser(description="Identify languages, frameworks, entry points and routes.")
    parser.add_argument("project_root")
    parser.add_argument("--output", type=Path, help="Optional JSON output path within the project root")
    parser.add_argument("--readiness", action="store_true", help="Write Mode C readiness reports to the standard material report directory")
    parser.add_argument("--runtime-evidence", type=Path, help="JSON record of already executed startup/core-flow/test checks")
    parser.add_argument("--readiness-json", type=Path, help="Custom Mode C readiness JSON path within the project")
    parser.add_argument("--readiness-report", type=Path, help="Custom Mode C readiness Markdown path within the project")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        root = resolve_existing_root(args.project_root)
        result = analyze_project(root)
        outputs: list[str] = []
        if args.output:
            output = ensure_within_root(root, args.output)
            write_json(output, result)
            outputs.append(relative_posix(output, root))
        readiness_requested = args.readiness or args.readiness_json is not None or args.readiness_report is not None
        if args.runtime_evidence and not readiness_requested:
            raise ValueError("--runtime-evidence requires --readiness or a readiness output path")
        if readiness_requested:
            runtime_payload = None
            if args.runtime_evidence:
                runtime_path = ensure_within_root(root, args.runtime_evidence)
                runtime_payload = load_json(runtime_path)
            readiness = assess_readiness(root, result, runtime_payload)
            json_path = ensure_within_root(
                root,
                args.readiness_json or (root / "软件著作权申请资料" / "04-校验报告" / "readiness-report.json"),
            )
            report_path = ensure_within_root(
                root,
                args.readiness_report or (root / "软件著作权申请资料" / "04-校验报告" / "readiness-report.md"),
            )
            write_json(json_path, readiness)
            atomic_write_text(report_path, readiness_markdown(readiness))
            outputs.extend([relative_posix(json_path, root), relative_posix(report_path, root)])
            result["readiness"] = readiness
            result["status"] = {"READY": "PASS", "CONDITIONAL": "CAUTION", "BLOCK": "BLOCK"}[readiness["status"]]
        result["outputs"] = sorted(set(outputs))
        return emit_json(result)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, json.JSONDecodeError) as exc:
        result = make_result("analyze_project", "ERROR", "Project analysis failed")
        result["findings"] = [make_finding("PROJECT_ANALYSIS_ERROR", "ERROR", ".", str(exc))]
        return emit_json(result)


if __name__ == "__main__":
    raise SystemExit(main())
