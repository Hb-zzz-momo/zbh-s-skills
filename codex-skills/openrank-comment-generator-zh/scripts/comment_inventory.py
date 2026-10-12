#!/usr/bin/env python3
"""Scan openrank2 files and report comment coverage targets."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PY_DEF = re.compile(r"^(?P<indent>\s*)(def|class)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
JS_FUNC = re.compile(r"^(?P<indent>\s*)(async\s+function|function)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
JS_CONST_FUNC = re.compile(
    r"^(?P<indent>\s*)const\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*"
    r"((async\s*)?\([^)]*\)\s*=>|computed\s*\(|watch\s*\(|defineStore\s*\()"
)
ROUTE = re.compile(r"^\s*@\w+_bp\.route\(")
CHINESE = re.compile(r"[\u4e00-\u9fff]")


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def has_chinese_near(lines: list[str], index: int, window: int = 3) -> bool:
    start = max(0, index - window)
    nearby = "\n".join(lines[start:index])
    return bool(CHINESE.search(nearby))


def has_module_comment(lines: list[str], suffix: str) -> bool:
    head = "\n".join(lines[:12])
    if suffix == ".py":
        return ('"""' in head and bool(CHINESE.search(head))) or bool(
            lines and lines[0].lstrip().startswith("#") and CHINESE.search(lines[0])
        )
    if suffix == ".vue":
        return ("<!--" in head and bool(CHINESE.search(head))) or bool(
            "/**" in head and CHINESE.search(head)
        )
    return bool(CHINESE.search(head) and ("//" in head or "/*" in head))


def iter_code_files(root: Path):
    ignored = {"node_modules", ".git", "__pycache__", "dist", "build", ".venv"}
    for path in root.rglob("*"):
        if any(part in ignored for part in path.parts):
            continue
        if path.suffix in {".py", ".js", ".vue", ".css"}:
            yield path


def scan_file(path: Path, root: Path) -> dict:
    text = read_text(path)
    lines = text.splitlines()
    rel = path.relative_to(root).as_posix()
    result = {
        "file": rel,
        "module_comment": has_module_comment(lines, path.suffix),
        "targets": [],
    }

    pending_route = False
    for idx, line in enumerate(lines):
        if ROUTE.match(line):
            pending_route = True
            continue

        if path.suffix == ".py":
            match = PY_DEF.match(line)
        else:
            match = JS_FUNC.match(line) or JS_CONST_FUNC.match(line)
        if not match:
            continue

        name = match.group("name")
        result["targets"].append({
            "line": idx + 1,
            "name": name,
            "kind": "route" if pending_route else "symbol",
            "has_chinese_comment": has_chinese_near(lines, idx),
        })
        pending_route = False

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan openrank2 comment coverage.")
    parser.add_argument("--root", default=".", help="Project root, default: current directory")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text summary")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    reports = [scan_file(path, root) for path in iter_code_files(root)]

    if args.json:
        print(json.dumps(reports, ensure_ascii=False, indent=2))
        return 0

    for report in reports:
        missing = [t for t in report["targets"] if not t["has_chinese_comment"]]
        if report["module_comment"] and not missing:
            continue
        print(f"\n{report['file']}")
        print(f"  module_comment: {'yes' if report['module_comment'] else 'NO'}")
        for target in missing:
            print(
                f"  line {target['line']}: {target['kind']} {target['name']} "
                "needs nearby Chinese comment"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
