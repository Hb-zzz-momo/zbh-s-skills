"""CLI for deterministic responsibility-based file placement."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from structure_core import configure_utf8_stdio, error_payload, status_exit_code, suggest_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Recommend one justified project-relative path without creating it."
    )
    parser.add_argument("root", help="Existing project root whose conventions should be preserved.")
    parser.add_argument("--artifact", required=True, help="Artifact responsibility, for example frontend-feature.")
    parser.add_argument("--name", required=True, help="File, directory, or research-step name.")
    parser.add_argument("--owner", help="Feature, domain, package, or test owner.")
    parser.add_argument(
        "--application",
        help="Owning app name under apps/ when a monorepo has multiple candidates.",
    )
    parser.add_argument("--scope", choices=("local", "shared"), default="local")
    parser.add_argument("--sequence", type=int, help="Explicit sequence for a research-step suggestion.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    try:
        payload = suggest_path(
            args.root,
            artifact=args.artifact,
            name=args.name,
            owner=args.owner,
            scope=args.scope,
            sequence=args.sequence,
            application=args.application,
        )
    except Exception as exc:
        payload = error_payload(exc)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return status_exit_code(str(payload.get("status", "ERROR")))


if __name__ == "__main__":
    raise SystemExit(main())
