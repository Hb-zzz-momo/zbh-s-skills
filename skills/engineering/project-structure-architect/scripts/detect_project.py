"""CLI for conservative project blueprint detection."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from structure_core import configure_utf8_stdio, detect_project, error_payload, status_exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detect the closest project-structure blueprint and print JSON evidence."
    )
    parser.add_argument("root", help="Existing project root to inspect.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    try:
        payload = detect_project(args.root)
    except Exception as exc:  # The CLI always exposes the stable JSON error contract.
        payload = error_payload(exc)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return status_exit_code(str(payload.get("status", "ERROR")))


if __name__ == "__main__":
    raise SystemExit(main())
