from __future__ import annotations

import argparse
from pathlib import Path

from skillguard.core.scanner import Scanner
from skillguard.reporters.json import JsonReporter
from skillguard.reporters.terminal import TerminalReporter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skillguard",
        description="Permission-first security scanner for Agent Skills.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="Scan a local Agent Skill directory.")
    scan.add_argument("target", type=Path, help="Path to the Skill directory to scan.")
    scan.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )

    scan_all = subparsers.add_parser("scan-all", help="Discover and scan Skill directories below a root.")
    scan_all.add_argument("target", type=Path, help="Root path containing one or more Skill directories.")
    scan_all.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "scan":
        result = Scanner().scan(args.target)
        reporter = JsonReporter() if args.format == "json" else TerminalReporter()
        print(reporter.render(result))
        return 1 if result.has_blocking_findings else 0

    if args.command == "scan-all":
        result = Scanner().scan_all(args.target)
        reporter = JsonReporter() if args.format == "json" else TerminalReporter()
        print(reporter.render(result))
        return 1 if result.has_blocking_findings else 0

    parser.error(f"Unknown command: {args.command}")
    return 2
