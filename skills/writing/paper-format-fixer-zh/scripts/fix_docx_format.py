#!/usr/bin/env python3
"""Conservatively fix formatting in a Word .docx paper."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt, RGBColor
except ImportError:  # pragma: no cover
    print("Missing dependency: python-docx. Install with: python -m pip install python-docx", file=sys.stderr)
    raise SystemExit(2)


ALIGNMENTS = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}


def parse_rgb(value: str | None) -> RGBColor | None:
    if value is None:
        return None
    normalized = str(value).strip().lstrip("#")
    if normalized.lower() in {"none", "false", "off"}:
        return None
    if len(normalized) != 6:
        raise ValueError(f"Invalid RGB color: {value}")
    return RGBColor(int(normalized[0:2], 16), int(normalized[2:4], 16), int(normalized[4:6], 16))


def load_rules(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    if not path.exists():
        raise FileNotFoundError(f"Rules file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_can_write(path: Path, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {path}. Use --overwrite to replace it.")
    path.parent.mkdir(parents=True, exist_ok=True)


def set_east_asia_font(element: Any, font_name: str) -> None:
    r_pr = element.get_or_add_rPr()
    r_fonts = r_pr.rFonts
    if r_fonts is None:
        r_fonts = OxmlElement("w:rFonts")
        r_pr.append(r_fonts)
    r_fonts.set(qn("w:eastAsia"), font_name)


def apply_style_rule(style: Any, rule: dict[str, Any]) -> None:
    if "font_name" in rule:
        style.font.name = rule["font_name"]
    if "east_asia_font" in rule:
        set_east_asia_font(style._element, rule["east_asia_font"])
    if "font_size_pt" in rule:
        style.font.size = Pt(float(rule["font_size_pt"]))
    if "bold" in rule:
        style.font.bold = bool(rule["bold"])
    if "italic" in rule:
        style.font.italic = bool(rule["italic"])
    if "font_color" in rule:
        color = parse_rgb(rule["font_color"])
        if color is not None:
            style.font.color.rgb = color

    fmt = style.paragraph_format
    if "line_spacing" in rule:
        fmt.line_spacing = float(rule["line_spacing"])
    if "space_before_pt" in rule:
        fmt.space_before = Pt(float(rule["space_before_pt"]))
    if "space_after_pt" in rule:
        fmt.space_after = Pt(float(rule["space_after_pt"]))
    if "first_line_indent_cm" in rule:
        fmt.first_line_indent = Cm(float(rule["first_line_indent_cm"]))
    if "left_indent_cm" in rule:
        fmt.left_indent = Cm(float(rule["left_indent_cm"]))
    if "right_indent_cm" in rule:
        fmt.right_indent = Cm(float(rule["right_indent_cm"]))
    if "alignment" in rule:
        alignment = ALIGNMENTS.get(str(rule["alignment"]).lower())
        if alignment is not None:
            fmt.alignment = alignment


def apply_page_rules(doc: Any, page_rule: dict[str, Any]) -> int:
    changed = 0
    mapping = {
        "top_cm": "top_margin",
        "bottom_cm": "bottom_margin",
        "left_cm": "left_margin",
        "right_cm": "right_margin",
        "header_cm": "header_distance",
        "footer_cm": "footer_distance",
    }
    for section in doc.sections:
        for key, attr in mapping.items():
            if key in page_rule:
                setattr(section, attr, Cm(float(page_rule[key])))
                changed += 1
    return changed


def collapse_blank_paragraphs(doc: Any) -> int:
    from journal_profile import has_payload
    removed = 0
    previous_blank = False
    for paragraph in list(doc.paragraphs):
        is_blank = not has_payload(paragraph)
        if is_blank and previous_blank:
            element = paragraph._element
            element.getparent().remove(element)
            removed += 1
            continue
        previous_blank = is_blank
    return removed


def normalize_abnormal_run_sizes(doc: Any, rule: dict[str, Any]) -> int:
    min_pt = float(rule.get("min_pt", 6))
    max_pt = float(rule.get("max_pt", 36))
    replacement = Pt(float(rule.get("replacement_pt", 12)))
    changed = 0
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            if not run.text.strip() or run.font.size is None:
                continue
            size = run.font.size.pt
            if size < min_pt or size > max_pt:
                run.font.size = replacement
                changed += 1
    return changed


def iter_all_paragraphs(doc: Any):
    from journal_profile import iter_paragraphs
    for _, paragraph in iter_paragraphs(doc):
        yield paragraph


def force_font_color(doc: Any, color_value: str | None = "000000") -> dict[str, Any]:
    from journal_profile import iter_runs
    color = parse_rgb(color_value)
    if color is None:
        return {"enabled": False, "runs_seen": 0, "runs_changed": 0, "styles_changed": 0, "color": None}
    styles_changed = 0
    for style in doc.styles:
        try:
            if style.font.color.rgb != color:
                styles_changed += 1
            style.font.color.rgb = color
        except Exception:
            continue
    runs_seen = 0
    runs_changed = 0
    for paragraph in iter_all_paragraphs(doc):
        for run in iter_runs(paragraph):
            if not run.text.strip():
                continue
            runs_seen += 1
            if run.font.color.rgb != color:
                runs_changed += 1
            run.font.color.rgb = color
    return {"enabled": True, "runs_seen": runs_seen, "runs_changed": runs_changed, "styles_changed": styles_changed, "color": str(color)}


def apply_table_style(doc: Any, style_name: str) -> int:
    changed = 0
    for table in doc.tables:
        try:
            table.style = style_name
            changed += 1
        except KeyError:
            continue
    return changed


def fix_docx(input_path: Path, out_path: Path, rules: dict[str, Any], overwrite: bool) -> dict[str, Any]:
    from journal_profile import content_signature
    if input_path.resolve() == out_path.resolve():
        raise ValueError("Use a separate output path; in-place modification is disabled")
    ensure_can_write(out_path, overwrite)
    doc = Document(str(input_path))
    original_content = content_signature(doc)
    summary = {
        "input": str(input_path.resolve()),
        "output": str(out_path.resolve()),
        "page_properties_changed": 0,
        "styles_changed": [],
        "blank_paragraphs_removed": 0,
        "abnormal_run_sizes_changed": 0,
        "font_color": {},
        "tables_styled": 0,
        "mode": "rules" if rules else "conservative-default",
    }

    if "page" in rules:
        summary["page_properties_changed"] = apply_page_rules(doc, rules["page"])

    for style_name, rule in rules.get("styles", {}).items():
        try:
            style = doc.styles[style_name]
        except KeyError:
            continue
        apply_style_rule(style, rule)
        summary["styles_changed"].append(style_name)

    if rules.get("collapse_blank_paragraphs", True):
        summary["blank_paragraphs_removed"] = collapse_blank_paragraphs(doc)

    run_font_rule = rules.get("run_font", {"min_pt": 6, "max_pt": 36, "replacement_pt": 12})
    summary["abnormal_run_sizes_changed"] = normalize_abnormal_run_sizes(doc, run_font_rule)

    color_value = rules.get("force_font_color", run_font_rule.get("font_color", "000000"))
    summary["font_color"] = force_font_color(doc, color_value)

    if "table_style" in rules:
        summary["tables_styled"] = apply_table_style(doc, str(rules["table_style"]))

    if content_signature(doc) != original_content:
        raise ValueError("Formatting changed document text or media")
    doc.save(str(out_path))
    if content_signature(Document(str(out_path))) != original_content:
        raise ValueError("Saved output changed document text or media")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Conservatively fix formatting in a .docx paper.")
    parser.add_argument("--input", required=True, help="Input .docx path")
    parser.add_argument("--rules", help="Optional JSON rules path")
    parser.add_argument("--out", required=True, help="Output .docx path")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing output file")
    parser.add_argument("--profile", help="Journal profile JSON; cannot be combined with --rules")
    parser.add_argument("--map", help="Semantic paragraph map and table overrides JSON")
    parser.add_argument("--report", help="Save machine-readable summary JSON")
    args = parser.parse_args()

    input_path = Path(args.input)
    out_path = Path(args.out)
    rules_path = Path(args.rules) if args.rules else None
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 2
    if input_path.suffix.lower() != ".docx" or out_path.suffix.lower() != ".docx":
        print("Input and output must be .docx files.", file=sys.stderr)
        return 2

    try:
        if args.profile and args.rules:
            raise ValueError("Choose either --profile or legacy --rules")
        if args.profile:
            from journal_profile import load_profile, format_file
            mapping = load_rules(Path(args.map)) if args.map else None
            summary = format_file(input_path, out_path, load_profile(args.profile), mapping, args.overwrite)
        else:
            rules = load_rules(rules_path)
            summary = fix_docx(input_path, out_path, rules, args.overwrite)
    except Exception as exc:
        print(f"Failed: {exc}", file=sys.stderr)
        return 1
    if args.report:
        from journal_profile import write_json
        write_json(args.report, summary)
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return 1 if summary.get("conformance", {}).get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
