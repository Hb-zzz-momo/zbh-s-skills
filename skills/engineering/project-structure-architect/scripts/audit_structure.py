"""CLI for read-only project-structure drift auditing."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from structure_core import (
    BLUEPRINT_IDS,
    audit_structure,
    configure_utf8_stdio,
    error_payload,
    status_exit_code,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit structural drift without moving, deleting, or rewriting project files."
    )
    parser.add_argument("root", help="Existing project root to audit.")
    parser.add_argument(
        "--blueprint",
        choices=BLUEPRINT_IDS,
        help="Expected blueprint; conflicts are reported and never auto-migrated.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    try:
        payload = audit_structure(args.root, blueprint_id=args.blueprint)
    except Exception as exc:
        payload = error_payload(exc)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return status_exit_code(str(payload.get("status", "ERROR")))


if __name__ == "__main__":
    raise SystemExit(main())
