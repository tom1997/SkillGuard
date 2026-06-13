from __future__ import annotations

import argparse
from pathlib import Path

from skillguard.core.lockfile import create_lock, verify_lock
from skillguard.core.scanner import Scanner
from skillguard.core.thresholds import should_fail
from skillguard.reporters.json import JsonReporter
from skillguard.reporters.lockfile import LockReporter
from skillguard.reporters.terminal import TerminalReporter

FAIL_ON_CHOICES = ("never", "info", "low", "medium", "high", "critical")


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
    scan.add_argument(
        "--fail-on",
        choices=FAIL_ON_CHOICES,
        default="high",
        help="Exit with code 1 when findings meet or exceed this severity.",
    )

    scan_all = subparsers.add_parser("scan-all", help="Discover and scan Skill directories below a root.")
    scan_all.add_argument("target", type=Path, help="Root path containing one or more Skill directories.")
    scan_all.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    scan_all.add_argument(
        "--fail-on",
        choices=FAIL_ON_CHOICES,
        default="high",
        help="Exit with code 1 when findings meet or exceed this severity.",
    )

    lock = subparsers.add_parser("lock", help="Create a SkillGuard permission lockfile for one Skill.")
    lock.add_argument("target", type=Path, help="Path to the Skill directory to lock.")
    lock.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Lockfile path. Defaults to <skill-dir>/skillguard.lock.",
    )
    lock.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )

    verify = subparsers.add_parser("verify", help="Compare current Skill permissions against a lockfile.")
    verify.add_argument("target", type=Path, help="Path to the Skill directory to verify.")
    verify.add_argument(
        "--lockfile",
        type=Path,
        default=None,
        help="Lockfile path. Defaults to <skill-dir>/skillguard.lock.",
    )
    verify.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    verify.add_argument(
        "--fail-on",
        choices=("never", "added", "risk"),
        default="added",
        help="Exit with code 1 on added capabilities, any risk change, or never.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "scan":
        result = Scanner().scan(args.target)
        reporter = JsonReporter() if args.format == "json" else TerminalReporter()
        print(reporter.render(result))
        return 1 if should_fail(result, args.fail_on) else 0

    if args.command == "scan-all":
        result = Scanner().scan_all(args.target)
        reporter = JsonReporter() if args.format == "json" else TerminalReporter()
        print(reporter.render(result))
        return 1 if should_fail(result, args.fail_on) else 0

    if args.command == "lock":
        payload = create_lock(args.target, args.output)
        if args.format == "json":
            import json

            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(LockReporter().render_lock_created(payload))
        return 0

    if args.command == "verify":
        result = verify_lock(args.target, args.lockfile)
        if args.format == "json":
            import json

            print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        else:
            print(LockReporter().render_verification(result))
        if args.fail_on == "never":
            return 0
        if args.fail_on == "risk":
            return 1 if result.changed else 0
        return 1 if result.has_added_capabilities else 0

    parser.error(f"Unknown command: {args.command}")
    return 2
