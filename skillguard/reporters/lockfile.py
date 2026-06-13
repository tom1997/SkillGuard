from __future__ import annotations

from skillguard.core.lockfile import VerificationResult


class LockReporter:
    def render_lock_created(self, payload: dict) -> str:
        return "\n".join(
            [
                "SkillGuard lockfile created",
                f"Target: {payload['target']}",
                f"Risk score: {payload['risk']['score']}/100 - {payload['risk']['label'].upper()}",
                f"Capabilities locked: {len(payload['capabilities'])}",
            ]
        )

    def render_verification(self, result: VerificationResult) -> str:
        lines = [
            "SkillGuard Lock Verification",
            f"Target: {result.target}",
            f"Lockfile: {result.lockfile}",
            f"Risk score: {result.previous_score}/100 -> {result.current_score}/100",
            f"Risk label: {result.previous_label.upper()} -> {result.current_label.upper()}",
            "",
        ]

        if not result.added and not result.removed:
            lines.append("Permission diff: no capability changes")
            return "\n".join(lines)

        if result.added:
            lines.append("New capabilities since lock:")
            for change in result.added:
                lines.append(f"+ {change.kind}.{change.access}: {change.resource}")
                evidence = change.evidence[0] if change.evidence else None
                if evidence:
                    location = evidence.get("file", "unknown")
                    if evidence.get("start_line"):
                        location += f":{evidence['start_line']}"
                    lines.append(f"  Evidence: {location}")
            lines.append("")

        if result.removed:
            lines.append("Removed capabilities since lock:")
            for change in result.removed:
                lines.append(f"- {change.kind}.{change.access}: {change.resource}")
            lines.append("")

        if result.added:
            lines.append("Recommendation: review before update or execution.")
        return "\n".join(lines).rstrip()
