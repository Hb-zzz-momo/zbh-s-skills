#!/usr/bin/env python3
"""Check local capabilities and optionally initialize a resumable material tree."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from collect_source_manifest import (
    JsonArgumentParser,
    atomic_write_bytes,
    atomic_write_text,
    emit_json,
    ensure_within_root,
    make_finding,
    make_result,
    relative_posix,
    resolve_existing_root,
    utc_now,
    load_json,
    write_json,
)


WORKFLOW_STAGES = (
    "environment",
    "project",
    "readiness",
    "business",
    "application-fields",
    "code-selection",
    "screenshot-method",
    "markdown-draft",
    "formal-generation",
    "render-validation",
    "final-review",
)

WORKFLOW_CONFIRMATIONS = (
    "project",
    "business",
    "application_fields",
    "code_selection",
    "screenshot_method",
    "markdown_bundle",
)

WORKFLOW_REQUIRED_TOP_LEVEL_KEYS = (
    "schema_version",
    "mode",
    "project_root",
    "current_stage",
    "stages",
    "confirmations",
    "screenshot_method",
    "formal_generation_authorized",
    "updated_at",
)

OUTPUT_DIRECTORIES = (
    "00-项目证据",
    "01-草稿",
    "02-截图",
    "02-截图/images",
    "03-正式资料",
    "04-校验报告",
)

STAGE_ARTIFACT_PATTERNS = {
    "environment": ("00-项目证据/environment-check.json",),
    "project": (
        "00-项目证据/project-analysis.json",
        "00-项目证据/source-manifest.json",
        "00-项目证据/source-line-count.json",
    ),
    "readiness": ("04-校验报告/readiness-report.json", "04-校验报告/readiness-report.md"),
    "business": ("01-草稿/业务理解.json", "01-草稿/业务理解.md", "00-项目证据/source-evidence-map.json"),
    "application-fields": ("01-草稿/申请表信息.json", "01-草稿/申请表信息.md"),
    "code-selection": ("01-草稿/代码文件选择.json", "01-草稿/代码文件候选清单.md"),
    "screenshot-method": ("02-截图/screenshot-plan.md", "02-截图/images/*"),
    "markdown-draft": ("01-草稿/操作手册.md", "01-草稿/草稿自检记录.md"),
    "formal-generation": ("03-正式资料/*.docx", "03-正式资料/*.txt"),
    "render-validation": (
        "04-校验报告/render-report.md",
        "04-校验报告/consistency-report.md",
        "04-校验报告/provenance-report.md",
    ),
    "final-review": ("04-校验报告/final-checklist.*", "04-校验报告/output-manifest.json"),
}


def module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def validate_workflow_state(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("workflow state must contain a JSON object")
    missing_top_level = [key for key in WORKFLOW_REQUIRED_TOP_LEVEL_KEYS if key not in payload]
    if missing_top_level:
        raise ValueError(f"workflow state is missing required top-level keys: {', '.join(missing_top_level)}")
    if isinstance(payload.get("schema_version"), bool) or payload.get("schema_version") != 1:
        raise ValueError("workflow state.schema_version must equal 1")
    mode = payload.get("mode")
    if mode is not None and mode not in {"A", "B", "C", "D"}:
        raise ValueError("workflow state.mode must be A, B, C, D or null")
    stages = payload.get("stages")
    if not isinstance(stages, dict):
        raise ValueError("workflow state.stages must be an object")
    expected_stages = set(WORKFLOW_STAGES)
    actual_stages = set(stages)
    if actual_stages != expected_stages:
        missing = sorted(expected_stages - actual_stages)
        unexpected = sorted(actual_stages - expected_stages)
        details = []
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected: {', '.join(unexpected)}")
        raise ValueError(f"workflow state.stages must contain exactly 11 stages ({'; '.join(details)})")
    for name in WORKFLOW_STAGES:
        stage = stages[name]
        stage_path = f"workflow state.stages.{name}"
        if not isinstance(stage, dict):
            raise ValueError(f"{stage_path} must be an object")
        status = stage.get("status")
        if status not in {"pending", "pass", "caution", "block"}:
            raise ValueError(f"{stage_path}.status is invalid")
        evidence = stage.get("evidence")
        if not isinstance(evidence, list) or not all(isinstance(item, str) for item in evidence):
            raise ValueError(f"{stage_path}.evidence must be an array of strings")
        if not isinstance(stage.get("confirmed_by_user"), bool):
            raise ValueError(f"{stage_path}.confirmed_by_user must be a boolean")
    first_incomplete = next((name for name in WORKFLOW_STAGES if stages[name]["status"] != "pass"), "final-review")
    if payload.get("current_stage") != first_incomplete:
        raise ValueError("workflow state.current_stage must equal the first incomplete stage")
    incomplete_seen = False
    for name in WORKFLOW_STAGES:
        if stages[name]["status"] != "pass":
            incomplete_seen = True
        elif incomplete_seen:
            raise ValueError("workflow state stage order cannot contain pass after an incomplete stage")
    confirmations = payload.get("confirmations")
    if not isinstance(confirmations, dict):
        raise ValueError("workflow state.confirmations must be an object")
    expected_confirmations = set(WORKFLOW_CONFIRMATIONS)
    actual_confirmations = set(confirmations)
    if actual_confirmations != expected_confirmations:
        missing = sorted(expected_confirmations - actual_confirmations)
        unexpected = sorted(actual_confirmations - expected_confirmations)
        details = []
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected: {', '.join(unexpected)}")
        raise ValueError(f"workflow state.confirmations must contain exactly 6 keys ({'; '.join(details)})")
    if not all(isinstance(confirmations[key], bool) for key in WORKFLOW_CONFIRMATIONS):
        raise ValueError("workflow state.confirmations values must be booleans")
    project_root = payload.get("project_root")
    if not isinstance(project_root, str) or not project_root.strip():
        raise ValueError("workflow state.project_root must be a non-empty string")
    current_stage = payload.get("current_stage")
    if not isinstance(current_stage, str) or current_stage not in WORKFLOW_STAGES:
        raise ValueError("workflow state.current_stage must name one of the 11 workflow stages")
    screenshot_method = payload.get("screenshot_method")
    if screenshot_method not in {None, "browser", "desktop", "user", "skip"}:
        raise ValueError("workflow state.screenshot_method is invalid")
    if not isinstance(payload.get("formal_generation_authorized"), bool):
        raise ValueError("workflow state.formal_generation_authorized must be a boolean")
    updated_at = payload.get("updated_at")
    if not isinstance(updated_at, str) or not updated_at.strip():
        raise ValueError("workflow state.updated_at must be a non-empty ISO-8601 string")
    try:
        datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("workflow state.updated_at must be a valid ISO-8601 string") from exc
    return payload


def artifact_is_readable(path: Path) -> bool:
    try:
        if not path.is_file() or path.stat().st_size == 0:
            return False
        if path.suffix.lower() == ".json":
            load_json(path)
        return True
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False


def discover_recovery_evidence(material_root: Path) -> dict[str, list[str]]:
    evidence: dict[str, list[str]] = {}
    for stage, patterns in STAGE_ARTIFACT_PATTERNS.items():
        matches: set[str] = set()
        for pattern in patterns:
            for path in material_root.glob(pattern):
                if artifact_is_readable(path):
                    # Stage evidence is consumed relative to the material root
                    # by validate_outputs.validate_state.
                    matches.add(relative_posix(path, material_root))
        if matches:
            evidence[stage] = sorted(matches)
    return evidence


def make_workflow_state(
    project_root: Path,
    mode: str | None,
    *,
    recovery_evidence: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    recovered = recovery_evidence or {}
    stages = {
        name: {
            "status": "caution" if name in recovered else "pending",
            "evidence": recovered.get(name, []),
            "confirmed_by_user": False,
        }
        for name in WORKFLOW_STAGES
    }
    # This status is backed by the environment check being executed now; no
    # user fact or downstream completion is inferred during recovery.
    stages["environment"]["status"] = "pass"
    state = {
        "schema_version": 1,
        "mode": mode,
        "project_root": str(project_root),
        "current_stage": next(name for name in WORKFLOW_STAGES if stages[name]["status"] != "pass"),
        "stages": stages,
        "confirmations": {
            "project": False,
            "business": False,
            "application_fields": False,
            "code_selection": False,
            "screenshot_method": False,
            "markdown_bundle": False,
        },
        "screenshot_method": None,
        "formal_generation_authorized": False,
        "updated_at": utc_now(),
    }
    return state


def recover_invalid_workflow_state(
    project_root: Path,
    material_root: Path,
    state_path: Path,
    requested_mode: str | None,
    reason: str,
    parsed_payload: Any = None,
) -> tuple[dict[str, Any], list[str]]:
    original = state_path.read_bytes()
    original_sha256 = hashlib.sha256(original).hexdigest()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    report_dir = material_root / "04-校验报告"
    backup_path = report_dir / f"workflow-state.corrupt-{timestamp}-{original_sha256}.bak"
    atomic_write_bytes(backup_path, original)

    salvaged_mode = parsed_payload.get("mode") if isinstance(parsed_payload, dict) else None
    recovered_mode = requested_mode or (salvaged_mode if salvaged_mode in {"A", "B", "C", "D"} else None)
    recovery_evidence = discover_recovery_evidence(material_root)
    recovered_state = make_workflow_state(project_root, recovered_mode, recovery_evidence=recovery_evidence)
    atomic_write_text(state_path, json.dumps(recovered_state, ensure_ascii=False, indent=2) + "\n")

    report_path = report_dir / "workflow-recovery-report.json"
    report = {
        "schema_version": 1,
        "status": "CAUTION",
        "recovered_at": utc_now(),
        "reason": reason,
        "original_state_path": relative_posix(state_path, project_root),
        "backup_path": relative_posix(backup_path, project_root),
        "original_sha256": original_sha256,
        "recovered_state_path": relative_posix(state_path, project_root),
        "recovered_mode": recovered_mode,
        "stages_marked_caution": sorted(recovery_evidence),
        "recovery_evidence": recovery_evidence,
        "all_user_confirmations_reset": True,
        "formal_generation_authorized": False,
        "next_action": "Review every caution stage and re-confirm all user-controlled facts before continuing.",
    }
    write_json(report_path, report)
    outputs = [
        relative_posix(backup_path, project_root),
        relative_posix(state_path, project_root),
        relative_posix(report_path, project_root),
    ]
    return report, outputs


def initialize_output_tree(
    project_root: Path,
    output_root: Path,
    mode: str | None = None,
) -> tuple[list[str], dict[str, Any] | None]:
    root = resolve_existing_root(project_root)
    target = ensure_within_root(root, output_root)
    target.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    for rel in OUTPUT_DIRECTORIES:
        directory = target / rel
        if not directory.exists():
            directory.mkdir(parents=True)
            created.append(relative_posix(directory, root))
    state_path = target / "workflow-state.json"
    recovery: dict[str, Any] | None = None
    if state_path.exists():
        existing: Any = None
        try:
            existing = load_json(state_path)
            existing = validate_workflow_state(existing)
        except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError) as exc:
            recovery, recovery_outputs = recover_invalid_workflow_state(
                root,
                target,
                state_path,
                mode,
                str(exc),
                existing,
            )
            created.extend(recovery_outputs)
        else:
            existing_mode = existing.get("mode")
            if mode and existing_mode is None:
                existing["mode"] = mode
                existing["updated_at"] = utc_now()
                atomic_write_text(state_path, json.dumps(existing, ensure_ascii=False, indent=2) + "\n")
                created.append(relative_posix(state_path, root))
            elif mode and existing_mode != mode:
                raise ValueError(
                    f"Existing workflow mode {existing_mode!r} conflicts with requested mode {mode!r}; state was preserved"
                )
    else:
        state = make_workflow_state(root, mode)
        atomic_write_text(state_path, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
        created.append(relative_posix(state_path, root))
    return sorted(set(created)), recovery


def check_environment(project_root: str | Path, required: Iterable[str] = ()) -> dict[str, Any]:
    root = resolve_existing_root(project_root)
    requirements = list(required) or ["analysis"]
    python_ok = sys.version_info >= (3, 10)
    readable = os.access(root, os.R_OK)
    writable = os.access(root, os.W_OK)
    docx_module = module_available("docx")
    renderer = shutil.which("soffice") or shutil.which("libreoffice")
    capabilities = {
        "analysis": {
            "available": python_ok and readable and writable,
            "details": f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        },
        "docx-generation": {
            "available": docx_module,
            "details": "python-docx detected" if docx_module else "python-docx not detected; no dependency was installed",
        },
        "render": {
            "available": bool(renderer),
            "details": renderer or "No LibreOffice/soffice CLI detected; external WPS/Word tooling may be used separately",
        },
        "browser-capture": {
            "available": False,
            "details": "Browser capture is an external agent capability and must be verified at the screenshot gate",
        },
    }
    findings: list[dict[str, Any]] = []
    for name in requirements:
        capability = capabilities[name]
        if not capability["available"]:
            findings.append(
                make_finding(
                    "REQUIRED_CAPABILITY_MISSING",
                    "BLOCK",
                    ".",
                    f"Required capability is unavailable: {name}",
                )
            )
    status = "BLOCK" if findings else "PASS"
    result = make_result(
        "check_environment",
        status,
        {"required": requirements, "available": [name for name, item in capabilities.items() if item["available"]]},
        project_root=str(root),
        checks={
            "project_root_exists": True,
            "project_root_readable": readable,
            "project_root_writable": writable,
            "python_utf8_mode": bool(sys.flags.utf8_mode),
        },
        capabilities=capabilities,
        installation_performed=False,
        network_upload_performed=False,
    )
    result["findings"] = findings
    return result


STAGE_CONFIRMATION_KEYS = {
    "project": "project",
    "business": "business",
    "application-fields": "application_fields",
    "code-selection": "code_selection",
    "screenshot-method": "screenshot_method",
    "markdown-draft": "markdown_bundle",
}


def advance_workflow_stage(
    material_root: Path,
    stage_name: str,
    status: str,
    evidence_paths: list[str],
    *,
    confirmed_by_user: bool = False,
    screenshot_method: str | None = None,
    authorize_formal_generation: bool = False,
) -> dict[str, Any]:
    state_path = material_root / "workflow-state.json"
    state = validate_workflow_state(load_json(state_path))
    if stage_name == "final-review":
        raise ValueError("final-review is calculated by validate_outputs.py")
    if state["current_stage"] != stage_name:
        raise ValueError(f"cannot advance {stage_name}; current stage is {state['current_stage']}")
    if status == "pass" and not evidence_paths:
        raise ValueError("a passed stage requires evidence paths")
    allowed_patterns = STAGE_ARTIFACT_PATTERNS[stage_name]
    normalized_evidence: list[str] = []
    for raw_path in evidence_paths:
        normalized = raw_path.replace("\\", "/")
        if not any(PurePosixPath(normalized).match(pattern) for pattern in allowed_patterns):
            raise ValueError(f"evidence path is not valid for {stage_name}: {raw_path}")
        evidence_path = ensure_within_root(material_root, material_root / normalized)
        if not artifact_is_readable(evidence_path):
            raise ValueError(f"stage evidence is missing or unreadable: {raw_path}")
        normalized_evidence.append(normalized)
    confirmation_key = STAGE_CONFIRMATION_KEYS.get(stage_name)
    if status == "pass" and confirmation_key and not confirmed_by_user:
        raise ValueError(f"{stage_name} requires explicit user confirmation")
    if stage_name == "screenshot-method":
        if screenshot_method not in {"browser", "desktop", "user", "skip"}:
            raise ValueError("screenshot-method requires a valid --screenshot-method value")
        state["screenshot_method"] = screenshot_method
    if stage_name == "formal-generation":
        if not authorize_formal_generation or not confirmed_by_user or state["confirmations"]["markdown_bundle"] is not True:
            raise ValueError("formal-generation requires explicit authorization after markdown confirmation")
        state["formal_generation_authorized"] = True
    state["stages"][stage_name] = {
        "status": status,
        "evidence": normalized_evidence,
        "confirmed_by_user": confirmed_by_user,
    }
    if confirmation_key and confirmed_by_user:
        state["confirmations"][confirmation_key] = True
    state["current_stage"] = next(
        (name for name in WORKFLOW_STAGES if state["stages"][name]["status"] != "pass"),
        "final-review",
    )
    state["updated_at"] = utc_now()
    write_json(state_path, state)
    return state


def invalidate_workflow_from(material_root: Path, stage_name: str) -> dict[str, Any]:
    state_path = material_root / "workflow-state.json"
    state = validate_workflow_state(load_json(state_path))
    start = WORKFLOW_STAGES.index(stage_name)
    for name in WORKFLOW_STAGES[start:]:
        state["stages"][name] = {"status": "pending", "evidence": [], "confirmed_by_user": False}
        confirmation_key = STAGE_CONFIRMATION_KEYS.get(name)
        if confirmation_key:
            state["confirmations"][confirmation_key] = False
    if start <= WORKFLOW_STAGES.index("screenshot-method"):
        state["screenshot_method"] = None
    if start <= WORKFLOW_STAGES.index("formal-generation"):
        state["formal_generation_authorized"] = False
    state["current_stage"] = stage_name
    state["updated_at"] = utc_now()
    write_json(state_path, state)
    return state


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = JsonArgumentParser(description="Check software-copyright workflow capabilities without installing anything.")
    parser.add_argument("project_root")
    parser.add_argument("--initialize", action="store_true", help="Create the standard material tree and workflow state")
    parser.add_argument("--material-root", type=Path, help="Custom material root; must remain within the project")
    parser.add_argument("--mode", choices=("A", "B", "C", "D"))
    parser.add_argument(
        "--require",
        action="append",
        choices=("analysis", "docx-generation", "render", "browser-capture"),
        default=[],
    )
    parser.add_argument("--output", type=Path, help="Optional JSON output path within the project root")
    parser.add_argument("--advance-stage", choices=WORKFLOW_STAGES)
    parser.add_argument("--stage-status", choices=("pass", "caution", "block"), default="pass")
    parser.add_argument("--evidence", action="append", default=[])
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--screenshot-method", choices=("browser", "desktop", "user", "skip"))
    parser.add_argument("--authorize-formal-generation", action="store_true")
    parser.add_argument("--invalidate-from", choices=WORKFLOW_STAGES)
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        root = resolve_existing_root(args.project_root)
        if args.initialize and (args.advance_stage or args.invalidate_from):
            raise ValueError("--initialize cannot be combined with stage transition options")
        if args.advance_stage and args.invalidate_from:
            raise ValueError("--advance-stage and --invalidate-from are mutually exclusive")
        result = check_environment(root, args.require)
        outputs: list[str] = []
        material_root: Path | None = None
        if args.advance_stage or args.invalidate_from:
            material_root = ensure_within_root(root, args.material_root or (root / "软件著作权申请资料"))
            if not material_root.is_dir():
                raise ValueError("workflow material root does not exist")
            if args.advance_stage:
                state = advance_workflow_stage(
                    material_root,
                    args.advance_stage,
                    args.stage_status,
                    args.evidence,
                    confirmed_by_user=args.confirm,
                    screenshot_method=args.screenshot_method,
                    authorize_formal_generation=args.authorize_formal_generation,
                )
                result["workflow_transition"] = {"stage": args.advance_stage, "status": args.stage_status}
            else:
                state = invalidate_workflow_from(material_root, args.invalidate_from)
                result["workflow_invalidation"] = {"from_stage": args.invalidate_from}
            result["workflow_state"] = state
        if args.initialize and result["status"] != "BLOCK":
            material_root = ensure_within_root(root, args.material_root or (root / "软件著作权申请资料"))
            initialization_outputs, recovery = initialize_output_tree(root, material_root, args.mode)
            outputs.extend(initialization_outputs)
            if recovery is not None:
                result["status"] = "CAUTION"
                result["summary"]["workflow_state_recovered"] = True
                result["findings"].append(
                    make_finding(
                        "WORKFLOW_STATE_RECOVERED",
                        "CAUTION",
                        recovery["recovered_state_path"],
                        "Invalid workflow state was backed up and conservatively rebuilt; every recovered stage requires review.",
                    )
                )
                result["workflow_recovery"] = recovery
        output_targets: list[Path] = []
        if material_root is not None:
            environment_output = material_root / "00-项目证据" / "environment-check.json"
            if args.initialize:
                output_targets.append(environment_output)
                outputs.append(relative_posix(environment_output, root))
        if args.output:
            output_targets.append(ensure_within_root(root, args.output))
            outputs.append(relative_posix(output_targets[-1], root))
        result["outputs"] = sorted(set(outputs))
        for output in {path.resolve(): path for path in output_targets}.values():
            write_json(output, result)
        if material_root is not None and args.initialize:
            state_path = material_root / "workflow-state.json"
            state = validate_workflow_state(load_json(state_path))
            state["stages"]["environment"]["status"] = "pass"
            state["stages"]["environment"]["evidence"] = ["00-项目证据/environment-check.json"]
            state["current_stage"] = "project"
            state["updated_at"] = utc_now()
            write_json(state_path, state)
        return emit_json(result)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, json.JSONDecodeError) as exc:
        result = make_result("check_environment", "ERROR", "Environment check failed")
        result["findings"] = [make_finding("ENVIRONMENT_CHECK_ERROR", "ERROR", ".", str(exc))]
        return emit_json(result)


if __name__ == "__main__":
    raise SystemExit(main())
