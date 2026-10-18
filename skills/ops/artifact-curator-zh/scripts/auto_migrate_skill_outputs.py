#!/usr/bin/env python
"""Move legacy-flat skill-outputs (root-level) into skill-outputs/<skill-name>/.

Only touches direct children of <root>/skill-outputs/. Writes a manifest CSV.
Reserved top-level dirs: _curation, _archive. Existing skill buckets (name*-zh) are skipped as targets only; their contents are not moved by this script.

Usage:
  python auto_migrate_skill_outputs.py --root <project> --dry-run
  python auto_migrate_skill_outputs.py --root <project> --apply
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
from datetime import datetime
from pathlib import Path


RESERVED = {"_curation", "_archive", ".git"}
MANIFEST_PREFIX = "_auto_migrate_manifest"
# Top-level directory that is already a skill bucket: <something>-zh
SKILL_DIR_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-zh$", re.IGNORECASE)

# (full_match_prefix_including_skill_and_underscore, skill_group_index)
# Order: most specific first.
LEGACY_PATTERNS: list[tuple[re.Pattern[str], int]] = [
    (re.compile(r"^(\d{8}_\d{6})_([a-z0-9-]+-zh)_(.+)$", re.IGNORECASE), 2),
    (re.compile(r"^(\d{8}_\d{4})_([a-z0-9-]+-zh)_(.+)$", re.IGNORECASE), 2),
    (re.compile(r"^(\d{8})_(\d+)_([a-z0-9-]+-zh)_(.+)$", re.IGNORECASE), 3),
    (re.compile(r"^(\d{8})_([a-z0-9-]+-zh)_(.+)$", re.IGNORECASE), 2),
]


def parse_skill_slug(entry_name: str) -> str | None:
    base = entry_name[:-4] if entry_name.endswith(".md") else entry_name
    for pat, skill_idx in LEGACY_PATTERNS:
        m = pat.match(base)
        if m:
            return m.group(skill_idx).lower()
    return None


def rewrite_md_refs(root: Path, pairs: list[tuple[str, str]]) -> int:
    """Replace old relative paths with new in *.md under root. Returns number of files modified."""
    if not pairs:
        return 0
    skip_parts = {".git", "__pycache__", ".venv", "node_modules", "_curation"}
    changed = 0
    for md in root.rglob("*.md"):
        if any(p in skip_parts for p in md.parts):
            continue
        try:
            text = md.read_text(encoding="utf-8")
        except OSError:
            continue
        new = text
        for old, newp in pairs:
            old_f = old.replace("\\", "/")
            new_f = newp.replace("\\", "/")
            new = new.replace(old_f, new_f)
            new = new.replace(old_f.replace("/", "\\"), newp.replace("/", "\\"))
        if new != text:
            md.write_text(new, encoding="utf-8")
            changed += 1
    return changed


def collect_moves(skill_root: Path) -> list[tuple[Path, Path, str]]:
    moves: list[tuple[Path, Path, str]] = []
    for child in sorted(skill_root.iterdir(), key=lambda p: p.name.lower()):
        name = child.name
        if name in RESERVED or name.startswith(".") or name.startswith(MANIFEST_PREFIX):
            continue
        if child.is_dir() and SKILL_DIR_RE.match(name):
            continue
        skill = parse_skill_slug(name)
        if not skill:
            continue
        dest_dir = skill_root / skill
        dest = dest_dir / name
        moves.append((child, dest, skill))
    return moves


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate legacy skill-outputs into per-skill folders.")
    parser.add_argument("--root", type=Path, default=Path("."), help="Project root")
    parser.add_argument("--dry-run", action="store_true", help="Print planned moves only (default if neither flag)")
    parser.add_argument("--apply", action="store_true", help="Execute moves immediately (no交互确认)")
    parser.add_argument(
        "--no-rewrite-md",
        action="store_true",
        help="With --apply: do not rewrite *.md references from old rel paths to new (default is to rewrite)",
    )
    args = parser.parse_args()
    if args.apply and args.dry_run:
        print("[auto_migrate] use only one of --apply or --dry-run")
        return 2
    if not args.apply:
        args.dry_run = True
    root: Path = args.root.resolve()
    skill_root = root / "skill-outputs"
    if not skill_root.is_dir():
        print(f"[auto_migrate] missing {skill_root}")
        return 1

    moves = collect_moves(skill_root)

    rows: list[dict[str, str]] = []
    for src, dest, skill in moves:
        rows.append(
            {
                "skill": skill,
                "src": str(src.relative_to(root)).replace("\\", "/"),
                "dest": str(dest.relative_to(root)).replace("\\", "/"),
                "status": "planned",
            }
        )

    if args.dry_run:
        for r in rows:
            print(f"DRY-RUN  {r['src']}  ->  {r['dest']}")
        print(f"[auto_migrate] planned={len(rows)} (no files changed; no manifest written)")
        return 0

    # --apply
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    manifest = skill_root / f"{MANIFEST_PREFIX}_{ts}.csv"
    for src, dest, skill in moves:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            for r in rows:
                if r["src"] == str(src.relative_to(root)).replace("\\", "/"):
                    r["status"] = "skipped_dest_exists"
            print(f"SKIP exists: {dest}")
            continue
        shutil.move(str(src), str(dest))
        for r in rows:
            if r["src"] == str(src.relative_to(root)).replace("\\", "/"):
                r["status"] = "moved"
        print(f"MOVED  {src.name}  ->  {dest}")

    with manifest.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["skill", "src", "dest", "status"])
        w.writeheader()
        w.writerows(rows)

    pairs = [(r["src"], r["dest"]) for r in rows if r["status"] == "moved"]
    if pairs and not args.no_rewrite_md:
        n = rewrite_md_refs(root, pairs)
        print(f"[auto_migrate] rewritten_md_files={n}")
    elif args.no_rewrite_md:
        print("[auto_migrate] skip md rewrite (--no-rewrite-md)")

    print(f"[auto_migrate] done moves={sum(1 for r in rows if r['status']=='moved')} manifest={manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
