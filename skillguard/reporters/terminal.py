from __future__ import annotations

from skillguard.core.models import BatchScanResult, Finding, ScanResult, Severity


class TerminalReporter:
    def render(self, result: BatchScanResult | ScanResult) -> str:
        if isinstance(result, BatchScanResult):
            return self._render_batch(result)
        return self._render_scan(result)

    def _render_scan(self, result: ScanResult) -> str:
        counts = result.finding_counts()
        lines = [
            "SkillGuard Security Report",
            f"Target: {result.target}",
            f"Risk score: {result.score}/100 - {result.risk_label}",
            "",
            "Findings: "
            f"{counts[Severity.CRITICAL.value]} critical, "
            f"{counts[Severity.HIGH.value]} high, "
            f"{counts[Severity.MEDIUM.value]} medium, "
            f"{counts[Severity.LOW.value]} low, "
            f"{counts[Severity.INFO.value]} info",
        ]
        if result.findings:
            lines.append("")
            for finding in result.findings:
                lines.extend(self._render_finding(finding))
                lines.append("")
        if result.dataflow_signals:
            lines.extend(self._render_dataflow_signals(result))
        lines.extend(self._render_capabilities(result))
        return "\n".join(lines).rstrip()

    def _render_batch(self, result: BatchScanResult) -> str:
        counts = result.finding_counts()
        lines = [
            "SkillGuard Skill Set Report",
            f"Target: {result.target}",
            f"Skills scanned: {len(result.results)}",
            f"Highest risk score: {result.score}/100 - {result.risk_label}",
            "",
            "Findings: "
            f"{counts[Severity.CRITICAL.value]} critical, "
            f"{counts[Severity.HIGH.value]} high, "
            f"{counts[Severity.MEDIUM.value]} medium, "
            f"{counts[Severity.LOW.value]} low, "
            f"{counts[Severity.INFO.value]} info",
            "",
            "Per-skill summary:",
        ]
        if not result.results:
            lines.append("  no Skill directories found")
            return "\n".join(lines)

        for scan_result in sorted(result.results, key=lambda item: (-item.score, str(item.target))):
            finding_count = len(scan_result.findings)
            lines.append(
                f"  {scan_result.risk_label:8} {scan_result.score:3}/100 "
                f"{finding_count:3} findings  {scan_result.target}"
            )
            top_findings = sorted(
                scan_result.findings,
                key=lambda item: (-self._severity_rank(item.severity), item.rule_id),
            )[:3]
            for finding in top_findings:
                evidence = finding.evidence[0] if finding.evidence else None
                location = evidence.file.as_posix() if evidence else "unknown"
                if evidence and evidence.start_line:
                    location += f":{evidence.start_line}"
                lines.append(f"    - {finding.severity.value.upper()} {finding.rule_id} {location}")
        return "\n".join(lines)

    def _render_finding(self, finding: Finding) -> list[str]:
        lines = [
            f"{finding.severity.value.upper()} {finding.rule_id} {finding.title}",
        ]
        for evidence in finding.evidence:
            location = evidence.file.as_posix()
            if evidence.start_line:
                location += f":{evidence.start_line}"
            lines.append(f"  {location}")
            if evidence.snippet:
                lines.append(f"  {evidence.snippet}")
        lines.append(f"  {finding.message}")
        if finding.remediation:
            lines.append(f"  Remediation: {finding.remediation}")
        return lines

    def _render_capabilities(self, result: ScanResult) -> list[str]:
        summary = result.capabilities_summary()
        lines = ["", "Required capabilities:"]
        if not result.capabilities:
            lines.append("  none inferred")
            return lines

        filesystem = summary.get("filesystem", {})
        for access, resources in filesystem.items():
            lines.append(f"  filesystem.{access}:")
            for resource in resources:
                lines.append(f"    - {resource}")
        for resource in summary.get("network", []):
            if "  network.connect:" not in lines:
                lines.append("  network.connect:")
            lines.append(f"    - {resource}")
        for resource in summary.get("commands", []):
            if "  command.execute:" not in lines:
                lines.append("  command.execute:")
            lines.append(f"    - {resource}")
        for resource in summary.get("environment", []):
            if "  environment.read:" not in lines:
                lines.append("  environment.read:")
            lines.append(f"    - {resource}")
        if summary.get("privileged"):
            lines.append("  privileged: true")
        return lines

    def _render_dataflow_signals(self, result: ScanResult) -> list[str]:
        lines = ["Dataflow signals:"]
        for signal in result.dataflow_signals[:8]:
            evidence = signal.evidence
            location = evidence.file.as_posix()
            if evidence.start_line:
                location += f":{evidence.start_line}"
            lines.append(f"  {signal.kind}.{signal.label}: {location}")
        if len(result.dataflow_signals) > 8:
            lines.append(f"  ... {len(result.dataflow_signals) - 8} more")
        lines.append("")
        return lines

    def _severity_rank(self, severity: Severity) -> int:
        return {
            Severity.INFO: 0,
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4,
        }[severity]
