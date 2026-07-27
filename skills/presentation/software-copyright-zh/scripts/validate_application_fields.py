#!/usr/bin/env python3
"""Validate application field completeness, logic and confirmation without echoing secrets."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

from collect_source_manifest import (
    JsonArgumentParser,
    emit_json,
    ensure_within_root,
    load_json,
    make_finding,
    make_result,
    relative_posix,
    write_json,
)


FIELD_RULES: dict[str, dict[str, Any]] = {
    "software_full_name": {"required": True, "types": (str,)},
    "software_short_name": {"required": False, "types": (str, type(None))},
    "version": {"required": True, "types": (str,)},
    "software_category": {"required": True, "types": (str,)},
    "copyright_holders": {"required": True, "types": (list,)},
    "development_completion_date": {"required": True, "types": (str,), "date": True},
    "development_method": {"required": True, "types": (str,)},
    "publication_status": {"required": True, "types": (str,), "allowed": {"published", "unpublished"}},
    "first_publication_date": {"required": False, "types": (str, type(None)), "date_optional": True},
    "rights_scope": {"required": True, "types": (str,)},
    "rights_acquisition_method": {"required": True, "types": (str,)},
    "development_hardware": {"required": True, "types": (str,)},
    "runtime_hardware": {"required": True, "types": (str,)},
    "development_os": {"required": True, "types": (str,)},
    "development_tools": {"required": True, "types": (str, list)},
    "runtime_platform": {"required": True, "types": (str,)},
    "runtime_support": {"required": True, "types": (str, list)},
    "programming_languages": {"required": True, "types": (list,)},
    "source_line_count": {"required": True, "types": (int,), "nonnegative": True},
    "application_purpose": {"required": True, "types": (str,)},
    "industry": {"required": True, "types": (str,)},
    "main_functions": {"required": True, "types": (str,)},
    "technical_characteristics": {"required": True, "types": (str, list)},
}

SENSITIVE_KEY_FRAGMENTS = {
    "identity_document",
    "identity_number",
    "id_card",
    "certificate_number",
    "credit_code",
    "social_credit",
    "phone_number",
    "mobile_number",
    "password",
    "api_key",
    "access_token",
    "private_key",
    "client_secret",
}

CURRENT_FORM_HOSTS = {"register.ccopyright.com.cn", "www.ccopyright.com.cn", "ccopyright.com.cn"}
SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
SENSITIVE_VALUE_PATTERN = re.compile(
    r"(?<!\d)1[3-9]\d{9}(?!\d)"
    r"|(?<!\d)[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[0-9Xx](?!\d)"
    r"|(?<![0-9A-Z])[0-9A-Z]{18}(?![0-9A-Z])"
)
STRING_ARRAY_FIELDS = {
    "development_tools",
    "runtime_support",
    "programming_languages",
    "technical_characteristics",
}

FIELD_DATA_TYPES = {
    "software_full_name": "string",
    "software_short_name": "string",
    "version": "string",
    "software_category": "enum",
    "copyright_holders": "array",
    "development_completion_date": "date",
    "development_method": "enum",
    "publication_status": "enum",
    "first_publication_date": "date",
    "rights_scope": "enum",
    "rights_acquisition_method": "enum",
    "development_hardware": "string",
    "runtime_hardware": "string",
    "development_os": "string",
    "development_tools": "array",
    "runtime_platform": "string",
    "runtime_support": "array",
    "programming_languages": "array",
    "source_line_count": "integer",
    "application_purpose": "string",
    "industry": "string",
    "main_functions": "string",
    "technical_characteristics": "string",
}
FIELD_SOURCES = {"user", "project", "official-page", "inference"}


def normalized_field_value(raw: Any, *, allow_suggested: bool = True) -> Any:
    if isinstance(raw, dict) and ("value" in raw or "suggested_value" in raw):
        value = raw.get("value")
        if value is None and allow_suggested:
            return raw.get("suggested_value")
        return value
    return raw


def serialize_application_txt(data: dict[str, Any]) -> str:
    """Serialize all public application fields deterministically for formal TXT comparison."""

    fields = data.get("fields")
    if not isinstance(fields, dict):
        raise ValueError("application fields must be an object")
    lines = ["schema_version\t1"]
    for key in FIELD_RULES:
        if key not in fields:
            raise ValueError(f"application field is missing: {key}")
        value = normalized_field_value(fields[key], allow_suggested=False)
        lines.append(f"{key}\t{json.dumps(value, ensure_ascii=False, sort_keys=True)}")
    return "\n".join(lines) + "\n"


def parse_application_txt(text: str) -> dict[str, Any]:
    values: dict[str, Any] = {}
    lines = text.splitlines()
    if not lines or lines[0] != "schema_version\t1":
        raise ValueError("formal application TXT must start with schema_version tab 1")
    for line_number, line in enumerate(lines[1:], start=2):
        if "\t" not in line:
            raise ValueError(f"formal application TXT line {line_number} lacks a tab separator")
        key, raw_value = line.split("\t", 1)
        if key not in FIELD_RULES or key in values:
            raise ValueError(f"formal application TXT line {line_number} has an unknown or duplicate field")
        try:
            values[key] = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"formal application TXT line {line_number} contains invalid JSON") from exc
    if set(values) != set(FIELD_RULES):
        raise ValueError("formal application TXT must contain every application field exactly once")
    return values


def field_is_confirmed(key: str, raw: Any, data: dict[str, Any]) -> bool:
    if isinstance(raw, dict) and raw.get("confirmed") is True:
        return True
    confirmed = data.get("confirmed_fields", [])
    return isinstance(confirmed, list) and key in confirmed


def is_missing(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def valid_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except (TypeError, ValueError):
        return False


def validate_field_schema_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Field schema must contain a JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError("Field schema.schema_version must equal 1")
    fields = payload.get("fields")
    if not isinstance(fields, dict):
        raise ValueError("Field schema.fields must be an object")
    for key, spec in fields.items():
        if key not in FIELD_RULES:
            raise ValueError(f"Field schema contains an unknown field: {key}")
        if not isinstance(spec, dict):
            raise ValueError(f"Field schema.fields.{key} must be an object")
        if "character_limit" in spec:
            limit = spec.get("character_limit")
            if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0):
                raise ValueError(f"Field schema.fields.{key}.character_limit must be a positive integer or null")
    return payload


def character_limit_source_is_valid(source: Any) -> bool:
    if isinstance(source, str):
        return bool(source.strip())
    if isinstance(source, dict):
        reference = source.get("reference") or source.get("source_url")
        kind = source.get("kind")
        return isinstance(reference, str) and bool(reference.strip()) and isinstance(kind, str) and bool(kind.strip())
    return False


def current_form_evidence_is_valid(
    data: dict[str, Any],
    findings: list[dict[str, Any]],
    *,
    snapshot_root: Path | None = None,
) -> bool:
    evidence = data.get("current_form_evidence")
    if evidence is None:
        if data.get("official_form_verified_at"):
            findings.append(
                make_finding(
                    "LEGACY_FORM_DATE_NOT_EVIDENCE",
                    "CAUTION",
                    "official_form_verified_at",
                    "A truthy date alone is not current-form evidence and was ignored.",
                )
            )
        findings.append(
            make_finding(
                "OFFICIAL_FORM_NOT_CURRENTLY_VERIFIED",
                "CAUTION",
                ".",
                "Current online registration fields have not been verified; final submission claims are not allowed.",
            )
        )
        return False
    if not isinstance(evidence, dict):
        findings.append(
            make_finding(
                "CURRENT_FORM_EVIDENCE_INVALID",
                "BLOCK",
                "current_form_evidence",
                "Current-form evidence must be an object.",
            )
        )
        return False

    errors: list[tuple[str, str]] = []
    source_url = evidence.get("source_url")
    if not isinstance(source_url, str):
        errors.append(("source_url", "source_url must be an HTTPS URL on the official copyright registry host."))
    else:
        parsed = urlparse(source_url)
        if parsed.scheme.lower() != "https" or (parsed.hostname or "").lower() not in CURRENT_FORM_HOSTS:
            errors.append(("source_url", "source_url must be an HTTPS URL on the official copyright registry host."))
    verified_at = evidence.get("verified_at")
    if not isinstance(verified_at, str) or not valid_date(verified_at):
        errors.append(("verified_at", "verified_at must be a real YYYY-MM-DD date."))
    elif datetime.strptime(verified_at, "%Y-%m-%d").date() > date.today():
        errors.append(("verified_at", "verified_at must not be in the future."))
    form_version = evidence.get("form_version")
    snapshot_path = evidence.get("snapshot_path")
    snapshot_sha256 = evidence.get("snapshot_sha256")
    valid_version = isinstance(form_version, str) and bool(form_version.strip())
    if form_version is not None and not valid_version:
        errors.append(("form_version", "form_version must be a non-empty string when present."))
    snapshot_declared = snapshot_path is not None or snapshot_sha256 is not None
    if snapshot_declared:
        if not isinstance(snapshot_path, str) or not snapshot_path.strip():
            errors.append(("snapshot_path", "snapshot_path must be a non-empty project-relative path."))
        if not isinstance(snapshot_sha256, str) or SHA256_PATTERN.fullmatch(snapshot_sha256) is None:
            errors.append(("snapshot_sha256", "snapshot_sha256 must contain exactly 64 hexadecimal characters."))
    for key, message in errors:
        findings.append(
            make_finding(
                "CURRENT_FORM_EVIDENCE_INVALID",
                "BLOCK",
                f"current_form_evidence.{key}",
                message,
            )
        )
    if errors:
        return False
    if not snapshot_declared:
        findings.append(
            make_finding(
                "CURRENT_FORM_SNAPSHOT_MISSING",
                "CAUTION",
                "current_form_evidence.snapshot_path",
                "A form version label is metadata only; a readable in-project snapshot and matching SHA-256 are required for current-form verification.",
            )
        )
        return False
    capture_method = evidence.get("capture_method")
    captured_at = evidence.get("captured_at")
    page_title = evidence.get("page_title")
    field_names = evidence.get("field_names")
    if capture_method not in {"browser-export", "browser-snapshot", "manual-export"}:
        errors.append(("capture_method", "capture_method must identify how the official page snapshot was collected."))
    try:
        captured = datetime.fromisoformat(str(captured_at).replace("Z", "+00:00"))
        if captured.date().isoformat() != verified_at:
            raise ValueError
    except (TypeError, ValueError):
        errors.append(("captured_at", "captured_at must be ISO-8601 and match verified_at."))
    if not isinstance(page_title, str) or not page_title.strip():
        errors.append(("page_title", "page_title must be recorded from the captured official form."))
    if (
        not isinstance(field_names, list)
        or set(field_names) != set(FIELD_RULES)
        or any(not isinstance(item, str) for item in field_names)
    ):
        errors.append(("field_names", "field_names must contain the complete internal field-key mapping."))
    if evidence.get("user_confirmed_source") is not True:
        errors.append(("user_confirmed_source", "The user must confirm that the snapshot came from the stated official page."))
    if isinstance(source_url, str) and urlparse(source_url).path.lower().endswith("/login.html"):
        errors.append(("source_url", "A login page is not evidence of the current registration form fields."))
    if errors:
        for key, message in errors:
            findings.append(make_finding("CURRENT_FORM_EVIDENCE_INVALID", "BLOCK", f"current_form_evidence.{key}", message))
        return False
    if snapshot_root is None:
        findings.append(
            make_finding(
                "CURRENT_FORM_SNAPSHOT_CONTEXT_MISSING",
                "CAUTION",
                "current_form_evidence.snapshot_path",
                "The snapshot cannot be bound to a project or material root in this validation context.",
            )
        )
        return False

    root = Path(snapshot_root).expanduser().resolve(strict=False)
    if not root.is_dir():
        findings.append(
            make_finding(
                "CURRENT_FORM_SNAPSHOT_ROOT_INVALID",
                "BLOCK",
                "current_form_evidence.snapshot_path",
                "The snapshot root must be an existing project or material directory.",
            )
        )
        return False
    declared_path = Path(snapshot_path)
    candidate = declared_path if declared_path.is_absolute() else root / declared_path
    try:
        snapshot = ensure_within_root(root, candidate)
    except ValueError:
        findings.append(
            make_finding(
                "CURRENT_FORM_SNAPSHOT_OUTSIDE_ROOT",
                "BLOCK",
                "current_form_evidence.snapshot_path",
                "The form snapshot must remain inside the bound project or material root.",
            )
        )
        return False
    try:
        if not snapshot.is_file() or snapshot.stat().st_size == 0:
            raise OSError("snapshot is missing, empty, or not a regular file")
        actual_sha256 = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    except OSError:
        findings.append(
            make_finding(
                "CURRENT_FORM_SNAPSHOT_UNREADABLE",
                "BLOCK",
                "current_form_evidence.snapshot_path",
                "The bound form snapshot is missing, empty, or unreadable.",
            )
        )
        return False
    if actual_sha256.lower() != snapshot_sha256.lower():
        findings.append(
            make_finding(
                "CURRENT_FORM_SNAPSHOT_HASH_MISMATCH",
                "BLOCK",
                "current_form_evidence.snapshot_sha256",
                "The recorded SHA-256 does not match the current bytes of the bound form snapshot.",
            )
        )
        return False
    snapshot_text = snapshot.read_text(encoding="utf-8", errors="ignore")
    if page_title not in snapshot_text:
        findings.append(
            make_finding(
                "CURRENT_FORM_SNAPSHOT_CONTENT_MISMATCH",
                "BLOCK",
                "current_form_evidence.page_title",
                "The captured page title is absent from the bound snapshot.",
            )
        )
        return False
    return True


def iter_sensitive_keys(value: Any, prefix: str = "") -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            lowered = str(key).lower()
            if any(fragment in lowered for fragment in SENSITIVE_KEY_FRAGMENTS):
                yield path
            yield from iter_sensitive_keys(child, path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_sensitive_keys(child, f"{prefix}[{index}]")


def contains_sensitive_value(value: Any) -> bool:
    if isinstance(value, str):
        return SENSITIVE_VALUE_PATTERN.search(value.upper()) is not None
    if isinstance(value, dict):
        return any(contains_sensitive_value(child) for child in value.values())
    if isinstance(value, list):
        return any(contains_sensitive_value(child) for child in value)
    return False


def validate_application_fields(
    data: dict[str, Any],
    *,
    require_confirmed: bool = False,
    allow_sensitive_local: bool = False,
    field_schema: dict[str, Any] | None = None,
    snapshot_root: Path | None = None,
) -> dict[str, Any]:
    if field_schema is not None:
        field_schema = validate_field_schema_payload(field_schema)
    findings: list[dict[str, Any]] = []
    if data.get("schema_version") != 1:
        findings.append(
            make_finding("APPLICATION_SCHEMA_INVALID", "BLOCK", "schema_version", "schema_version must equal 1.")
        )
    fields = data.get("fields", {})
    if not isinstance(fields, dict):
        findings.append(make_finding("APPLICATION_SCHEMA_INVALID", "BLOCK", "fields", "fields must be an object."))
        fields = {}
    confirmed_fields = data.get("confirmed_fields", [])
    if not isinstance(confirmed_fields, list) or not all(isinstance(key, str) for key in confirmed_fields):
        findings.append(
            make_finding(
                "APPLICATION_SCHEMA_INVALID",
                "BLOCK",
                "confirmed_fields",
                "confirmed_fields must be an array of field-name strings.",
            )
        )
    schema_fields = (field_schema or {}).get("fields", {})
    current_form_verified = current_form_evidence_is_valid(data, findings, snapshot_root=snapshot_root)
    character_limits_checked = 0
    for key, rule in FIELD_RULES.items():
        raw = fields.get(key)
        if require_confirmed and not isinstance(raw, dict):
            findings.append(
                make_finding(
                    "FIELD_ENVELOPE_REQUIRED",
                    "BLOCK",
                    key,
                    "Formal validation requires the complete field metadata envelope.",
                )
            )
        if isinstance(raw, dict):
            if "value" not in raw and "suggested_value" not in raw:
                findings.append(
                    make_finding(
                        "FIELD_ENVELOPE_INVALID",
                        "BLOCK",
                        key,
                        "A field object must contain value or suggested_value.",
                    )
                )
            confirmed = raw.get("confirmed")
            if confirmed is not None and not isinstance(confirmed, bool):
                findings.append(
                    make_finding("FIELD_ENVELOPE_INVALID", "BLOCK", key, "confirmed must be a boolean when present.")
                )
            if require_confirmed:
                metadata_rules = {
                    "data_type": isinstance(raw.get("data_type"), str) and raw.get("data_type") == FIELD_DATA_TYPES[key],
                    "required": isinstance(raw.get("required"), bool) and raw.get("required") is bool(rule.get("required")),
                    "character_limit": "character_limit" in raw
                    and (raw.get("character_limit") is None or isinstance(raw.get("character_limit"), int)),
                    "allowed_values": isinstance(raw.get("allowed_values"), list),
                    "source": raw.get("source") in FIELD_SOURCES,
                    "project_inferable": isinstance(raw.get("project_inferable"), bool),
                    "user_confirmation_required": raw.get("user_confirmation_required") is True,
                    "verified_at": isinstance(raw.get("verified_at"), str) and bool(raw.get("verified_at", "").strip()),
                }
                for metadata_key, valid in metadata_rules.items():
                    if not valid:
                        findings.append(
                            make_finding(
                                "FIELD_METADATA_INVALID",
                                "BLOCK",
                                f"{key}.{metadata_key}",
                                "Formal field metadata is missing or inconsistent with the field schema.",
                            )
                        )
                if isinstance(raw.get("verified_at"), str):
                    try:
                        datetime.fromisoformat(raw["verified_at"].replace("Z", "+00:00"))
                    except ValueError:
                        findings.append(
                            make_finding("FIELD_METADATA_INVALID", "BLOCK", f"{key}.verified_at", "verified_at must be ISO-8601.")
                        )
                if isinstance(confirmed_fields, list) and ((key in confirmed_fields) != (raw.get("confirmed") is True)):
                    findings.append(
                        make_finding(
                            "FIELD_CONFIRMATION_CONFLICT",
                            "BLOCK",
                            key,
                            "confirmed_fields and the field envelope disagree.",
                        )
                    )
        if (
            require_confirmed
            and isinstance(raw, dict)
            and is_missing(raw.get("value"))
            and not is_missing(raw.get("suggested_value"))
        ):
            findings.append(
                make_finding(
                    "SUGGESTED_VALUE_NOT_FORMAL",
                    "BLOCK",
                    key,
                    "suggested_value is advisory only and must be copied into value through explicit confirmation before formal validation.",
                )
            )
        value = normalized_field_value(raw, allow_suggested=not require_confirmed)
        if rule.get("required") and is_missing(value):
            findings.append(make_finding("REQUIRED_FIELD_MISSING", "BLOCK", key, "A required field is missing."))
            continue
        if is_missing(value):
            continue
        if not isinstance(value, rule["types"]) or isinstance(value, bool) and int in rule["types"]:
            findings.append(make_finding("FIELD_TYPE_INVALID", "BLOCK", key, "The field value has an invalid type."))
            continue
        if isinstance(value, str) and not value.strip():
            findings.append(make_finding("REQUIRED_FIELD_MISSING", "BLOCK", key, "A required field is blank."))
        allowed = rule.get("allowed")
        if allowed and value not in allowed:
            findings.append(make_finding("FIELD_ENUM_INVALID", "BLOCK", key, "The field value is outside the workflow enum."))
        if rule.get("date") and not valid_date(value):
            findings.append(make_finding("DATE_FORMAT_INVALID", "BLOCK", key, "Date must be a real YYYY-MM-DD value."))
        if rule.get("date_optional") and value is not None and not valid_date(value):
            findings.append(make_finding("DATE_FORMAT_INVALID", "BLOCK", key, "Date must be a real YYYY-MM-DD value."))
        if rule.get("nonnegative") and value < 0:
            findings.append(make_finding("SOURCE_LINE_COUNT_INVALID", "BLOCK", key, "Source line count must be non-negative."))
        if key in STRING_ARRAY_FIELDS and isinstance(value, list):
            if not value or not all(isinstance(item, str) and bool(item.strip()) for item in value):
                findings.append(
                    make_finding("FIELD_NESTED_VALUE_INVALID", "BLOCK", key, "Array entries must be non-empty strings.")
                )
        if key == "copyright_holders" and isinstance(value, list):
            for index, holder in enumerate(value):
                if not isinstance(holder, dict):
                    findings.append(
                        make_finding(
                            "FIELD_NESTED_VALUE_INVALID",
                            "BLOCK",
                            f"{key}[{index}]",
                            "Each copyright holder must be an object.",
                        )
                    )
                    continue
                for holder_key in ("name", "type"):
                    holder_value = holder.get(holder_key)
                    if not isinstance(holder_value, str) or not holder_value.strip():
                        findings.append(
                            make_finding(
                                "FIELD_NESTED_VALUE_INVALID",
                                "BLOCK",
                                f"{key}[{index}].{holder_key}",
                                f"Copyright holder {holder_key} must be a non-empty string.",
                            )
                        )
        limit_spec = raw if isinstance(raw, dict) and "character_limit" in raw else schema_fields.get(key, {})
        if isinstance(limit_spec, dict) and "character_limit" in limit_spec:
            limit = limit_spec.get("character_limit")
            if limit is not None:
                if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
                    findings.append(
                        make_finding(
                            "CHARACTER_LIMIT_INVALID",
                            "BLOCK",
                            key,
                            "character_limit must be a positive integer or null.",
                        )
                    )
                elif not character_limit_source_is_valid(limit_spec.get("character_limit_source")):
                    findings.append(
                        make_finding(
                            "CHARACTER_LIMIT_SOURCE_MISSING",
                            "BLOCK",
                            key,
                            "A declared character_limit requires a non-empty character_limit_source.",
                        )
                    )
                elif not isinstance(value, str):
                    findings.append(
                        make_finding(
                            "CHARACTER_LIMIT_VALUE_TYPE_INVALID",
                            "BLOCK",
                            key,
                            "A declared character_limit can only be applied to a string value.",
                        )
                    )
                else:
                    character_limits_checked += 1
                    if len(value) > limit:
                        findings.append(
                            make_finding(
                                "CHARACTER_LIMIT_EXCEEDED",
                                "BLOCK",
                                key,
                                f"Field length {len(value)} exceeds the declared limit {limit}.",
                            )
                        )
        if require_confirmed and not field_is_confirmed(key, raw, data):
            findings.append(make_finding("FIELD_NOT_CONFIRMED", "BLOCK", key, "The required field is not user-confirmed."))

    status_value = normalized_field_value(fields.get("publication_status"), allow_suggested=not require_confirmed)
    publication_date = normalized_field_value(fields.get("first_publication_date"), allow_suggested=not require_confirmed)
    if status_value == "unpublished" and not is_missing(publication_date):
        findings.append(
            make_finding(
                "UNPUBLISHED_DATE_CONFLICT",
                "BLOCK",
                "first_publication_date",
                "Unpublished software must not contain a first publication date.",
            )
        )
    if status_value == "published" and is_missing(publication_date):
        findings.append(
            make_finding(
                "PUBLISHED_DATE_MISSING",
                "BLOCK",
                "first_publication_date",
                "Published software requires a first publication date.",
            )
        )

    for key_path in iter_sensitive_keys(data):
        if not allow_sensitive_local:
            findings.append(
                make_finding(
                    "SENSITIVE_FIELD_IN_PUBLIC_DATA",
                    "BLOCK",
                    key_path,
                    "Sensitive identity or credential data must not be stored in a public draft or report.",
                )
            )
    if not allow_sensitive_local and contains_sensitive_value(data):
        findings.append(
            make_finding(
                "SENSITIVE_VALUE_IN_PUBLIC_DATA",
                "BLOCK",
                ".",
                "A personal identifier or social-credit-code pattern appears in public application data.",
            )
        )

    if require_confirmed and data.get("user_confirmed") is not True:
        findings.append(make_finding("APPLICATION_NOT_CONFIRMED", "BLOCK", ".", "Application fields lack overall user confirmation."))
    elif data.get("user_confirmed") is not True:
        findings.append(make_finding("APPLICATION_CONFIRMATION_PENDING", "CAUTION", ".", "Overall user confirmation is pending."))

    errors = sum(item["severity"] in {"BLOCK", "ERROR"} for item in findings)
    warnings = sum(item["severity"] == "CAUTION" for item in findings)
    status = "BLOCK" if errors else ("CAUTION" if warnings else "PASS")
    result = make_result(
        "validate_application_fields",
        status,
        {
            "errors": errors,
            "warnings": warnings,
            "checked_fields": len(FIELD_RULES),
            "character_limits_checked": character_limits_checked,
        },
        schema_version=1,
        current_online_form_verified=current_form_verified,
        sensitive_values_echoed=False,
    )
    result["findings"] = findings
    return result


def material_root_for(path: Path) -> Path:
    for ancestor in (path.parent, *path.parents):
        if ancestor.name == "软件著作权申请资料":
            return ancestor
    return path.parent


def project_root_for_application(path: Path) -> Path:
    material_root = material_root_for(path)
    return material_root.parent if material_root.name == "软件著作权申请资料" else material_root


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = JsonArgumentParser(description="Validate software copyright application fields.")
    parser.add_argument("application_json", type=Path)
    parser.add_argument("--schema", type=Path, help="Optional machine-readable JSON field schema")
    parser.add_argument("--require-confirmed", action="store_true")
    parser.add_argument("--allow-sensitive-local", action="store_true")
    parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        application_path = args.application_json.expanduser().resolve()
        if not application_path.is_file():
            raise FileNotFoundError(f"Application JSON does not exist: {application_path}")
        field_schema = None
        if args.schema:
            schema_path = args.schema.expanduser().resolve()
            if not schema_path.is_file():
                raise FileNotFoundError(f"Schema JSON does not exist: {schema_path}")
            field_schema = validate_field_schema_payload(load_json(schema_path))
        data = load_json(application_path)
        if not isinstance(data, dict):
            raise ValueError("Application JSON must contain an object")
        local_sensitive_allowed = args.allow_sensitive_local and "03-正式资料" in application_path.parts
        result = validate_application_fields(
            data,
            require_confirmed=args.require_confirmed,
            allow_sensitive_local=local_sensitive_allowed,
            field_schema=field_schema,
            snapshot_root=project_root_for_application(application_path),
        )
        if args.output:
            root = material_root_for(application_path).resolve()
            output = ensure_within_root(root, args.output)
            write_json(output, result)
            result["outputs"] = [relative_posix(output, root)]
        return emit_json(result)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, json.JSONDecodeError) as exc:
        result = make_result("validate_application_fields", "ERROR", "Application field validation failed")
        result["findings"] = [make_finding("APPLICATION_FIELD_VALIDATION_ERROR", "ERROR", ".", str(exc))]
        return emit_json(result)


if __name__ == "__main__":
    raise SystemExit(main())
