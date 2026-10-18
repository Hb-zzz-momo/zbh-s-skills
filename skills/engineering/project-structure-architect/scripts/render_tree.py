"""CLI for deterministic, generated-content-free tree rendering."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from structure_core import configure_utf8_stdio, error_payload, render_tree, status_exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a sorted project tree while excluding generated directories."
    )
    parser.add_argument("root", help="Existing project root to render.")
    parser.add_argument("--max-depth", type=int, default=4, help="Maximum directory depth (default: 4).")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="NAME",
        help="Additional exact directory/file name to exclude; repeat as needed.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    try:
        payload = {
            "status": "PASS",
            "root": args.root,
            "max_depth": args.max_depth,
            "tree": render_tree(args.root, max_depth=args.max_depth, exclude=args.exclude),
        }
    except Exception as exc:
        payload = error_payload(exc)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return status_exit_code(str(payload.get("status", "ERROR")))


if __name__ == "__main__":
    raise SystemExit(main())
