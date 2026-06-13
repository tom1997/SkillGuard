from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


SEVERITY_ORDER = {
    Severity.INFO: 0,
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}

SEVERITY_SCORE = {
    Severity.INFO: 0,
    Severity.LOW: 3,
    Severity.MEDIUM: 10,
    Severity.HIGH: 20,
    Severity.CRITICAL: 40,
}


@dataclass(frozen=True)
class Evidence:
    file: Path
    start_line: int | None = None
    end_line: int | None = None
    snippet: str | None = None
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file.as_posix(),
            "start_line": self.start_line,
            "end_line": self.end_line,
            "snippet": self.snippet,
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class Capability:
    kind: str
    resource: str
    access: str
    evidence: tuple[Evidence, ...] = ()

    def key(self) -> tuple[str, str, str]:
        return (self.kind, self.access, self.resource)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "resource": self.resource,
            "access": self.access,
            "evidence": [item.to_dict() for item in self.evidence],
        }


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    severity: Severity
    category: str
    languages: tuple[str, ...]
    regex: str
    message: str
    remediation: str
    capability_templates: tuple[dict[str, str], ...] = ()


@dataclass(frozen=True)
class DataFlowSignal:
    kind: str
    label: str
    evidence: Evidence

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "label": self.label,
            "evidence": self.evidence.to_dict(),
        }


@dataclass
class Finding:
    rule_id: str
    title: str
    category: str
    severity: Severity
    confidence: float
    evidence: list[Evidence]
    message: str
    remediation: str | None = None
    capabilities: list[Capability] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "category": self.category,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "message": self.message,
            "evidence": [item.to_dict() for item in self.evidence],
            "remediation": self.remediation,
            "capabilities": [item.to_dict() for item in self.capabilities],
        }


@dataclass
class ScanResult:
    target: Path
    findings: list[Finding]
    capabilities: list[Capability]
    dataflow_signals: list[DataFlowSignal] = field(default_factory=list)

    @property
    def score(self) -> int:
        return min(100, sum(SEVERITY_SCORE[item.severity] for item in self.findings))

    @property
    def max_severity(self) -> Severity:
        if not self.findings:
            return Severity.INFO
        return max((item.severity for item in self.findings), key=lambda item: SEVERITY_ORDER[item])

    @property
    def risk_label(self) -> str:
        if self.max_severity == Severity.CRITICAL or self.score >= 90:
            return "CRITICAL"
        if self.score >= 50 or self.max_severity == Severity.HIGH:
            return "HIGH"
        if self.score >= 20 or self.max_severity == Severity.MEDIUM:
            return "MEDIUM"
        if self.score > 0:
            return "LOW"
        return "INFO"

    @property
    def has_blocking_findings(self) -> bool:
        return any(item.severity in {Severity.HIGH, Severity.CRITICAL} for item in self.findings)

    def finding_counts(self) -> dict[str, int]:
        counts = {severity.value: 0 for severity in Severity}
        for finding in self.findings:
            counts[finding.severity.value] += 1
        return counts

    def capabilities_summary(self) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "filesystem": {"read": [], "write": [], "sensitive": []},
            "network": [],
            "commands": [],
            "environment": [],
            "privileged": False,
        }
        for capability in self.capabilities:
            if capability.kind == "filesystem":
                bucket = "sensitive" if "sensitive" in capability.access else capability.access
                if bucket not in summary["filesystem"]:
                    summary["filesystem"][bucket] = []
                summary["filesystem"][bucket].append(capability.resource)
            elif capability.kind == "network":
                summary["network"].append(capability.resource)
            elif capability.kind == "command":
                summary["commands"].append(capability.resource)
            elif capability.kind == "environment":
                summary["environment"].append(capability.resource)
            elif capability.kind == "privilege":
                summary["privileged"] = True

        summary["filesystem"] = {
            key: sorted(set(value)) for key, value in summary["filesystem"].items() if value
        }
        summary["network"] = sorted(set(summary["network"]))
        summary["commands"] = sorted(set(summary["commands"]))
        summary["environment"] = sorted(set(summary["environment"]))
        return summary

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": str(self.target),
            "risk": {
                "score": self.score,
                "label": self.risk_label.lower(),
                "max_severity": self.max_severity.value,
            },
            "finding_counts": self.finding_counts(),
            "findings": [item.to_dict() for item in self.findings],
            "dataflow_signals": [item.to_dict() for item in self.dataflow_signals],
            "required_capabilities": self.capabilities_summary(),
        }


@dataclass
class BatchScanResult:
    target: Path
    results: list[ScanResult]

    @property
    def score(self) -> int:
        if not self.results:
            return 0
        return max(result.score for result in self.results)

    @property
    def max_severity(self) -> Severity:
        if not self.results:
            return Severity.INFO
        return max((result.max_severity for result in self.results), key=lambda item: SEVERITY_ORDER[item])

    @property
    def risk_label(self) -> str:
        if not self.results:
            return "INFO"
        if self.max_severity == Severity.CRITICAL or self.score >= 90:
            return "CRITICAL"
        if self.score >= 50 or self.max_severity == Severity.HIGH:
            return "HIGH"
        if self.score >= 20 or self.max_severity == Severity.MEDIUM:
            return "MEDIUM"
        if self.score > 0:
            return "LOW"
        return "INFO"

    @property
    def has_blocking_findings(self) -> bool:
        return any(result.has_blocking_findings for result in self.results)

    def finding_counts(self) -> dict[str, int]:
        counts = {severity.value: 0 for severity in Severity}
        for result in self.results:
            for severity, count in result.finding_counts().items():
                counts[severity] += count
        return counts

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": str(self.target),
            "summary": {
                "skills_scanned": len(self.results),
                "score": self.score,
                "label": self.risk_label.lower(),
                "max_severity": self.max_severity.value,
                "finding_counts": self.finding_counts(),
                "blocking": self.has_blocking_findings,
            },
            "results": [result.to_dict() for result in self.results],
        }
