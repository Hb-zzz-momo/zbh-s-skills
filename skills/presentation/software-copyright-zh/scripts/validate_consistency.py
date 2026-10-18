#!/usr/bin/env python3
"""Validate names, versions, feature evidence and source provenance across materials."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree

from collect_source_manifest import (
    JsonArgumentParser,
    atomic_write_text,
    emit_json,
    ensure_within_root,
    is_within_root,
    is_third_party_path,
    load_json,
    make_finding,
    make_result,
    relative_posix,
    resolve_existing_root,
    sha256_file,
    verify_sha256,
    write_json,
)
from validate_application_fields import (
    FIELD_RULES,
    normalized_field_value,
    parse_application_txt,
    validate_application_fields,
)


TEXT_SUFFIXES = {".md", ".txt"}
VERSION_PATTERN = re.compile(r"(?i)\bV?\d+(?:\.\d+){1,3}\b")
SOURCE_SENSITIVE_PATTERN = re.compile(
    r"(?i)\b(?:api[_-]?key|access[_-]?token|password|client[_-]?secret|private[_-]?key)\s*=\s*['\"][^'\"]+['\"]"
    r"|(?<!\d)[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[0-9Xx](?!\d)"
    r"|(?<!\d)1[3-9]\d{9}(?!\d)"
)
SNAPSHOT_DIR_NAMES = {"__snapshots__", "snapshots"}
CODE_LINE_NUMBER_PREFIX = re.compile(r"^\s*\d{1,8}(?:\s*[|:]\s?|\s)")


def extract_docx_text(path: Path) -> str:
    if not zipfile.is_zipfile(path):
        return ""
    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml")
        root = ElementTree.fromstring(xml)
        namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        paragraphs: list[str] = []
        for paragraph in root.iter(namespace + "p"):
            parts: list[str] = []
            for node in paragraph.iter():
                if node.tag == namespace + "t" and node.text:
                    parts.append(node.text)
                elif node.tag == namespace + "tab":
                    parts.append("\t")
                elif node.tag in {namespace + "br", namespace + "cr"}:
                    parts.append("\n")
            paragraphs.append("".join(parts))
        return "\n".join(paragraphs)
    except (KeyError, OSError, ElementTree.ParseError, zipfile.BadZipFile):
        return ""


def read_material_text(path: Path) -> str:
    if path.suffix.lower() in TEXT_SUFFIXES:
        try:
            return path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError):
            return ""
    if path.suffix.lower() == ".docx":
        return extract_docx_text(path)
    return ""


def read_source_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return ""


def selected_content_sha256(path: Path, start_line: int | None, end_line: int | None) -> str:
    if start_line is None and end_line is None:
        return sha256_file(path)
    lines = path.read_bytes().splitlines(keepends=True)
    selected = b"".join(lines[start_line - 1 : end_line])
    return hashlib.sha256(selected).hexdigest()


def normalized_code_document_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        if not raw_line.strip():
            continue
        lines.append(CODE_LINE_NUMBER_PREFIX.sub("", raw_line, count=1).rstrip())
    return lines


def count_contiguous_sequences(document_lines: list[str], source_lines: list[str]) -> int:
    if not source_lines or len(source_lines) > len(document_lines):
        return 0
    width = len(source_lines)
    return sum(document_lines[index : index + width] == source_lines for index in range(len(document_lines) - width + 1))


def application_value(application: dict[str, Any], key: str) -> Any:
    fields = application.get("fields", {})
    if not isinstance(fields, dict):
        return None
    return normalized_field_value(fields.get(key))


def material_documents(materials_root: Path) -> list[Path]:
    paths: list[Path] = []
    manual = materials_root / "01-草稿" / "操作手册.md"
    if manual.is_file():
        paths.append(manual)
    formal = materials_root / "03-正式资料"
    if formal.is_dir():
        paths.extend(
            path
            for path in formal.rglob("*")
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES | {".docx"}
        )
    return sorted(set(paths), key=lambda path: path.as_posix().lower())


def selected_items(selection: dict[str, Any]) -> list[dict[str, Any]]:
    values = selection.get("candidates")
    if not isinstance(values, list):
        values = selection.get("files", [])
    return [item for item in values if isinstance(item, dict) and item.get("selected") is True]


def require_object_list(payload: dict[str, Any], key: str, *, alternate: str | None = None) -> list[dict[str, Any]]:
    value = payload.get(key)
    if value is None and alternate:
        value = payload.get(alternate, [])
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"{key} must be an array of objects")
    return value


def validate_evidence_map_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("schema_version") != 1:
        raise ValueError("source evidence map schema_version must equal 1")
    features = require_object_list(payload, "features")
    seen_ids: set[str] = set()
    for index, feature in enumerate(features):
        prefix = f"features[{index}]"
        for key in ("feature_id", "feature_name", "description"):
            if not isinstance(feature.get(key), str) or not feature[key].strip():
                raise ValueError(f"source evidence map {prefix}.{key} must be a non-empty string")
        feature_id = feature["feature_id"].strip()
        if feature_id in seen_ids:
            raise ValueError(f"source evidence map contains duplicate feature_id: {feature_id}")
        seen_ids.add(feature_id)
        for key in ("evidence_files", "routes", "api_endpoints", "screenshots"):
            value = feature.get(key)
            if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
                raise ValueError(f"source evidence map {prefix}.{key} must be an array of non-empty strings")
        if feature.get("confidence") not in {"confirmed", "partial", "unsupported"}:
            raise ValueError(f"source evidence map {prefix}.confidence is invalid")
    return features


def markdown_report(title: str, result: dict[str, Any]) -> str:
    lines = [f"# {title}", "", f"status: {result['status']}", "", "## Findings", ""]
    if not result.get("findings"):
        lines.append("- None")
    else:
        for item in result["findings"]:
            lines.append(
                f"- [{item['severity']}] `{item['rule_id']}` `{item['path']}`：{item['message']}"
            )
    lines.append("")
    return "\n".join(lines)


def provenance_markdown(result: dict[str, Any]) -> str:
    lines = ["# 源码来源校验报告", "", f"status: {result['status']}", "", "## Provenance", ""]
    lines.extend(
        [
            "| path | recorded_sha256 | current_sha256 | selected_content_sha256 | matches |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for item in result.get("provenance", []):
        lines.append(
            "| {path} | `{recorded}` | `{current}` | `{selected}` | {matches} |".format(
                path=str(item.get("path", "")).replace("|", "\\|"),
                recorded=item.get("recorded_sha256", ""),
                current=item.get("current_sha256", ""),
                selected=item.get("selected_content_sha256", ""),
                matches="yes" if item.get("matches") else "no",
            )
        )
    lines.extend(["", "## Findings", ""])
    if not result.get("findings"):
        lines.append("- None")
    else:
        for item in result["findings"]:
            lines.append(f"- [{item['severity']}] `{item['rule_id']}` `{item['path']}`：{item['message']}")
    lines.append("")
    return "\n".join(lines)


def validate_consistency(
    application_path: Path,
    materials_root: Path,
    source_manifest_path: Path,
    selection_path: Path,
    evidence_map_path: Path,
    project_root: Path | None = None,
) -> dict[str, Any]:
    materials = materials_root.resolve()
    if not materials.is_dir():
        raise NotADirectoryError(f"Materials root does not exist: {materials}")
    for path in (application_path, source_manifest_path, selection_path, evidence_map_path):
        ensure_within_root(materials, path)
        if not path.is_file():
            raise FileNotFoundError(f"Required input does not exist: {path}")
    application = load_json(application_path)
    manifest = load_json(source_manifest_path)
    selection = load_json(selection_path)
    evidence_map = load_json(evidence_map_path)
    if not all(isinstance(item, dict) for item in (application, manifest, selection, evidence_map)):
        raise ValueError("All consistency inputs must be JSON objects")
    if not isinstance(application.get("fields"), dict):
        raise ValueError("application fields must be an object")
    if manifest.get("schema_version") != 1:
        raise ValueError("source manifest schema_version must equal 1")
    if selection.get("schema_version") != 1:
        raise ValueError("code selection schema_version must equal 1")
    manifest_files = require_object_list(manifest, "files")
    selection_values = require_object_list(selection, "candidates", alternate="files")
    features = validate_evidence_map_payload(evidence_map)
    if project_root is None:
        manifest_root = manifest.get("project_root")
        if not manifest_root:
            raise ValueError("project_root is required when the manifest does not record it")
        project = resolve_existing_root(manifest_root)
    else:
        project = resolve_existing_root(project_root)
    if not is_within_root(project, materials):
        raise ValueError("Materials root must remain inside the validated project root")

    findings: list[dict[str, Any]] = []
    field_report = validate_application_fields(application, require_confirmed=False, snapshot_root=project)
    findings.extend(field_report.get("findings", []))
    formal_application_txt = materials / "03-正式资料" / "申请表信息.txt"
    if formal_application_txt.is_file():
        try:
            formal_values = parse_application_txt(formal_application_txt.read_text(encoding="utf-8-sig"))
            for key in FIELD_RULES:
                expected_value = normalized_field_value(application["fields"].get(key), allow_suggested=False)
                if formal_values[key] != expected_value:
                    findings.append(
                        make_finding(
                            "APPLICATION_TXT_FIELD_MISMATCH",
                            "BLOCK",
                            key,
                            "Formal application TXT differs from the confirmed application JSON.",
                        )
                    )
        except (OSError, UnicodeError, ValueError) as exc:
            findings.append(make_finding("APPLICATION_TXT_INVALID", "BLOCK", "03-正式资料/申请表信息.txt", str(exc)))
    expected_name = str(application_value(application, "software_full_name") or "").strip()
    expected_version = str(application_value(application, "version") or "").strip()
    documents = material_documents(materials)
    for path in documents:
        text = read_material_text(path)
        rel = relative_posix(path, materials)
        if not text:
            findings.append(make_finding("MATERIAL_TEXT_UNREADABLE", "CAUTION", rel, "Material text could not be inspected."))
            continue
        if expected_name and expected_name not in text:
            findings.append(
                make_finding("SOFTWARE_NAME_MISMATCH", "BLOCK", rel, "The expected software full name is absent from the material.")
            )
        if expected_version and expected_version not in text:
            findings.append(
                make_finding("VERSION_MISMATCH", "BLOCK", rel, "The expected version is absent from the material.")
            )
        filename_versions = VERSION_PATTERN.findall(path.stem)
        if filename_versions and expected_version and all(value.lower() != expected_version.lower() for value in filename_versions):
            findings.append(
                make_finding("FILENAME_VERSION_MISMATCH", "BLOCK", rel, "A version in the filename differs from the application version.")
            )
        if path.suffix.lower() == ".docx" and expected_name and expected_name not in path.name:
            findings.append(
                make_finding("FILENAME_SOFTWARE_NAME_MISMATCH", "BLOCK", rel, "Formal DOCX filename lacks the confirmed software full name.")
            )

    if not documents:
        findings.append(make_finding("MATERIAL_DOCUMENTS_MISSING", "CAUTION", ".", "No manual or formal documents were available for consistency checks."))

    manifest_entries = {
        str(item.get("path", "")): item
        for item in manifest_files
        if item.get("path")
    }
    selected = [item for item in selection_values if item.get("selected") is True]
    if selection.get("user_confirmed") is not True:
        findings.append(make_finding("CODE_SELECTION_NOT_CONFIRMED", "BLOCK", "01-草稿/代码文件选择.json", "Code selection lacks user confirmation."))
    if not selected:
        findings.append(make_finding("CODE_SELECTION_EMPTY", "BLOCK", "01-草稿/代码文件选择.json", "No real source file or line range was selected."))

    manifest_total_lines = 0
    for item in manifest_files:
        value = item.get("line_count")
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError("manifest line_count values must be non-negative integers")
        manifest_total_lines += value
    application_total_lines = application_value(application, "source_line_count")
    if isinstance(application_total_lines, int) and not isinstance(application_total_lines, bool):
        if application_total_lines != manifest_total_lines:
            findings.append(
                make_finding(
                    "SOURCE_LINE_COUNT_MISMATCH",
                    "BLOCK",
                    "source_line_count",
                    "Application source line count differs from the current source manifest total.",
                )
            )
    seen: set[str] = set()
    seen_content: dict[str, str] = {}
    provenance: list[dict[str, Any]] = []
    for item in selected:
        rel = str(item.get("path", ""))
        if item.get("user_confirmed") is not True:
            findings.append(make_finding("CODE_ITEM_NOT_CONFIRMED", "BLOCK", rel, "Each selected source item requires explicit user confirmation."))
        if rel in seen:
            findings.append(make_finding("DUPLICATE_SOURCE_SELECTION", "BLOCK", rel, "The same source path was selected more than once."))
        seen.add(rel)
        if item.get("is_third_party") is True:
            findings.append(make_finding("THIRD_PARTY_SOURCE_SELECTED", "BLOCK", rel, "The confirmed selection marks this source as third-party."))
            continue
        if is_third_party_path(rel, project):
            findings.append(make_finding("THIRD_PARTY_SOURCE_SELECTED", "BLOCK", rel, "A dependency or third-party path was selected."))
            continue
        if {part.lower() for part in Path(rel).parts} & SNAPSHOT_DIR_NAMES:
            findings.append(make_finding("TEST_SNAPSHOT_SOURCE_SELECTED", "BLOCK", rel, "A test snapshot was selected as code material."))
            continue
        try:
            path = ensure_within_root(project, project / rel)
        except ValueError as exc:
            findings.append(make_finding("SOURCE_PATH_OUTSIDE_PROJECT", "BLOCK", rel, str(exc)))
            continue
        manifest_item = manifest_entries.get(rel)
        if manifest_item is None:
            findings.append(make_finding("SOURCE_NOT_IN_MANIFEST", "BLOCK", rel, "Selected source is absent from source-manifest.json."))
            continue
        if manifest_item.get("is_third_party") is True:
            findings.append(make_finding("THIRD_PARTY_SOURCE_SELECTED", "BLOCK", rel, "The source manifest marks this file as third-party."))
            continue
        if not path.is_file():
            findings.append(make_finding("SOURCE_FILE_MISSING", "BLOCK", rel, "Selected source file no longer exists."))
            continue
        manifest_hash = str(manifest_item.get("sha256") or "")
        confirmed_hash = str(item.get("sha256") or "")
        expected_hash = confirmed_hash
        current_hash = sha256_file(path)
        if not confirmed_hash or confirmed_hash.lower() != manifest_hash.lower():
            findings.append(make_finding("SELECTION_MANIFEST_HASH_MISMATCH", "BLOCK", rel, "The user-confirmed source hash differs from the current manifest."))
        if not expected_hash or not verify_sha256(path, expected_hash):
            findings.append(make_finding("SOURCE_HASH_MISMATCH", "BLOCK", rel, "Selected source differs from the recorded manifest hash."))
        start_line = item.get("start_line")
        end_line = item.get("end_line")
        line_count = int(manifest_item.get("line_count") or 0)
        range_valid = True
        if start_line is not None or end_line is not None:
            if not isinstance(start_line, int) or not isinstance(end_line, int) or start_line < 1 or end_line < start_line or end_line > line_count:
                findings.append(make_finding("SOURCE_LINE_RANGE_INVALID", "BLOCK", rel, "Selected line range is outside the real file."))
                range_valid = False
        if range_valid:
            content_hash = selected_content_sha256(path, start_line, end_line)
            if str(item.get("selected_content_sha256") or "").lower() != content_hash.lower():
                findings.append(make_finding("SELECTED_CONTENT_HASH_MISMATCH", "BLOCK", rel, "The confirmed line range hash differs from the current selected bytes."))
            previous_path = seen_content.get(content_hash)
            if previous_path and previous_path != rel:
                findings.append(make_finding("DUPLICATE_SOURCE_CONTENT", "BLOCK", rel, "Selected source content duplicates another selected file or range."))
            else:
                seen_content[content_hash] = rel
        else:
            content_hash = ""
        provenance.append(
            {
                "path": rel,
                "recorded_sha256": expected_hash,
                "current_sha256": current_hash,
                "selected_content_sha256": content_hash,
                "start_line": start_line,
                "end_line": end_line,
                "matches": expected_hash.lower() == current_hash.lower(),
            }
        )
        source_text = read_source_text(path)
        if SOURCE_SENSITIVE_PATTERN.search(source_text):
            findings.append(make_finding("SENSITIVE_DATA_IN_SELECTED_SOURCE", "BLOCK", rel, "Selected source contains a credential or personal-data pattern."))

    formal_documents = [path for path in documents if "03-正式资料" in path.parts]
    formal_text = "\n".join(read_material_text(path) for path in formal_documents)
    material_text = "\n".join(read_material_text(path) for path in documents)
    selected_paths = {str(item.get("path", "")) for item in selected}
    for feature in features:
        name = str(feature.get("feature_name", "")).strip()
        confidence = feature.get("confidence")
        if name and name in material_text and confidence == "unsupported":
            findings.append(make_finding("UNSUPPORTED_FEATURE_IN_MATERIAL", "BLOCK", name, "An unsupported feature appears in material text."))
        if name and name in material_text and confidence == "partial":
            findings.append(make_finding("PARTIAL_FEATURE_IN_MATERIAL", "CAUTION", name, "A partially supported feature appears in material text."))
        evidence_files = feature.get("evidence_files", [])
        screenshots = feature.get("screenshots", [])
        if not isinstance(evidence_files, list) or any(not isinstance(item, str) for item in evidence_files):
            raise ValueError("feature evidence_files must be an array of strings")
        if not isinstance(screenshots, list) or any(not isinstance(item, str) for item in screenshots):
            raise ValueError("feature screenshots must be an array of strings")
        if confidence == "confirmed" and not evidence_files:
            findings.append(make_finding("CONFIRMED_FEATURE_SOURCE_MISSING", "BLOCK", name or ".", "A confirmed feature has no source evidence."))
        if confidence == "confirmed" and not screenshots:
            findings.append(make_finding("CONFIRMED_FEATURE_SCREENSHOT_MISSING", "BLOCK", name or ".", "A confirmed feature has no screenshot evidence."))
        if confidence == "confirmed" and name and name not in formal_text:
            findings.append(make_finding("CONFIRMED_FEATURE_NOT_IN_FORMAL_MATERIAL", "BLOCK", name, "A confirmed feature is absent from the formal materials."))
        for evidence_path in evidence_files:
            if confidence == "confirmed" and evidence_path not in manifest_entries:
                findings.append(
                    make_finding("FEATURE_EVIDENCE_NOT_IN_MANIFEST", "BLOCK", str(evidence_path), "Confirmed feature evidence is absent from the source manifest.")
                )
            elif confidence == "confirmed" and evidence_path not in selected_paths:
                findings.append(
                    make_finding("FEATURE_EVIDENCE_NOT_SELECTED", "BLOCK", str(evidence_path), "Confirmed feature evidence is not included in the user-confirmed source selection.")
                )
        for screenshot in screenshots:
            if not screenshot.strip():
                findings.append(make_finding("FEATURE_SCREENSHOT_REFERENCE_INVALID", "BLOCK", name or ".", "Screenshot reference is blank."))
                continue
            candidate = materials / screenshot if "/" in screenshot.replace("\\", "/") else materials / "02-截图" / "images" / screenshot
            try:
                screenshot_path = ensure_within_root(materials, candidate)
            except ValueError:
                findings.append(make_finding("FEATURE_SCREENSHOT_OUTSIDE_MATERIAL_ROOT", "BLOCK", screenshot, "Screenshot reference escapes the material root."))
                continue
            if confidence == "confirmed" and not screenshot_path.is_file():
                findings.append(make_finding("CONFIRMED_FEATURE_SCREENSHOT_NOT_FOUND", "BLOCK", screenshot, "Confirmed feature screenshot does not exist."))

    code_documents = [path for path in formal_documents if path.suffix.lower() == ".docx" and "代码" in path.name]
    if selected and not code_documents:
        findings.append(make_finding("FORMAL_CODE_DOCX_MISSING", "BLOCK", "03-正式资料", "Selected source cannot be verified because the formal code DOCX is missing."))
    code_text = "\n".join(read_material_text(path) for path in code_documents)
    code_document_lines = normalized_code_document_lines(code_text)
    for item in selected:
        rel = str(item.get("path", ""))
        manifest_item = manifest_entries.get(rel)
        if manifest_item is None:
            continue
        try:
            source_path = ensure_within_root(project, project / rel)
        except ValueError:
            continue
        if not source_path.is_file():
            continue
        source_lines = read_source_text(source_path).splitlines()
        start_line = item.get("start_line")
        end_line = item.get("end_line")
        if isinstance(start_line, int) and isinstance(end_line, int):
            source_lines = source_lines[start_line - 1 : end_line]
        significant_lines = [line.rstrip() for line in source_lines if line.strip()]
        occurrences = count_contiguous_sequences(code_document_lines, significant_lines)
        if code_documents and significant_lines and occurrences != 1:
            findings.append(
                make_finding(
                    "SELECTED_SOURCE_NOT_IN_CODE_DOCX",
                    "BLOCK",
                    rel,
                    "The formal code DOCX must contain the confirmed non-blank source lines exactly once and in order.",
                )
            )

    errors = sum(item["severity"] in {"BLOCK", "ERROR"} for item in findings)
    warnings = sum(item["severity"] == "CAUTION" for item in findings)
    status = "BLOCK" if errors else ("CAUTION" if warnings else "PASS")
    result = make_result(
        "validate_consistency",
        status,
        {"errors": errors, "warnings": warnings, "documents": len(documents), "selected_sources": len(selected)},
        schema_version=1,
        expected_software_name=expected_name,
        expected_version=expected_version,
        project_root=str(project),
        materials_root=str(materials),
        provenance=provenance,
        sensitive_values_echoed=False,
    )
    result["findings"] = findings
    return result


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = JsonArgumentParser(description="Validate cross-material consistency and source provenance.")
    parser.add_argument("--application", type=Path, required=True)
    parser.add_argument("--materials-root", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--evidence-map", type=Path, required=True)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--provenance-report", type=Path)
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        materials = args.materials_root.expanduser().resolve()
        result = validate_consistency(
            args.application.expanduser().resolve(),
            materials,
            args.source_manifest.expanduser().resolve(),
            args.selection.expanduser().resolve(),
            args.evidence_map.expanduser().resolve(),
            args.project_root.expanduser().resolve() if args.project_root else None,
        )
        outputs: list[str] = []
        if args.output:
            output = ensure_within_root(materials, args.output)
            write_json(output, result)
            outputs.append(relative_posix(output, materials))
        if args.report:
            report = ensure_within_root(materials, args.report)
            atomic_write_text(report, markdown_report("一致性校验报告", result))
            outputs.append(relative_posix(report, materials))
        if args.provenance_report:
            report = ensure_within_root(materials, args.provenance_report)
            atomic_write_text(report, provenance_markdown(result))
            outputs.append(relative_posix(report, materials))
        result["outputs"] = outputs
        return emit_json(result)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        result = make_result("validate_consistency", "ERROR", "Consistency validation failed")
        result["findings"] = [make_finding("CONSISTENCY_VALIDATION_ERROR", "ERROR", ".", str(exc))]
        return emit_json(result)


if __name__ == "__main__":
    raise SystemExit(main())
    try:
        datetime.fromisoformat(str(selection.get("confirmed_at")).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        findings.append(make_finding("CODE_SELECTION_CONFIRMATION_INVALID", "BLOCK", "01-草稿/代码文件选择.json", "Code selection requires an ISO-8601 confirmed_at timestamp."))
