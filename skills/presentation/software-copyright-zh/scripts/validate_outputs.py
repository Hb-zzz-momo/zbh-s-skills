#!/usr/bin/env python3
"""Validate the final material bundle and generate a reproducible output manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import struct
import subprocess
import zipfile
import zlib
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from xml.etree import ElementTree

from check_environment import STAGE_ARTIFACT_PATTERNS, WORKFLOW_STAGES, validate_workflow_state
from collect_source_manifest import (
    JsonArgumentParser,
    atomic_write_bytes,
    atomic_write_text,
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
from validate_application_fields import validate_application_fields
from validate_consistency import extract_docx_text, validate_consistency, validate_evidence_map_payload


REQUIRED_DIRECTORIES = (
    "00-项目证据",
    "01-草稿",
    "02-截图",
    "02-截图/images",
    "03-正式资料",
    "04-校验报告",
)

REQUIRED_EVIDENCE_FILES = (
    "00-项目证据/environment-check.json",
    "00-项目证据/project-analysis.json",
    "00-项目证据/source-line-count.json",
    "00-项目证据/source-evidence-map.json",
    "00-项目证据/source-manifest.json",
)

REQUIRED_DRAFT_FILES = (
    "01-草稿/业务理解.md",
    "01-草稿/业务理解.json",
    "01-草稿/申请表信息.md",
    "01-草稿/申请表信息.json",
    "01-草稿/代码文件候选清单.md",
    "01-草稿/代码文件选择.json",
    "01-草稿/操作手册.md",
    "01-草稿/草稿自检记录.md",
)

PLACEHOLDER_PATTERN = re.compile(r"待补充|此处略|后续实现|\bTODO\b|\bTBD\b|\[\s*placeholder\s*\]", re.IGNORECASE)
SENSITIVE_PATTERN = re.compile(
    r"(?i)\b(?:api[_-]?key|access[_-]?token|password|client[_-]?secret|private[_-]?key)\s*[:=]"
    r"|(?<!\d)[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[0-9Xx](?!\d)"
    r"|(?<!\d)1[3-9]\d{9}(?!\d)"
)
STATUS_LINE = re.compile(r"(?im)^\s*status\s*:\s*(PASS|CAUTION|BLOCK)\s*$")
VISUAL_LINE = re.compile(r"(?im)^\s*visual_validation\s*:\s*completed\s*$")
REPAIR_LINE = re.compile(r"(?im)^\s*repair_rounds\s*:\s*(\d+)\s*$")
RENDER_RECORD_LINE = re.compile(r"(?im)^\s*render_record\s*:\s*(\{.*\})\s*$")
PDF_PAGE_PATTERN = re.compile(rb"/Type\s*/Page(?!s)\b")
SCREENSHOT_METADATA_LABELS = (
    "截图文件",
    "对应页面",
    "访问路径",
    "前置数据",
    "操作动作",
    "证明的功能",
    "采集方式",
    "采集时间",
    "证据 ID",
    "敏感信息",
    "SHA-256",
)
MIN_SCREENSHOT_WIDTH = 320
MIN_SCREENSHOT_HEIGHT = 200
MANUAL_SELF_CHECK_KEYS = (
    "evidence_mapping",
    "natural_language",
    "no_template_marketing",
    "screenshot_mapping",
    "sensitive_data",
)
MANUAL_TEMPLATE_PATTERN = re.compile(r"进入方式\s*[:：]|页面内容\s*[:：]|操作步骤\s*[:：]|操作结果\s*[:：]")
MANUAL_MARKETING_PATTERN = re.compile(r"赋能|一站式|智能化|高效便捷|显著提升|强大能力")


def read_text_for_scan(path: Path) -> str:
    if path.suffix.lower() in {".md", ".txt", ".log", ".json"}:
        try:
            return path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError):
            return ""
    if path.suffix.lower() == ".docx":
        return extract_docx_text(path)
    return ""


def report_status(path: Path) -> str | None:
    text = read_text_for_scan(path)
    match = STATUS_LINE.search(text)
    return match.group(1).upper() if match else None


def validate_business_understanding_payload(
    payload: Any,
    *,
    known_evidence_ids: set[str] | None = None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("business understanding must be a schema_version 1 object")
    for key in (
        "software_name",
        "product_positioning",
        "industry",
        "application_purpose",
        "main_functions",
        "technical_characteristics",
    ):
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            raise ValueError(f"business understanding {key} must be a non-empty string")
    for key in (
        "target_users",
        "core_value",
        "operation_flows",
        "page_modules",
        "manual_modules",
        "evidence_sources",
        "excluded_features",
    ):
        if not isinstance(payload.get(key), list):
            raise ValueError(f"business understanding {key} must be an array")
    if not isinstance(payload.get("system_requirements"), dict):
        raise ValueError("business understanding system_requirements must be an object")
    features = payload.get("business_features")
    if not isinstance(features, list) or not features or any(not isinstance(item, dict) for item in features):
        raise ValueError("business understanding business_features must be a non-empty array of objects")
    for index, feature in enumerate(features):
        for key in ("feature_name", "description"):
            if not isinstance(feature.get(key), str) or not feature[key].strip():
                raise ValueError(f"business_features[{index}].{key} must be a non-empty string")
        evidence_ids = feature.get("evidence_ids")
        if not isinstance(evidence_ids, list) or not evidence_ids or any(not isinstance(item, str) or not item.strip() for item in evidence_ids):
            raise ValueError(f"business_features[{index}].evidence_ids must be a non-empty string array")
        if feature.get("confidence") not in {"confirmed", "partial", "unsupported"}:
            raise ValueError(f"business_features[{index}].confidence is invalid")
        if known_evidence_ids is not None and any(item not in known_evidence_ids for item in evidence_ids):
            raise ValueError(f"business_features[{index}] references an unknown evidence ID")
    excluded = payload["excluded_features"]
    if any(not isinstance(item, str) or not item.strip() for item in excluded):
        raise ValueError("business understanding excluded_features must contain non-empty strings")
    for index, feature in enumerate(features):
        name = feature["feature_name"]
        if feature["confidence"] == "unsupported" and name not in excluded:
            raise ValueError(f"unsupported business_features[{index}] must appear in excluded_features")
    manual_modules = payload["manual_modules"]
    if not manual_modules or any(not isinstance(item, dict) for item in manual_modules):
        raise ValueError("business understanding manual_modules must be a non-empty array of objects")
    for index, module in enumerate(manual_modules):
        for key in ("title", "purpose", "entry"):
            if not isinstance(module.get(key), str) or not module[key].strip():
                raise ValueError(f"manual_modules[{index}].{key} must be a non-empty string")
        for key in (
            "visible_elements",
            "user_actions",
            "input_or_state_rules",
            "error_feedback",
            "result_feedback",
            "evidence_ids",
            "screenshot_ids",
        ):
            values = module.get(key)
            if not isinstance(values, list) or not values or any(not isinstance(item, str) or not item.strip() for item in values):
                raise ValueError(f"manual_modules[{index}].{key} must be a non-empty string array")
        if known_evidence_ids is not None and any(item not in known_evidence_ids for item in module["evidence_ids"]):
            raise ValueError(f"manual_modules[{index}] references an unknown evidence ID")
    confirmed_at = payload.get("confirmed_at")
    try:
        datetime.fromisoformat(str(confirmed_at).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError("business understanding confirmed_at must be ISO-8601") from exc
    for index, source in enumerate(payload["evidence_sources"]):
        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"evidence_sources[{index}] must be a non-empty project path")
        if project_root is not None:
            source_path = ensure_within_root(project_root, project_root / source)
            if not source_path.is_file():
                raise ValueError(f"evidence_sources[{index}] does not exist in the project")
    if payload.get("user_confirmed") is not True:
        raise ValueError("business understanding lacks user confirmation")
    return payload


def validate_state(material_root: Path, findings: list[dict[str, Any]]) -> dict[str, Any]:
    state_path = material_root / "workflow-state.json"
    if not state_path.is_file():
        findings.append(make_finding("WORKFLOW_STATE_MISSING", "BLOCK", "workflow-state.json", "Workflow state is missing."))
        return {}
    try:
        state = load_json(state_path)
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(make_finding("WORKFLOW_STATE_INVALID", "BLOCK", "workflow-state.json", str(exc)))
        return {}
    if not isinstance(state, dict):
        findings.append(make_finding("WORKFLOW_STATE_INVALID", "BLOCK", "workflow-state.json", "Workflow state must be an object."))
        return {}
    try:
        state = validate_workflow_state(state)
    except (TypeError, ValueError) as exc:
        findings.append(make_finding("WORKFLOW_STATE_INVALID", "BLOCK", "workflow-state.json", str(exc)))
        return {}
    stages = state.get("stages", {})
    if not isinstance(stages, dict):
        findings.append(make_finding("WORKFLOW_STATE_INVALID", "BLOCK", "stages", "Workflow stages must be an object."))
        stages = {}
    for name in WORKFLOW_STAGES:
        stage = stages.get(name, {})
        if not isinstance(stage, dict):
            findings.append(make_finding("WORKFLOW_STATE_INVALID", "BLOCK", name, "Workflow stage must be an object."))
            stage = {}
        stage_status = stage.get("status")
        if name == "final-review":
            continue
        if stage_status != "pass":
            findings.append(make_finding("WORKFLOW_STAGE_NOT_PASSED", "BLOCK", name, "A required workflow stage is not passed."))
            continue
        evidence = stage.get("evidence")
        if not isinstance(evidence, list) or not evidence or any(not isinstance(item, str) or not item.strip() for item in evidence):
            findings.append(make_finding("WORKFLOW_STAGE_EVIDENCE_MISSING", "BLOCK", name, "A passed stage requires one or more evidence paths."))
            continue
        allowed_patterns = STAGE_ARTIFACT_PATTERNS.get(name, ())
        for raw_path in evidence:
            normalized = raw_path.replace("\\", "/")
            if not any(PurePosixPath(normalized).match(pattern) for pattern in allowed_patterns):
                findings.append(
                    make_finding(
                        "WORKFLOW_STAGE_EVIDENCE_MISMATCH",
                        "BLOCK",
                        raw_path,
                        f"Evidence path is not valid for the {name} stage.",
                    )
                )
                continue
            try:
                evidence_path = ensure_within_root(material_root, material_root / normalized)
            except ValueError as exc:
                findings.append(make_finding("WORKFLOW_STAGE_EVIDENCE_INVALID", "BLOCK", name, str(exc)))
                continue
            if not evidence_path.is_file():
                findings.append(make_finding("WORKFLOW_STAGE_EVIDENCE_MISSING", "BLOCK", raw_path, "Recorded stage evidence does not exist."))
    confirmations = state.get("confirmations", {})
    for key in ("project", "business", "application_fields", "code_selection", "screenshot_method", "markdown_bundle"):
        if not isinstance(confirmations, dict) or confirmations.get(key) is not True:
            findings.append(make_finding("USER_CONFIRMATION_MISSING", "BLOCK", key, "A required user confirmation is missing."))
    if state.get("formal_generation_authorized") is not True:
        findings.append(make_finding("FORMAL_GENERATION_NOT_AUTHORIZED", "BLOCK", "workflow-state.json", "Formal generation lacks user authorization."))
    if state.get("screenshot_method") == "skip":
        findings.append(make_finding("SCREENSHOTS_SKIPPED", "BLOCK", "workflow-state.json", "Submission is incomplete because screenshots were skipped."))
    return state


def validate_json_evidence(material_root: Path, project_root: Path, findings: list[dict[str, Any]]) -> None:
    manifest_total_lines: int | None = None
    evidence_features: list[dict[str, Any]] = []
    try:
        analysis = load_json(material_root / "00-项目证据" / "project-analysis.json")
        if not isinstance(analysis, dict) or analysis.get("schema_version") != 1 or analysis.get("status") not in {"PASS", "CAUTION"}:
            findings.append(make_finding("EVIDENCE_JSON_INVALID", "BLOCK", "00-项目证据/project-analysis.json", "Project analysis must be a schema_version 1 PASS/CAUTION object."))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(make_finding("EVIDENCE_JSON_INVALID", "BLOCK", "00-项目证据/project-analysis.json", str(exc)))
    try:
        environment = load_json(material_root / "00-项目证据" / "environment-check.json")
        if not isinstance(environment, dict) or environment.get("status") != "PASS":
            findings.append(make_finding("EVIDENCE_JSON_INVALID", "BLOCK", "00-项目证据/environment-check.json", "Environment evidence must contain PASS status."))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(make_finding("EVIDENCE_JSON_INVALID", "BLOCK", "00-项目证据/environment-check.json", str(exc)))
    try:
        readiness = load_json(material_root / "04-校验报告" / "readiness-report.json")
        if not isinstance(readiness, dict) or readiness.get("schema_version") != 1 or readiness.get("status") != "READY":
            findings.append(make_finding("READINESS_NOT_READY", "BLOCK", "04-校验报告/readiness-report.json", "Final materials require a schema_version 1 READY report."))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(make_finding("READINESS_NOT_READY", "BLOCK", "04-校验报告/readiness-report.json", str(exc)))
    try:
        manifest = load_json(material_root / "00-项目证据" / "source-manifest.json")
        files = manifest.get("files") if isinstance(manifest, dict) else None
        if not isinstance(manifest, dict) or manifest.get("schema_version") != 1 or not isinstance(files, list) or not files or any(not isinstance(item, dict) for item in files):
            findings.append(make_finding("SOURCE_MANIFEST_EMPTY", "BLOCK", "00-项目证据/source-manifest.json", "Source manifest has no real source files."))
        elif all(isinstance(item.get("line_count"), int) and not isinstance(item.get("line_count"), bool) for item in files):
            manifest_total_lines = sum(item["line_count"] for item in files)
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(make_finding("EVIDENCE_JSON_INVALID", "BLOCK", "00-项目证据/source-manifest.json", str(exc)))
    try:
        line_report = load_json(material_root / "00-项目证据" / "source-line-count.json")
        line_summary = line_report.get("summary") if isinstance(line_report, dict) else None
        if (
            not isinstance(line_report, dict)
            or line_report.get("status") != "PASS"
            or not isinstance(line_summary, dict)
            or not isinstance(line_summary.get("total_source_lines"), int)
        ):
            findings.append(make_finding("EVIDENCE_JSON_INVALID", "BLOCK", "00-项目证据/source-line-count.json", "Source line report must contain PASS and an integer total_source_lines."))
        elif manifest_total_lines is not None and line_summary["total_source_lines"] != manifest_total_lines:
            findings.append(make_finding("SOURCE_LINE_COUNT_MISMATCH", "BLOCK", "00-项目证据/source-line-count.json", "Source line report differs from the source manifest."))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(make_finding("EVIDENCE_JSON_INVALID", "BLOCK", "00-项目证据/source-line-count.json", str(exc)))
    try:
        evidence = load_json(material_root / "00-项目证据" / "source-evidence-map.json")
        if not isinstance(evidence, dict):
            raise ValueError("source evidence map must be an object")
        evidence_features = validate_evidence_map_payload(evidence)
        if not any(item.get("confidence") == "confirmed" for item in evidence_features):
            findings.append(make_finding("CONFIRMED_FEATURE_EVIDENCE_MISSING", "BLOCK", "00-项目证据/source-evidence-map.json", "No confirmed feature evidence is recorded."))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        findings.append(make_finding("EVIDENCE_JSON_INVALID", "BLOCK", "00-项目证据/source-evidence-map.json", str(exc)))
    try:
        business = load_json(material_root / "01-草稿" / "业务理解.json")
        validate_business_understanding_payload(
            business,
            known_evidence_ids={str(item.get("feature_id")) for item in evidence_features},
            project_root=project_root,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        findings.append(make_finding("DRAFT_JSON_INVALID", "BLOCK", "01-草稿/业务理解.json", str(exc)))
    try:
        selection = load_json(material_root / "01-草稿" / "代码文件选择.json")
        candidates = selection.get("candidates") if isinstance(selection, dict) else None
        if (
            not isinstance(selection, dict)
            or selection.get("schema_version") != 1
            or selection.get("user_confirmed") is not True
            or not isinstance(candidates, list)
            or not any(isinstance(item, dict) and item.get("selected") is True for item in candidates)
        ):
            findings.append(make_finding("CODE_SELECTION_NOT_CONFIRMED", "BLOCK", "01-草稿/代码文件选择.json", "Code selection is not user-confirmed."))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(make_finding("DRAFT_JSON_INVALID", "BLOCK", "01-草稿/代码文件选择.json", str(exc)))
    try:
        application = load_json(material_root / "01-草稿" / "申请表信息.json")
        if not isinstance(application, dict):
            findings.append(make_finding("DRAFT_JSON_INVALID", "BLOCK", "01-草稿/申请表信息.json", "Application data must be an object."))
        else:
            report = validate_application_fields(application, require_confirmed=True, snapshot_root=project_root)
            findings.extend(report.get("findings", []))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        findings.append(make_finding("DRAFT_JSON_INVALID", "BLOCK", "01-草稿/申请表信息.json", str(exc)))


def validate_docx(path: Path, material_root: Path, findings: list[dict[str, Any]]) -> None:
    rel = relative_posix(path, material_root)
    if not zipfile.is_zipfile(path):
        findings.append(make_finding("DOCX_PACKAGE_INVALID", "BLOCK", rel, "DOCX is not a valid ZIP package."))
        return
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            required = {"[Content_Types].xml", "_rels/.rels", "word/document.xml"}
            if not required.issubset(names):
                raise ValueError("DOCX lacks required content-types, relationships or word/document.xml parts")
            content_types = ElementTree.fromstring(archive.read("[Content_Types].xml"))
            relationships = ElementTree.fromstring(archive.read("_rels/.rels"))
            document = ElementTree.fromstring(archive.read("word/document.xml"))
        override_ok = any(
            node.attrib.get("PartName") == "/word/document.xml"
            and "wordprocessingml.document.main+xml" in node.attrib.get("ContentType", "")
            for node in content_types.iter()
        )
        relationship_ok = any(
            node.attrib.get("Target", "").lstrip("/") == "word/document.xml"
            and node.attrib.get("Type", "").endswith("/officeDocument")
            for node in relationships.iter()
        )
        document_ok = document.tag.endswith("}document") and any(node.tag.endswith("}body") for node in document.iter())
        if not (override_ok and relationship_ok and document_ok):
            raise ValueError("DOCX package relationships or document content type are invalid")
    except (OSError, ValueError, ElementTree.ParseError, KeyError, zipfile.BadZipFile) as exc:
        findings.append(make_finding("DOCX_PACKAGE_INVALID", "BLOCK", rel, str(exc)))


def docx_referenced_media_hashes(path: Path) -> set[str]:
    hashes: set[str] = set()
    try:
        with zipfile.ZipFile(path) as archive:
            rels_name = "word/_rels/document.xml.rels"
            if rels_name not in archive.namelist():
                return hashes
            relationships = ElementTree.fromstring(archive.read(rels_name))
            document = ElementTree.fromstring(archive.read("word/document.xml"))
            targets = {
                node.attrib.get("Id", ""): node.attrib.get("Target", "")
                for node in relationships.iter()
                if node.attrib.get("Type", "").endswith("/image")
            }
            embedded_ids = {
                value
                for node in document.iter()
                for key, value in node.attrib.items()
                if key.endswith("}embed")
            }
            for relationship_id in embedded_ids:
                target = targets.get(relationship_id, "")
                normalized = (PurePosixPath("word") / PurePosixPath(target)).as_posix()
                if normalized.startswith("word/media/") and normalized in archive.namelist():
                    hashes.add(hashlib.sha256(archive.read(normalized)).hexdigest())
    except (OSError, ElementTree.ParseError, KeyError, zipfile.BadZipFile):
        return set()
    return hashes


def validate_png(path: Path) -> bool:
    try:
        data = path.read_bytes()
    except OSError:
        return False
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return False
    offset = 8
    seen_ihdr = seen_idat = seen_iend = False
    compressed = bytearray()
    width = height = 0
    bit_depth = color_type = interlace = -1
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_data = data[offset + 8 : offset + 8 + length]
        crc_end = offset + 12 + length
        if crc_end > len(data):
            return False
        expected_crc = struct.unpack(">I", data[offset + 8 + length : crc_end])[0]
        if zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF != expected_crc:
            return False
        if chunk_type == b"IHDR":
            if length != 13:
                return False
            width, height = struct.unpack(">II", chunk_data[:8])
            bit_depth, color_type, compression, filter_method, interlace = chunk_data[8:13]
            seen_ihdr = width > 0 and height > 0 and compression == 0 and filter_method == 0
        elif chunk_type == b"IDAT":
            seen_idat = True
            compressed.extend(chunk_data)
        elif chunk_type == b"IEND":
            seen_iend = length == 0
            offset = crc_end
            break
        offset = crc_end
    if not (seen_ihdr and seen_idat and seen_iend and offset == len(data)):
        return False
    try:
        raw = zlib.decompress(bytes(compressed))
    except zlib.error:
        return False
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type)
    allowed_depths = {
        0: {1, 2, 4, 8, 16},
        2: {8, 16},
        3: {1, 2, 4, 8},
        4: {8, 16},
        6: {8, 16},
    }
    if channels is None or bit_depth not in allowed_depths.get(color_type, set()) or interlace != 0:
        return False
    row_bytes = (width * channels * bit_depth + 7) // 8
    if len(raw) != height * (row_bytes + 1):
        return False
    return all(raw[index * (row_bytes + 1)] <= 4 for index in range(height))


def validate_jpeg(path: Path) -> bool:
    try:
        data = path.read_bytes()
    except OSError:
        return False
    if len(data) < 4 or not data.startswith(b"\xff\xd8") or not data.endswith(b"\xff\xd9"):
        return False
    offset = 2
    dimensions_found = False
    scan_data_found = False
    while offset + 4 <= len(data) - 2:
        if data[offset] != 0xFF:
            offset += 1
            continue
        marker = data[offset + 1]
        offset += 2
        if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            continue
        if offset + 2 > len(data):
            return False
        length = int.from_bytes(data[offset : offset + 2], "big")
        if length < 2 or offset + length > len(data):
            return False
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            if length < 7:
                return False
            height = int.from_bytes(data[offset + 3 : offset + 5], "big")
            width = int.from_bytes(data[offset + 5 : offset + 7], "big")
            dimensions_found = width > 0 and height > 0
        if marker == 0xDA:
            scan_start = offset + length
            scan_end = len(data) - 2
            scan_data_found = scan_start < scan_end and any(byte != 0xFF for byte in data[scan_start:scan_end])
            break
        offset += length
    if not dimensions_found or not scan_data_found:
        return False
    try:
        from PIL import Image

        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            image.load()
            return image.format == "JPEG" and image.width > 0 and image.height > 0
    except ImportError:
        return True
    except (OSError, ValueError):
        return False


def validate_image(path: Path) -> bool:
    suffix = path.suffix.lower()
    if suffix == ".png":
        return validate_png(path)
    if suffix in {".jpg", ".jpeg"}:
        return validate_jpeg(path)
    return False


def image_dimensions(path: Path) -> tuple[int, int]:
    try:
        data = path.read_bytes()
    except OSError:
        return 0, 0
    if path.suffix.lower() == ".png" and len(data) >= 24 and data.startswith(b"\x89PNG\r\n\x1a\n"):
        return struct.unpack(">II", data[16:24])
    if path.suffix.lower() in {".jpg", ".jpeg"} and data.startswith(b"\xff\xd8"):
        offset = 2
        while offset + 9 <= len(data):
            if data[offset] != 0xFF:
                offset += 1
                continue
            marker = data[offset + 1]
            offset += 2
            if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
                continue
            if offset + 2 > len(data):
                break
            length = int.from_bytes(data[offset : offset + 2], "big")
            if length < 2 or offset + length > len(data):
                break
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                return int.from_bytes(data[offset + 5 : offset + 7], "big"), int.from_bytes(data[offset + 3 : offset + 5], "big")
            offset += length
    return 0, 0


def validate_manual_quality(material_root: Path, findings: list[dict[str, Any]]) -> None:
    manual_path = material_root / "01-草稿" / "操作手册.md"
    self_check_path = material_root / "01-草稿" / "草稿自检记录.md"
    manual_text = read_text_for_scan(manual_path) if manual_path.is_file() else ""
    if MANUAL_TEMPLATE_PATTERN.search(manual_text):
        findings.append(make_finding("MANUAL_FIELD_TEMPLATE_LANGUAGE", "BLOCK", "01-草稿/操作手册.md", "Manual text uses a prohibited field-template style."))
    if MANUAL_MARKETING_PATTERN.search(manual_text):
        findings.append(make_finding("MANUAL_MARKETING_LANGUAGE", "BLOCK", "01-草稿/操作手册.md", "Manual text contains prohibited marketing language."))
    paragraphs = [
        " ".join(line.split())
        for line in re.split(r"\n\s*\n", manual_text)
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if len(paragraphs) < 2 or any(len(item) < 20 for item in paragraphs):
        findings.append(make_finding("MANUAL_CONTENT_TOO_SHALLOW", "BLOCK", "01-草稿/操作手册.md", "Manual requires at least two substantive natural-language paragraphs."))
    normalized = [re.sub(r"\s+", "", item) for item in paragraphs]
    if len(normalized) != len(set(normalized)):
        findings.append(make_finding("MANUAL_DUPLICATE_PARAGRAPH", "BLOCK", "01-草稿/操作手册.md", "Manual contains a duplicated paragraph."))
    self_check = read_text_for_scan(self_check_path) if self_check_path.is_file() else ""
    if report_status(self_check_path) != "PASS":
        findings.append(make_finding("MANUAL_SELF_CHECK_INVALID", "BLOCK", "01-草稿/草稿自检记录.md", "Manual self-check must contain status: PASS."))
    reviewer = re.search(r"(?im)^\s*reviewer\s*:\s*(\S.*?)\s*$", self_check)
    reviewed_at = re.search(r"(?im)^\s*reviewed_at\s*:\s*(\S.*?)\s*$", self_check)
    if not reviewer or not reviewed_at:
        findings.append(make_finding("MANUAL_SELF_CHECK_INVALID", "BLOCK", "01-草稿/草稿自检记录.md", "Manual self-check requires reviewer and reviewed_at."))
    elif reviewed_at:
        try:
            datetime.fromisoformat(reviewed_at.group(1).replace("Z", "+00:00"))
        except ValueError:
            findings.append(make_finding("MANUAL_SELF_CHECK_INVALID", "BLOCK", "01-草稿/草稿自检记录.md", "reviewed_at must be ISO-8601."))
    for key in MANUAL_SELF_CHECK_KEYS:
        if re.search(rf"(?im)^\s*{re.escape(key)}\s*:\s*PASS\s*$", self_check) is None:
            findings.append(make_finding("MANUAL_SELF_CHECK_INVALID", "BLOCK", "01-草稿/草稿自检记录.md", f"Manual self-check is missing {key}: PASS."))


def pdf_page_count(path: Path) -> int:
    try:
        data = path.read_bytes()
    except OSError:
        return 0
    if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-1024:]:
        return 0
    if b"xref" not in data or b"trailer" not in data or b"startxref" not in data:
        return 0
    startxref_matches = list(re.finditer(rb"startxref\s+(\d+)\s+%%EOF\s*$", data, re.DOTALL))
    if not startxref_matches:
        return 0
    xref_offset = int(startxref_matches[-1].group(1))
    if xref_offset < 0 or data[xref_offset : xref_offset + 4] != b"xref":
        return 0
    structural_pages = len(PDF_PAGE_PATTERN.findall(data))
    declared_page_counts = [int(value) for value in re.findall(rb"/Type\s*/Pages\b[^>]*?/Count\s+(\d+)", data, re.DOTALL)]
    if structural_pages <= 0 or not declared_page_counts or structural_pages not in declared_page_counts:
        return 0
    pdfinfo = shutil.which("pdfinfo")
    if not pdfinfo:
        return structural_pages
    try:
        completed = subprocess.run(
            [pdfinfo, str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError):
        return 0
    if completed.returncode != 0:
        return 0
    match = re.search(rb"(?im)^Pages:\s*(\d+)\s*$", completed.stdout)
    parsed_pages = int(match.group(1)) if match else 0
    return parsed_pages if parsed_pages > 0 and parsed_pages == structural_pages else 0


def git_tracked_paths(project_root: Path, paths: list[Path]) -> tuple[set[str], str]:
    if not shutil.which("git"):
        return set(), "unavailable"
    try:
        probe = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "--is-inside-work-tree"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            shell=False,
        )
        if probe.returncode != 0:
            return set(), "not-a-repository"
        completed = subprocess.run(
            ["git", "-C", str(project_root), "-c", "core.quotePath=false", "ls-files", "-z"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            shell=False,
        )
        if completed.returncode != 0:
            return set(), "error"
        tracked = {
            raw.decode("utf-8", errors="surrogateescape").replace("\\", "/")
            for raw in completed.stdout.split(b"\0")
            if raw
        }
        result: set[str] = set()
        for path in paths:
            try:
                rel = path.resolve().relative_to(project_root.resolve()).as_posix()
            except ValueError:
                continue
            if rel in tracked:
                result.add(rel)
        return result, "verified"
    except (OSError, subprocess.SubprocessError):
        return set(), "error"


def build_output_manifest(material_root: Path, manifest_path: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for path in sorted((item for item in material_root.rglob("*") if item.is_file()), key=lambda item: item.as_posix().lower()):
        if path.resolve() == manifest_path.resolve():
            continue
        files.append(
            {
                "path": relative_posix(path, material_root),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return {"schema_version": 1, "root": str(material_root), "files": files}


def audit_existing_materials(
    project_root: Path,
    source_root: Path,
    material_root: Path,
    repair_ledger_path: Path | None = None,
) -> dict[str, Any]:
    project = project_root.resolve()
    source = ensure_within_root(project, source_root)
    materials = ensure_within_root(project, material_root)
    if not source.exists():
        raise FileNotFoundError(f"Existing material source does not exist: {source}")
    candidates = [source] if source.is_file() else [path for path in source.rglob("*") if path.is_file() and not path.is_symlink()]
    existing_backup_root = materials / "00-项目证据" / "original-materials-backup"
    candidates = [path for path in candidates if not path.resolve().is_relative_to(existing_backup_root.resolve())]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup_root = existing_backup_root / timestamp
    report_dir = materials / "04-校验报告"
    findings: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    repair_ledger: dict[str, Any] | None = None
    authorized_changes: list[dict[str, Any]] = []
    baseline_report_rel: str | None = None
    if repair_ledger_path is not None:
        ledger_path = ensure_within_root(project, repair_ledger_path)
        payload = load_json(ledger_path)
        if not isinstance(payload, dict) or payload.get("schema_version") != 1 or payload.get("repair_authorized") is not True:
            raise ValueError("repair ledger must be a schema_version 1 object with repair_authorized=true")
        if not isinstance(payload.get("authorized_by"), str) or not payload["authorized_by"].strip():
            raise ValueError("repair ledger authorized_by is required")
        try:
            datetime.fromisoformat(str(payload.get("authorized_at", "")).replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("repair ledger authorized_at must be ISO-8601") from exc
        if not isinstance(payload.get("authorized_changes"), list):
            raise ValueError("repair ledger authorized_changes must be an array")
        repair_ledger = payload
    if not candidates:
        findings.append(make_finding("EXISTING_MATERIALS_EMPTY", "BLOCK", ".", "No existing material files were found."))
    for path in sorted(candidates, key=lambda item: item.as_posix().lower()):
        ensure_within_root(project, path)
        relative = Path(path.name) if source.is_file() else path.relative_to(source)
        destination = ensure_within_root(materials, backup_root / relative)
        payload = path.read_bytes()
        atomic_write_bytes(destination, payload)
        os.chmod(destination, stat.S_IREAD)
        source_hash = sha256_file(path)
        backup_hash = sha256_file(destination)
        matches = source_hash == backup_hash
        if not matches:
            findings.append(make_finding("MATERIAL_BACKUP_HASH_MISMATCH", "BLOCK", relative.as_posix(), "Backup hash differs from the original."))
        text = read_text_for_scan(path)
        if path.suffix.lower() == ".docx":
            validate_docx(path, project, findings)
        if text and PLACEHOLDER_PATTERN.search(text):
            findings.append(make_finding("PLACEHOLDER_IN_EXISTING_MATERIAL", "BLOCK", relative.as_posix(), "Existing material contains placeholder text."))
        if text and SENSITIVE_PATTERN.search(text):
            findings.append(make_finding("SENSITIVE_DATA_IN_EXISTING_MATERIAL", "CAUTION", relative.as_posix(), "Existing material contains a sensitive-value pattern; keep it local and review Git tracking."))
        records.append(
            {
                "path": relative.as_posix(),
                "size": len(payload),
                "sha256": source_hash,
                "backup_path": relative_posix(destination, materials),
                "backup_sha256": backup_hash,
                "hash_matches": matches,
                "backup_read_only": not bool(destination.stat().st_mode & stat.S_IWRITE),
            }
        )
    if repair_ledger is not None:
        raw_baseline = repair_ledger.get("baseline_report")
        if not isinstance(raw_baseline, str) or not raw_baseline.strip():
            raise ValueError("repair ledger baseline_report is required")
        baseline_path = ensure_within_root(materials, materials / raw_baseline)
        baseline = load_json(baseline_path)
        baseline_files = baseline.get("files") if isinstance(baseline, dict) else None
        if not isinstance(baseline_files, list) or any(not isinstance(item, dict) for item in baseline_files):
            raise ValueError("repair ledger baseline_report does not contain an audit file list")
        baseline_report_rel = relative_posix(baseline_path, materials)
        before_by_path = {str(item.get("path", "")): str(item.get("sha256", "")) for item in baseline_files}
        after_by_path = {str(item.get("path", "")): str(item.get("sha256", "")) for item in records}
        ledger_by_path: dict[str, dict[str, Any]] = {}
        for item in repair_ledger["authorized_changes"]:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                raise ValueError("each authorized change must be an object with a path")
            ledger_by_path[item["path"]] = item
        changed_paths = sorted(
            path for path in set(before_by_path) | set(after_by_path) if before_by_path.get(path) != after_by_path.get(path)
        )
        for path in changed_paths:
            ledger_item = ledger_by_path.get(path)
            if ledger_item is None:
                findings.append(make_finding("UNAUTHORIZED_MATERIAL_CHANGE", "BLOCK", path, "A material changed outside the authorized repair ledger."))
                continue
            if (
                ledger_item.get("before_sha256") != before_by_path.get(path)
                or ledger_item.get("after_sha256") != after_by_path.get(path)
                or not isinstance(ledger_item.get("description"), str)
                or not ledger_item["description"].strip()
            ):
                findings.append(make_finding("REPAIR_LEDGER_HASH_MISMATCH", "BLOCK", path, "Authorized repair hashes or description do not match the audited bytes."))
                continue
            authorized_changes.append(ledger_item)
        unused = sorted(set(ledger_by_path) - set(changed_paths))
        for path in unused:
            findings.append(make_finding("REPAIR_LEDGER_UNUSED_CHANGE", "BLOCK", path, "The repair ledger claims a change that is absent from the audited materials."))
    errors = sum(item["severity"] in {"BLOCK", "ERROR"} for item in findings)
    warnings = sum(item["severity"] == "CAUTION" for item in findings)
    status = "BLOCK" if errors else ("CAUTION" if warnings else "PASS")
    result = make_result(
        "audit_existing_materials",
        status,
        {"files": len(records), "errors": errors, "warnings": warnings},
        schema_version=1,
        audited_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        project_root=str(project),
        source_root=str(source),
        backup_root=relative_posix(backup_root, materials),
        files=records,
        modifications_performed=bool(authorized_changes),
        repair_authorized=repair_ledger is not None,
        authorized_changes=authorized_changes,
        baseline_report=baseline_report_rel,
        revalidation_complete=repair_ledger is not None and errors == 0,
        revalidation_required_after_change=repair_ledger is None,
        sensitive_values_echoed=False,
    )
    result["findings"] = findings
    report_dir.mkdir(parents=True, exist_ok=True)
    json_report = report_dir / "material-audit-report.json"
    md_report = report_dir / "material-audit-report.md"
    immutable_json_report = report_dir / f"material-audit-report-{timestamp}.json"
    result["immutable_report"] = relative_posix(immutable_json_report, materials)
    write_json(json_report, result)
    write_json(immutable_json_report, result)
    lines = [
        "# 已有软著材料审计报告",
        "",
        f"status: {result['status']}",
        f"modifications_performed: {str(result['modifications_performed']).lower()}",
        f"repair_authorized: {str(result['repair_authorized']).lower()}",
        f"revalidation_complete: {str(result['revalidation_complete']).lower()}",
        "",
        "## Findings",
        "",
    ]
    if not findings:
        lines.append("- None")
    else:
        for item in findings:
            lines.append(f"- [{item['severity']}] `{item['rule_id']}` `{item['path']}`：{item['message']}")
    lines.append("")
    atomic_write_text(md_report, "\n".join(lines))
    result["outputs"] = [
        relative_posix(json_report, materials),
        relative_posix(md_report, materials),
        relative_posix(immutable_json_report, materials),
    ]
    return result


def checklist_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 最终检查清单",
        "",
        f"status: {result['status']}",
        f"submission_ready: {str(result['submission_ready']).lower()}",
        "",
        "## Findings",
        "",
    ]
    if not result.get("findings"):
        lines.append("- None")
    else:
        for item in result["findings"]:
            lines.append(f"- [{item['severity']}] `{item['rule_id']}` `{item['path']}`：{item['message']}")
    lines.append("")
    return "\n".join(lines)


def update_final_review_state(material_root: Path, status: str, evidence_paths: list[Path]) -> None:
    state_path = material_root / "workflow-state.json"
    state = load_json(state_path)
    if not isinstance(state, dict) or not isinstance(state.get("stages"), dict):
        raise ValueError("Cannot update final review because workflow-state.json is invalid")
    final_stage = state["stages"].get("final-review")
    if not isinstance(final_stage, dict):
        final_stage = {"confirmed_by_user": False}
        state["stages"]["final-review"] = final_stage
    final_stage["status"] = status.lower()
    final_stage["evidence"] = [relative_posix(path, material_root) for path in evidence_paths]
    final_stage["confirmed_by_user"] = False
    state["current_stage"] = "final-review"
    state["updated_at"] = utc_now()
    write_json(state_path, state)


def validate_outputs(
    material_root: str | Path,
    project_root: str | Path | None = None,
    *,
    write_manifest: bool = False,
) -> dict[str, Any]:
    materials = Path(material_root).expanduser().resolve()
    if not materials.is_dir():
        raise NotADirectoryError(f"Material root does not exist: {materials}")
    project = Path(project_root).expanduser().resolve() if project_root else materials.parent.resolve()
    findings: list[dict[str, Any]] = []
    for rel in REQUIRED_DIRECTORIES:
        if not (materials / rel).is_dir():
            findings.append(make_finding("REQUIRED_DIRECTORY_MISSING", "BLOCK", rel, "Required output directory is missing."))
    for rel in (*REQUIRED_EVIDENCE_FILES, *REQUIRED_DRAFT_FILES, "02-截图/screenshot-plan.md"):
        path = materials / rel
        if not path.is_file() or path.stat().st_size == 0:
            findings.append(make_finding("REQUIRED_OUTPUT_MISSING", "BLOCK", rel, "Required output file is missing or empty."))
    _ = validate_state(materials, findings)
    validate_json_evidence(materials, project, findings)

    consistency_inputs = (
        materials / "01-草稿" / "申请表信息.json",
        materials / "00-项目证据" / "source-manifest.json",
        materials / "01-草稿" / "代码文件选择.json",
        materials / "00-项目证据" / "source-evidence-map.json",
    )
    if all(path.is_file() for path in consistency_inputs) and project.is_dir():
        try:
            live_consistency = validate_consistency(
                consistency_inputs[0],
                materials,
                consistency_inputs[1],
                consistency_inputs[2],
                consistency_inputs[3],
                project,
            )
            findings.extend(live_consistency.get("findings", []))
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
            findings.append(make_finding("LIVE_CONSISTENCY_ERROR", "BLOCK", ".", str(exc)))

    screenshot_dir = materials / "02-截图" / "images"
    images = [path for path in screenshot_dir.rglob("*") if path.is_file() and path.stat().st_size > 0] if screenshot_dir.is_dir() else []
    if not images:
        findings.append(make_finding("SCREENSHOT_FILES_MISSING", "BLOCK", "02-截图/images", "No real screenshots are present."))
    screenshot_plan = materials / "02-截图" / "screenshot-plan.md"
    plan_text = read_text_for_scan(screenshot_plan) if screenshot_plan.is_file() else ""
    plan_has_labels = all(label in plan_text for label in SCREENSHOT_METADATA_LABELS)
    for path in images:
        rel = relative_posix(path, materials)
        if not validate_image(path):
            findings.append(make_finding("SCREENSHOT_IMAGE_INVALID", "BLOCK", rel, "Screenshot is not a structurally valid PNG or JPEG image."))
        matching_lines = [line for line in plan_text.splitlines() if path.name in line]
        valid_row = False
        for line in matching_lines:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) < len(SCREENSHOT_METADATA_LABELS) or cells[0] != path.name:
                continue
            if cells[8] and cells[9] in {"是", "否", "yes", "no"} and cells[10].lower() == sha256_file(path).lower():
                try:
                    datetime.fromisoformat(cells[7].replace("Z", "+00:00"))
                    valid_row = True
                except ValueError:
                    pass
        width, height = image_dimensions(path)
        if width < MIN_SCREENSHOT_WIDTH or height < MIN_SCREENSHOT_HEIGHT:
            findings.append(make_finding("SCREENSHOT_DIMENSIONS_TOO_SMALL", "BLOCK", rel, "Screenshot dimensions are below the workflow minimum."))
        if not plan_has_labels or not valid_row:
            findings.append(
                make_finding(
                    "SCREENSHOT_METADATA_MISSING",
                    "BLOCK",
                    rel,
                    "Screenshot plan lacks the file's page, path, data, action, feature, method and capture-time metadata.",
                )
            )

    validate_manual_quality(materials, findings)

    formal_dir = materials / "03-正式资料"
    formal_files = [path for path in formal_dir.rglob("*") if path.is_file()] if formal_dir.is_dir() else []
    application_txt = formal_dir / "申请表信息.txt"
    if not application_txt.is_file() or application_txt.stat().st_size == 0:
        findings.append(make_finding("FORMAL_APPLICATION_TXT_MISSING", "BLOCK", "03-正式资料/申请表信息.txt", "Formal application TXT is missing."))
    manual_docx = [path for path in formal_files if path.suffix.lower() == ".docx" and "操作手册" in path.name]
    code_docx = [path for path in formal_files if path.suffix.lower() == ".docx" and "代码" in path.name]
    if not manual_docx:
        findings.append(make_finding("FORMAL_MANUAL_DOCX_MISSING", "BLOCK", "03-正式资料", "Formal operation manual DOCX is missing."))
    if not code_docx:
        findings.append(make_finding("FORMAL_CODE_DOCX_MISSING", "BLOCK", "03-正式资料", "Formal code material DOCX is missing."))
    for path in manual_docx + code_docx:
        validate_docx(path, materials, findings)
    embedded_screenshot_hashes: set[str] = set()
    for path in manual_docx:
        embedded_screenshot_hashes.update(docx_referenced_media_hashes(path))
    for image_path in images:
        if sha256_file(image_path) not in embedded_screenshot_hashes:
            findings.append(
                make_finding(
                    "SCREENSHOT_NOT_EMBEDDED_IN_MANUAL",
                    "BLOCK",
                    relative_posix(image_path, materials),
                    "Every confirmed screenshot must be embedded in a formal operation-manual DOCX.",
                )
            )

    scan_files = [
        path
        for path in materials.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".txt", ".log", ".json", ".docx"}
    ]
    sensitive_formal_paths: set[Path] = set()
    for path in scan_files:
        text = read_text_for_scan(path)
        rel = relative_posix(path, materials)
        if path.is_relative_to(formal_dir) and PLACEHOLDER_PATTERN.search(text):
            findings.append(make_finding("PLACEHOLDER_IN_FORMAL_OUTPUT", "BLOCK", rel, "Formal output contains placeholder text."))
        if (path.suffix.lower() == ".log" or "tests" in {part.lower() for part in path.parts}) and SENSITIVE_PATTERN.search(text):
            findings.append(make_finding("SENSITIVE_DATA_IN_LOG_OR_TEST", "BLOCK", rel, "A log or test artifact contains a sensitive-value pattern."))
        if path.is_relative_to(formal_dir) and SENSITIVE_PATTERN.search(text):
            sensitive_formal_paths.add(path.resolve())
        elif SENSITIVE_PATTERN.search(text):
            findings.append(make_finding("SENSITIVE_DATA_IN_PUBLIC_ARTIFACT", "BLOCK", rel, "A public evidence, draft, screenshot plan or report contains a sensitive-value pattern."))

    report_dir = materials / "04-校验报告"
    for name in ("consistency-report.md", "provenance-report.md", "render-report.md"):
        path = report_dir / name
        if not path.is_file():
            findings.append(make_finding("VALIDATION_REPORT_MISSING", "BLOCK", f"04-校验报告/{name}", "A required validation report is missing."))
            continue
        status = report_status(path)
        if status is None:
            findings.append(
                make_finding(
                    "VALIDATION_REPORT_STATUS_MISSING",
                    "BLOCK",
                    f"04-校验报告/{name}",
                    "Validation report lacks a machine-readable PASS, CAUTION or BLOCK status.",
                )
            )
        elif status == "BLOCK":
            findings.append(
                make_finding(
                    "VALIDATION_REPORT_BLOCKED",
                    "BLOCK",
                    f"04-校验报告/{name}",
                    "Validation report records a blocking result.",
                )
            )
        elif status == "CAUTION":
            findings.append(
                make_finding(
                    "VALIDATION_REPORT_CAUTION",
                    "CAUTION",
                    f"04-校验报告/{name}",
                    "Validation report records a non-blocking caution that must remain visible in the final result.",
                )
            )
    render_path = report_dir / "render-report.md"
    if render_path.is_file():
        render_text = read_text_for_scan(render_path)
        repair_match = REPAIR_LINE.search(render_text)
        if not VISUAL_LINE.search(render_text) or not repair_match or int(repair_match.group(1)) < 1:
            findings.append(make_finding("DOCX_VISUAL_VALIDATION_INCOMPLETE", "BLOCK", "04-校验报告/render-report.md", "Visual rendering and at least one repair/recheck round are required."))
        records: list[dict[str, Any]] = []
        for raw_record in RENDER_RECORD_LINE.findall(render_text):
            try:
                record = json.loads(raw_record)
            except json.JSONDecodeError as exc:
                findings.append(make_finding("RENDER_RECORD_INVALID", "BLOCK", "04-校验报告/render-report.md", str(exc)))
                continue
            if not isinstance(record, dict):
                findings.append(make_finding("RENDER_RECORD_INVALID", "BLOCK", "04-校验报告/render-report.md", "render_record must be a JSON object."))
                continue
            records.append(record)
        docx_paths = {path.resolve(): path for path in manual_docx + code_docx}
        covered_inputs: set[Path] = set()
        seen_artifacts: set[Path] = set()
        for record in records:
            raw_input = str(record.get("input", "")).strip()
            raw_artifact = str(record.get("artifact", "")).strip()
            try:
                input_path = ensure_within_root(materials, materials / raw_input)
                artifact = ensure_within_root(materials, materials / raw_artifact)
            except ValueError as exc:
                findings.append(make_finding("RENDER_RECORD_PATH_INVALID", "BLOCK", raw_input or raw_artifact or ".", str(exc)))
                continue
            if input_path.resolve() not in docx_paths:
                findings.append(make_finding("RENDER_INPUT_NOT_FORMAL_DOCX", "BLOCK", raw_input, "Render input is not one of the formal DOCX files."))
                continue
            covered_inputs.add(input_path.resolve())
            if artifact.resolve() in seen_artifacts:
                findings.append(make_finding("RENDER_ARTIFACT_DUPLICATE", "BLOCK", raw_artifact, "A rendered artifact is reused for more than one render record."))
            seen_artifacts.add(artifact.resolve())
            if str(record.get("input_sha256", "")).lower() != sha256_file(input_path).lower():
                findings.append(make_finding("RENDER_INPUT_HASH_MISMATCH", "BLOCK", raw_input, "Render record input hash does not match the current DOCX."))
            renderer = str(record.get("renderer", "")).strip()
            command = str(record.get("command", "")).strip()
            rendered_at = str(record.get("rendered_at", "")).strip()
            if not renderer or not command or not rendered_at:
                findings.append(make_finding("RENDER_TOOL_EVIDENCE_MISSING", "BLOCK", raw_input, "Renderer, command and render timestamp are required."))
            else:
                try:
                    datetime.fromisoformat(rendered_at.replace("Z", "+00:00"))
                except ValueError:
                    findings.append(make_finding("RENDER_TIMESTAMP_INVALID", "BLOCK", raw_input, "rendered_at must be an ISO-8601 timestamp."))
            actual_pages = 0
            if artifact.is_file() and artifact.stat().st_size > 0:
                if artifact.suffix.lower() == ".pdf":
                    actual_pages = pdf_page_count(artifact)
                elif validate_image(artifact):
                    actual_pages = 1
            if actual_pages <= 0:
                findings.append(make_finding("RENDER_ARTIFACT_INVALID", "BLOCK", raw_artifact, "Rendered artifact is not a structurally valid PDF, PNG or JPEG."))
            page_count = record.get("page_count")
            if not isinstance(page_count, int) or isinstance(page_count, bool) or page_count <= 0 or page_count != actual_pages:
                findings.append(make_finding("RENDER_PAGE_COUNT_MISMATCH", "BLOCK", raw_artifact, "Recorded page count differs from the rendered artifact."))
        if set(docx_paths) != covered_inputs:
            findings.append(make_finding("RENDER_ARTIFACT_COUNT_INSUFFICIENT", "BLOCK", "04-校验报告/render-report.md", "Every formal DOCX requires a current, uniquely mapped render record."))

    tracked, tracking_state = git_tracked_paths(project, formal_files) if project.is_dir() else (set(), "error")
    if tracking_state in {"unavailable", "error"}:
        findings.append(make_finding("GIT_TRACKING_STATUS_UNVERIFIED", "CAUTION", ".", "Git tracking status could not be verified."))
    for rel in sorted(tracked):
        tracked_path = (project / rel).resolve()
        if tracked_path in sensitive_formal_paths:
            findings.append(make_finding("SENSITIVE_FORMAL_FILE_GIT_TRACKED", "BLOCK", rel, "A Git-tracked formal material contains sensitive data."))
        else:
            findings.append(make_finding("FORMAL_FILE_GIT_TRACKED", "CAUTION", rel, "A formal material file is tracked by Git; verify that it remains intentionally sanitized."))

    unique_findings: list[dict[str, Any]] = []
    seen_findings: set[tuple[Any, ...]] = set()
    for item in findings:
        key = (item.get("rule_id"), item.get("severity"), item.get("path"), item.get("line"), item.get("message"))
        if key not in seen_findings:
            seen_findings.add(key)
            unique_findings.append(item)
    findings = unique_findings
    errors = sum(item["severity"] in {"BLOCK", "ERROR"} for item in findings)
    warnings = sum(item["severity"] == "CAUTION" for item in findings)
    status = "BLOCK" if errors else ("CAUTION" if warnings else "PASS")
    result = make_result(
        "validate_outputs",
        status,
        {"errors": errors, "warnings": warnings, "formal_files": len(formal_files), "screenshots": len(images)},
        schema_version=1,
        material_root=str(materials),
        project_root=str(project),
        submission_ready=status == "PASS",
        sensitive_values_echoed=False,
        sensitive_formal_files=len(sensitive_formal_paths),
        git_tracking_status=tracking_state,
    )
    result["findings"] = findings
    if write_manifest:
        manifest_path = report_dir / "output-manifest.json"
        manifest_payload = build_output_manifest(materials, manifest_path)
        write_json(manifest_path, manifest_payload)
        result["output_manifest"] = relative_posix(manifest_path, materials)
    return result


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = JsonArgumentParser(description="Validate a complete software copyright material bundle.")
    parser.add_argument("material_root", type=Path)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--output", type=Path, help="Output manifest path; defaults to 04-校验报告/output-manifest.json")
    parser.add_argument("--report", type=Path, help="Final checklist path; defaults to 04-校验报告/final-checklist.md")
    parser.add_argument("--audit-existing", type=Path, help="Mode B: back up and audit an existing material file or directory without modifying it")
    parser.add_argument("--repair-ledger", type=Path, help="Mode B: validate authorized repairs against an immutable prior audit report")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        materials = args.material_root.expanduser().resolve()
        if args.audit_existing is not None:
            if args.output or args.report:
                raise ValueError("--output/--report are final-review options and cannot be combined with --audit-existing")
            project = args.project_root.expanduser().resolve() if args.project_root else materials.parent.resolve()
            project = Path(resolve_existing_root(project))
            materials = ensure_within_root(project, materials)
            materials.mkdir(parents=True, exist_ok=True)
            source = args.audit_existing.expanduser()
            if not source.is_absolute():
                source = project / source
            ledger = args.repair_ledger.expanduser() if args.repair_ledger is not None else None
            if ledger is not None and not ledger.is_absolute():
                ledger = project / ledger
            result = audit_existing_materials(project, source, materials, ledger)
            return emit_json(result)
        if args.repair_ledger is not None:
            raise ValueError("--repair-ledger requires --audit-existing")
        result = validate_outputs(materials, args.project_root, write_manifest=False)
        report_path = ensure_within_root(materials, args.report or (materials / "04-校验报告" / "final-checklist.md"))
        manifest_path = ensure_within_root(materials, args.output or (materials / "04-校验报告" / "output-manifest.json"))
        state_path = materials / "workflow-state.json"
        if report_path.resolve() == manifest_path.resolve():
            raise ValueError("Final checklist and output manifest must use different paths")
        for target in (report_path, manifest_path, state_path):
            if target.exists() and not target.is_file():
                raise ValueError(f"Output target is not a file: {target}")
        previous = {path: path.read_bytes() if path.is_file() else None for path in (report_path, manifest_path, state_path)}
        try:
            atomic_write_text(report_path, checklist_markdown(result))
            update_final_review_state(materials, result["status"], [report_path, manifest_path])
            write_json(manifest_path, build_output_manifest(materials, manifest_path))
        except Exception:
            for path, payload in previous.items():
                try:
                    if payload is None:
                        path.unlink(missing_ok=True)
                    else:
                        atomic_write_bytes(path, payload)
                except OSError:
                    pass
            raise
        result["outputs"] = [relative_posix(report_path, materials), relative_posix(manifest_path, materials)]
        return emit_json(result)
    except Exception as exc:
        result = make_result("validate_outputs", "ERROR", "Output validation failed")
        result["findings"] = [make_finding("OUTPUT_VALIDATION_ERROR", "ERROR", ".", str(exc))]
        return emit_json(result)


if __name__ == "__main__":
    raise SystemExit(main())
