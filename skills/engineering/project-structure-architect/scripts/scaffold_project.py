"""CLI for additive project scaffolding and numbered research-step creation."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from structure_core import (
    BLUEPRINT_IDS,
    StructureError,
    add_research_step,
    configure_utf8_stdio,
    error_payload,
    scaffold_project,
    status_exit_code,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create a project blueprint additively, or append one numbered research step. "
            "Existing files are never overwritten."
        )
    )
    parser.add_argument("target", help="Target project root.")
    parser.add_argument("--blueprint", choices=BLUEPRINT_IDS, help="Blueprint for a new project.")
    parser.add_argument("--project-name", help="Human-readable project name for a new project.")
    parser.add_argument("--package-name", help="Python/package identifier; derived when omitted.")
    parser.add_argument(
        "--technology",
        action="append",
        default=[],
        help="Exact required technology label; repeat for multiple technologies.",
    )
    parser.add_argument(
        "--shared-contracts",
        action="store_true",
        help="Create the optional shared contracts boundary when supported.",
    )
    parser.add_argument(
        "--allow-existing",
        action="store_true",
        help="Add only missing scaffold content to a non-empty target; preserve every existing file.",
    )
    parser.add_argument(
        "--with-infrastructure",
        action="store_true",
        help="Explicitly create blueprint entries conditional on with_infrastructure.",
    )
    parser.add_argument(
        "--enable-option",
        action="append",
        default=[],
        metavar="NAME",
        help="Enable a blueprint conditional by name; repeat for multiple options.",
    )
    parser.add_argument(
        "--add-step",
        metavar="NAME",
        help="Runtime mode: append a numbered research step to the existing target.",
    )
    parser.add_argument(
        "--step-number",
        type=int,
        help="Explicit step number for --add-step; default is max existing number plus one.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Return planned additions without writing.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    try:
        if args.add_step:
            if (
                args.blueprint
                or args.project_name
                or args.package_name
                or args.shared_contracts
                or args.allow_existing
                or args.with_infrastructure
                or args.technology
                or args.enable_option
            ):
                raise StructureError(
                    "--add-step cannot be combined with new-project blueprint options.",
                    "CONFLICTING_OPTIONS",
                )
            payload = add_research_step(
                args.target,
                args.add_step,
                sequence=args.step_number,
                dry_run=args.dry_run,
            )
        else:
            if args.step_number is not None:
                raise StructureError("--step-number requires --add-step.", "CONFLICTING_OPTIONS")
            if not args.blueprint or not args.project_name:
                raise StructureError(
                    "--blueprint and --project-name are required for new-project scaffolding.",
                    "MISSING_REQUIRED_OPTION",
                )
            payload = scaffold_project(
                args.target,
                blueprint_id=args.blueprint,
                project_name=args.project_name,
                package_name=args.package_name,
                shared_contracts=args.shared_contracts,
                allow_existing=args.allow_existing,
                dry_run=args.dry_run,
                with_infrastructure=args.with_infrastructure,
                technology_stack=args.technology,
                enabled_options=args.enable_option,
            )
    except Exception as exc:
        payload = error_payload(exc)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return status_exit_code(str(payload.get("status", "ERROR")))


if __name__ == "__main__":
    raise SystemExit(main())
