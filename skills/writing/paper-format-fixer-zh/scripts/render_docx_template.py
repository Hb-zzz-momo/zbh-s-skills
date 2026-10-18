#!/usr/bin/env python3
"""Render a docxtpl Word template with JSON data."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_docxtpl():
    try:
        from docxtpl import DocxTemplate
    except ImportError:
        print("Missing dependency: docxtpl. Install with: python -m pip install docxtpl", file=sys.stderr)
        raise SystemExit(2)
    return DocxTemplate


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a .docx template using docxtpl and JSON data.")
    parser.add_argument("--template", required=True, help="Template .docx path")
    parser.add_argument("--data", required=True, help="JSON data path")
    parser.add_argument("--out", required=True, help="Output .docx path")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing output file")
    parser.add_argument("--autoescape", action="store_true", help="Enable XML autoescaping during render")
    args = parser.parse_args()

    template_path = Path(args.template)
    data_path = Path(args.data)
    out_path = Path(args.out)
    if not template_path.exists():
        print(f"Template not found: {template_path}", file=sys.stderr)
        return 2
    if not data_path.exists():
        print(f"Data file not found: {data_path}", file=sys.stderr)
        return 2
    if out_path.exists() and not args.overwrite:
        print(f"Output already exists: {out_path}. Use --overwrite to replace it.", file=sys.stderr)
        return 2
    if template_path.suffix.lower() != ".docx" or out_path.suffix.lower() != ".docx":
        print("Template and output must be .docx files.", file=sys.stderr)
        return 2

    DocxTemplate = load_docxtpl()
    data = json.loads(data_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        print("JSON data must be an object at the top level.", file=sys.stderr)
        return 2

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = DocxTemplate(str(template_path))
    doc.render(data, autoescape=args.autoescape)
    doc.save(str(out_path))
    print(str(out_path.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
