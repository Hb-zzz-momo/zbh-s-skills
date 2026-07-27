#!/usr/bin/env python3
"""Count all recognized project source lines without applying a 3000-line gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from collect_source_manifest import (
    JsonArgumentParser,
    collect_source_manifest,
    emit_json,
    ensure_within_root,
    load_json,
    make_finding,
    make_result,
    relative_posix,
    resolve_existing_root,
    sha256_file,
    count_text_lines,
    validate_source_manifest_payload,
    write_json,
)


def count_source_lines(project_root: str | Path, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    root = resolve_existing_root(project_root)
    source = manifest if manifest is not None else collect_source_manifest(root)
    source = validate_source_manifest_payload(source)
    entries = source["files"]
    findings: list[dict[str, Any]] = []
    by_language: dict[str, dict[str, int]] = {}
    total_lines = 0
    counted_files = 0
    for item in entries:
        rel = str(item.get("path", ""))
        try:
            path = ensure_within_root(root, root / rel)
            if not path.is_file():
                findings.append(make_finding("SOURCE_FILE_MISSING", "BLOCK", rel, "Manifest source file is missing."))
                continue
            line_count = count_text_lines(path)
            expected_hash = str(item.get("sha256", ""))
            if expected_hash and sha256_file(path).lower() != expected_hash.lower():
                findings.append(
                    make_finding("SOURCE_HASH_MISMATCH", "CAUTION", rel, "Source changed after the manifest was created.")
                )
            language = str(item.get("language") or "Unknown")
            bucket = by_language.setdefault(language, {"files": 0, "lines": 0})
            bucket["files"] += 1
            bucket["lines"] += line_count
            counted_files += 1
            total_lines += line_count
        except (OSError, ValueError) as exc:
            findings.append(make_finding("SOURCE_COUNT_ERROR", "BLOCK", rel or ".", str(exc)))
    if any(item["severity"] == "BLOCK" for item in findings):
        status = "BLOCK"
    elif findings or not counted_files:
        status = "CAUTION"
    else:
        status = "PASS"
    result = make_result(
        "count_source_lines",
        status,
        {"source_files": counted_files, "total_source_lines": total_lines},
        project_root=str(root),
        by_language=dict(sorted(by_language.items())),
        line_count_definition="Physical lines; LF/CRLF/CR supported; comments and blank lines count; trailing newline adds no line.",
        material_page_estimate=None,
        maximum_line_gate_applied=False,
    )
    result["findings"] = findings
    return result


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = JsonArgumentParser(description="Count project source lines by language.")
    parser.add_argument("project_root")
    parser.add_argument("--manifest", type=Path, help="Optional existing source manifest")
    parser.add_argument("--output", type=Path, help="Optional JSON output path within the project root")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        root = resolve_existing_root(args.project_root)
        manifest = None
        if args.manifest:
            manifest_path = ensure_within_root(root, args.manifest)
            manifest = load_json(manifest_path)
        result = count_source_lines(root, manifest)
        if args.output:
            output = ensure_within_root(root, args.output)
            write_json(output, result)
            result["outputs"] = [relative_posix(output, root)]
        return emit_json(result)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, json.JSONDecodeError) as exc:
        result = make_result("count_source_lines", "ERROR", "Source line counting failed")
        result["findings"] = [make_finding("SOURCE_COUNT_ERROR", "ERROR", ".", str(exc))]
        return emit_json(result)


if __name__ == "__main__":
    raise SystemExit(main())
