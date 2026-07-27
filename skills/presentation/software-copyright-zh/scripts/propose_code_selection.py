#!/usr/bin/env python3
"""Propose source candidates for human confirmation; never auto-confirm selection."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable

from collect_source_manifest import (
    EXCLUDED_DIR_NAMES,
    JsonArgumentParser,
    collect_source_manifest,
    emit_json,
    ensure_within_root,
    is_generated_or_lock_file,
    is_third_party_path,
    load_json,
    make_finding,
    make_result,
    relative_posix,
    resolve_existing_root,
    utc_now,
    validate_source_manifest_payload,
    write_json,
    atomic_write_text,
)


CATEGORY_PRIORITY = {
    "entry": 0,
    "route": 1,
    "page": 2,
    "component": 3,
    "api": 4,
    "state": 5,
    "service": 6,
    "data": 7,
    "model": 8,
    "algorithm": 9,
    "source": 10,
}

CATEGORY_RESPONSIBILITY = {
    "entry": "应用入口",
    "route": "路由与导航",
    "page": "核心页面",
    "component": "业务组件",
    "api": "接口适配",
    "state": "状态管理",
    "service": "核心业务服务",
    "data": "数据访问或处理",
    "model": "数据模型",
    "algorithm": "核心算法",
    "source": "通用源码",
}

OFFICIAL_GENERAL_LINES_PER_PAGE = 50
SNAPSHOT_DIR_NAMES = {"__snapshots__", "snapshots"}


def load_optional_json(root: Path, path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    resolved = ensure_within_root(root, path)
    payload = load_json(resolved)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object: {resolved}")
    return payload


def evidence_features(evidence_map: dict[str, Any]) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for feature in evidence_map.get("features", []):
        if feature.get("confidence") != "confirmed":
            continue
        name = str(feature.get("feature_name", "")).strip()
        for path in feature.get("evidence_files", []):
            mapping.setdefault(str(path), []).append(name)
    return mapping


def validate_evidence_map_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("source evidence map must contain a JSON object")
    features = payload.get("features", [])
    if not isinstance(features, list):
        raise ValueError("source evidence map.features must be an array")
    for index, feature in enumerate(features):
        item_path = f"source evidence map.features[{index}]"
        if not isinstance(feature, dict):
            raise ValueError(f"{item_path} must be an object")
        name = feature.get("feature_name")
        if name is not None and not isinstance(name, str):
            raise ValueError(f"{item_path}.feature_name must be a string or null")
        confidence = feature.get("confidence")
        if confidence is not None and not isinstance(confidence, str):
            raise ValueError(f"{item_path}.confidence must be a string or null")
        evidence_files = feature.get("evidence_files", [])
        if not isinstance(evidence_files, list) or not all(isinstance(path, str) for path in evidence_files):
            raise ValueError(f"{item_path}.evidence_files must be an array of strings")
    return payload


def build_candidates(
    project_root: str | Path,
    manifest: dict[str, Any],
    evidence_map: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    root = resolve_existing_root(project_root)
    manifest = validate_source_manifest_payload(manifest)
    evidence_map = validate_evidence_map_payload(evidence_map or {})
    features = evidence_features(evidence_map)
    candidates: list[dict[str, Any]] = []
    for item in manifest.get("files", []):
        rel = str(item.get("path", ""))
        category = str(item.get("category") or "source")
        third_party = bool(item.get("is_third_party")) or is_third_party_path(rel, root)
        path_parts = {part.lower() for part in Path(rel).parts}
        snapshot = bool(path_parts & SNAPSHOT_DIR_NAMES)
        generated_or_lock = is_generated_or_lock_file(Path(rel))
        excluded_directory = bool(path_parts & EXCLUDED_DIR_NAMES)
        line_count = int(item.get("line_count") or 0)
        if snapshot:
            recommendation = "excluded"
            exclusion_kind = "test-snapshot"
            reason = "测试快照目录默认排除；只能作为测试证据，不能作为主要源码鉴别材料。"
        elif generated_or_lock:
            recommendation = "excluded"
            exclusion_kind = "generated-or-lock"
            reason = "生成文件、压缩文件或锁文件默认排除。"
        elif third_party or excluded_directory:
            recommendation = "excluded"
            exclusion_kind = "dependency-or-build"
            reason = "第三方、依赖、构建或输出目录，禁止进入源码鉴别材料。"
        elif category in {"entry", "route", "page", "component", "api", "service", "model", "algorithm"}:
            recommendation = "recommended"
            exclusion_kind = None
            reason = f"候选职责为{CATEGORY_RESPONSIBILITY.get(category, category)}；仍需模型阅读和用户确认。"
        else:
            recommendation = "consider"
            exclusion_kind = None
            reason = "可作为补充候选；必须证明与核心业务功能有关。"
        candidates.append(
            {
                "path": rel,
                "language": item.get("language"),
                "line_count": line_count,
                "sha256": item.get("sha256"),
                "category": category,
                "module_responsibility": CATEGORY_RESPONSIBILITY.get(category, "通用源码"),
                "corresponding_features": sorted(features.get(rel, [])),
                "is_third_party": third_party,
                "exclusion_kind": exclusion_kind,
                "recommendation": recommendation,
                "recommendation_reason": reason,
                "estimated_page_contribution": (
                    math.ceil(line_count / OFFICIAL_GENERAL_LINES_PER_PAGE) if line_count else 0
                ),
                "page_estimate_is_physical_render_result": False,
                "selected": False,
                "start_line": None,
                "end_line": None,
                "user_confirmed": False,
                "selected_content_sha256": None,
            }
        )
    candidates.sort(
        key=lambda item: (
            item["recommendation"] == "excluded",
            CATEGORY_PRIORITY.get(str(item["category"]), 99),
            str(item["path"]).lower(),
        )
    )
    return candidates


def proposal_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 代码文件候选清单",
        "",
        "> 本清单只提出候选，不代表用户已确认。预计页数按法规一般规则的每页不少于 50 行做工作流估算，不能替代 DOCX 实际渲染页数。",
        "",
        "| 路径 | 行数 | 模块职责 | 对应功能 | 第三方 | 推荐状态 | 推荐理由 | 预计页数贡献 |",
        "| --- | ---: | --- | --- | --- | --- | --- | ---: |",
    ]
    for item in payload.get("candidates", []):
        features = "、".join(item.get("corresponding_features", [])) or "待模型结合证据填写"
        reason = str(item.get("recommendation_reason", "")).replace("|", "\\|")
        lines.append(
            "| {path} | {line_count} | {responsibility} | {features} | {third_party} | {recommendation} | {reason} | {pages} |".format(
                path=str(item.get("path", "")).replace("|", "\\|"),
                line_count=item.get("line_count", 0),
                responsibility=item.get("module_responsibility", ""),
                features=features.replace("|", "\\|"),
                third_party="是" if item.get("is_third_party") else "否",
                recommendation=item.get("recommendation", ""),
                reason=reason,
                pages=item.get("estimated_page_contribution", 0),
            )
        )
    lines.extend(["", "用户确认前，所有 `selected` 均保持 `false`。", ""])
    return "\n".join(lines)


def propose_code_selection(
    project_root: str | Path,
    manifest: dict[str, Any],
    evidence_map: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = resolve_existing_root(project_root)
    candidates = build_candidates(root, manifest, evidence_map)
    findings = [
        make_finding(
            "CODE_SELECTION_REQUIRES_CONFIRMATION",
            "CAUTION",
            ".",
            "The proposal is not a confirmed code selection.",
        )
    ]
    if not candidates:
        findings.append(make_finding("NO_CODE_CANDIDATES", "CAUTION", ".", "No source candidates were found."))
    result = make_result(
        "propose_code_selection",
        "CAUTION",
        {"candidates": len(candidates), "excluded": sum(item["recommendation"] == "excluded" for item in candidates)},
        schema_version=1,
        generated_at=utc_now(),
        project_root=str(root),
        user_confirmed=False,
        confirmation_status="pending",
        lines_per_page_basis={
            "value": OFFICIAL_GENERAL_LINES_PER_PAGE,
            "kind": "official-general-rule-and-workflow-estimate",
            "source": "https://www.ncac.gov.cn/xxfb/flfg/bmgz/202410/t20241015_869486.html",
            "verified_at": "2026-07-12",
            "physical_render_required": True,
        },
        candidates=candidates,
    )
    result["findings"] = findings
    return result


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = JsonArgumentParser(description="Create a code candidate proposal for user confirmation.")
    parser.add_argument("project_root")
    parser.add_argument("--manifest", type=Path, help="Source manifest; generated if omitted")
    parser.add_argument("--evidence-map", type=Path, help="Optional source evidence map")
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        root = resolve_existing_root(args.project_root)
        manifest = load_optional_json(root, args.manifest) if args.manifest else collect_source_manifest(root)
        evidence_map = load_optional_json(root, args.evidence_map) if args.evidence_map else {}
        json_output = ensure_within_root(root, args.json_output)
        markdown_output = ensure_within_root(root, args.markdown_output)
        if json_output.exists():
            existing = load_json(json_output)
            if isinstance(existing, dict) and existing.get("user_confirmed"):
                result = make_result("propose_code_selection", "BLOCK", "Confirmed selection was not overwritten")
                result["findings"] = [
                    make_finding(
                        "CONFIRMED_SELECTION_EXISTS",
                        "BLOCK",
                        relative_posix(json_output, root),
                        "A confirmed code selection already exists; create a new reviewed version explicitly.",
                    )
                ]
                return emit_json(result)
        result = propose_code_selection(root, manifest, evidence_map)
        write_json(json_output, result)
        atomic_write_text(markdown_output, proposal_markdown(result))
        result["outputs"] = [relative_posix(json_output, root), relative_posix(markdown_output, root)]
        return emit_json(result)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, json.JSONDecodeError) as exc:
        result = make_result("propose_code_selection", "ERROR", "Code selection proposal failed")
        result["findings"] = [make_finding("CODE_SELECTION_ERROR", "ERROR", ".", str(exc))]
        return emit_json(result)


if __name__ == "__main__":
    raise SystemExit(main())
