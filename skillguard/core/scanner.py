from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

from skillguard.core.models import BatchScanResult, Capability, DataFlowSignal, Evidence, Finding, Rule, ScanResult, Severity
from skillguard.core.rules import load_rules


LANGUAGE_BY_SUFFIX = {
    ".md": "prompt",
    ".markdown": "prompt",
    ".txt": "prompt",
    ".yml": "config",
    ".yaml": "config",
    ".json": "config",
    ".toml": "config",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".ps1": "powershell",
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "javascript",
    ".tsx": "javascript",
}

SPECIAL_FILE_LANGUAGES = {
    "Dockerfile": "dockerfile",
    "package.json": "supply-chain",
    "requirements.txt": "supply-chain",
    "pyproject.toml": "supply-chain",
    "Pipfile": "supply-chain",
}

URL_RE = re.compile(r"https?://[^\s'\"`>)]+")
ENV_RE = re.compile(r"\b(?:process\.env\.|os\.environ(?:\.get\()?[\[('\"]*)([A-Z][A-Z0-9_]{2,})")
GENERIC_ENV_RE = re.compile(r"\$\{([A-Z][A-Z0-9_]{2,})\}|\b([A-Z][A-Z0-9_]*(?:API_KEY|TOKEN|SECRET|PASSWORD)[A-Z0-9_]*)\b")
USER_INPUT_RE = re.compile(
    r"\b(input|user_input|prompt|message|query|question|content|payload|data|args?|argv|stdin|form|body|params?)\b",
    re.IGNORECASE,
)
LOCAL_SOURCE_RE = re.compile(
    r"(\.read_text\(|open\(|readFileSync|fs\.readFile|cat\s+|os\.environ|process\.env|~\/\.ssh|~\/\.aws|\.env\b)",
    re.IGNORECASE,
)
NETWORK_WRITE_RE = re.compile(
    r"(requests|httpx)\.(post|put|patch)\s*\(|fetch\s*\(|axios\.(post|put|patch)\s*\(|curl\b.*\b(-d|--data|--data-binary|--form|-F|POST)\b",
    re.IGNORECASE,
)


class Scanner:
    def __init__(self, rules: list[Rule] | None = None) -> None:
        self.rules = rules or load_rules()

    def scan(self, target: Path) -> ScanResult:
        root = target.resolve()
        if not root.exists():
            raise FileNotFoundError(f"Target does not exist: {target}")
        if root.is_file():
            files = [root]
            base = root.parent
        else:
            files = [path for path in root.rglob("*") if path.is_file() and not self._is_ignored(path)]
            base = root

        findings: list[Finding] = []
        dataflow_signals: list[DataFlowSignal] = []
        for path in files:
            languages = self._languages_for(path)
            if not languages:
                continue
            text = self._read_text(path)
            if text is None:
                continue
            rel_path = path.relative_to(base)
            for rule in self.rules:
                if not set(rule.languages).intersection(languages):
                    continue
                findings.extend(self._apply_rule(rule, rel_path, text))
            extra_findings, extra_signals = self._analyze_dataflow(rel_path, text, languages)
            findings.extend(extra_findings)
            dataflow_signals.extend(extra_signals)

        capabilities = self._dedupe_capabilities(
            [capability for finding in findings for capability in finding.capabilities]
        )
        return ScanResult(
            target=target,
            findings=findings,
            capabilities=capabilities,
            dataflow_signals=dataflow_signals,
        )

    def scan_all(self, target: Path) -> BatchScanResult:
        root = target.resolve()
        if not root.exists():
            raise FileNotFoundError(f"Target does not exist: {target}")
        skill_dirs = self.discover_skill_dirs(root)
        return BatchScanResult(target=target, results=[self.scan(path) for path in skill_dirs])

    def discover_skill_dirs(self, target: Path) -> list[Path]:
        root = target.resolve()
        if root.is_file():
            return [root.parent] if root.name == "SKILL.md" else []
        if (root / "SKILL.md").is_file():
            return [root]
        skill_files = [
            path
            for path in root.rglob("SKILL.md")
            if path.is_file() and not self._is_ignored(path)
        ]
        return sorted({path.parent for path in skill_files})

    def _apply_rule(self, rule: Rule, path: Path, text: str) -> list[Finding]:
        findings: list[Finding] = []
        compiled = re.compile(rule.regex, re.IGNORECASE)
        for line_no, line in enumerate(text.splitlines(), start=1):
            if not compiled.search(line):
                continue
            evidence = Evidence(
                file=path,
                start_line=line_no,
                end_line=line_no,
                snippet=line.strip(),
                explanation=rule.message,
            )
            capabilities = self._capabilities_for(rule, line, evidence)
            findings.append(
                Finding(
                    rule_id=rule.id,
                    title=rule.title,
                    category=rule.category,
                    severity=rule.severity,
                    confidence=0.9,
                    evidence=[evidence],
                    message=rule.message,
                    remediation=rule.remediation,
                    capabilities=capabilities,
                )
            )
        return findings

    def _capabilities_for(self, rule: Rule, line: str, evidence: Evidence) -> list[Capability]:
        capabilities: list[Capability] = []
        for template in rule.capability_templates:
            resource = template.get("resource", "")
            if resource == "$HOST":
                resource = self._host_from_line(line) or "external-network"
            elif resource == "$ENV":
                resource = self._env_from_line(line) or "environment"
            capabilities.append(
                Capability(
                    kind=template.get("kind", "unknown"),
                    access=template.get("access", "use"),
                    resource=resource,
                    evidence=(evidence,),
                )
            )
        return capabilities

    def _analyze_dataflow(
        self, path: Path, text: str, languages: set[str]
    ) -> tuple[list[Finding], list[DataFlowSignal]]:
        if not languages.intersection({"python", "javascript", "shell"}):
            return [], []

        source_signals: list[DataFlowSignal] = []
        sink_signals: list[DataFlowSignal] = []
        lines = text.splitlines()

        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            is_network_write = NETWORK_WRITE_RE.search(line)
            if USER_INPUT_RE.search(line) and not is_network_write:
                source_signals.append(
                    DataFlowSignal(
                        kind="source",
                        label="user-input",
                        evidence=Evidence(
                            file=path,
                            start_line=line_no,
                            end_line=line_no,
                            snippet=stripped,
                            explanation="Potential user-controlled input source.",
                        ),
                    )
                )
            if LOCAL_SOURCE_RE.search(line):
                source_signals.append(
                    DataFlowSignal(
                        kind="source",
                        label="local-or-sensitive-data",
                        evidence=Evidence(
                            file=path,
                            start_line=line_no,
                            end_line=line_no,
                            snippet=stripped,
                            explanation="Potential local file, environment, or sensitive data source.",
                        ),
                    )
                )
            if is_network_write:
                sink_signals.append(
                    DataFlowSignal(
                        kind="sink",
                        label="network-write",
                        evidence=Evidence(
                            file=path,
                            start_line=line_no,
                            end_line=line_no,
                            snippet=stripped,
                            explanation="Potential outbound network write sink.",
                        ),
                    )
                )

        if not source_signals or not sink_signals:
            return [], source_signals + sink_signals

        first_source = source_signals[0]
        first_sink = sink_signals[0]
        evidence = [first_source.evidence, first_sink.evidence]
        capability = Capability(
            kind="network",
            access="connect",
            resource=self._host_from_line(first_sink.evidence.snippet or "") or "external-network",
            evidence=(first_sink.evidence,),
        )
        finding = Finding(
            rule_id="SG-FLOW-001",
            title="Potential data flow to outbound network request",
            category="dataflow",
            severity=Severity.MEDIUM,
            confidence=0.65,
            evidence=evidence,
            message="The same file contains a potential user/local data source and an outbound network write.",
            remediation="Verify what data is sent, document the destination, and require user confirmation before transmitting user input or local data.",
            capabilities=[capability],
        )
        return [finding], source_signals + sink_signals

    def _languages_for(self, path: Path) -> set[str]:
        languages: set[str] = set()
        if path.name in SPECIAL_FILE_LANGUAGES:
            languages.add(SPECIAL_FILE_LANGUAGES[path.name])
        if path.name == "SKILL.md":
            languages.add("prompt")
        suffix_language = LANGUAGE_BY_SUFFIX.get(path.suffix)
        if suffix_language:
            languages.add(suffix_language)
        if path.suffix in {".yml", ".yaml"} and ".github" in path.parts:
            languages.add("supply-chain")
        if "install" in path.stem.lower():
            languages.add("supply-chain")
        return languages

    def _read_text(self, path: Path) -> str | None:
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                return path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                return None

    def _is_ignored(self, path: Path) -> bool:
        ignored = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv"}
        return any(part in ignored for part in path.parts)

    def _host_from_line(self, line: str) -> str | None:
        match = URL_RE.search(line)
        if not match:
            return None
        return urlparse(match.group(0)).netloc or None

    def _env_from_line(self, line: str) -> str | None:
        match = ENV_RE.search(line)
        if match:
            return match.group(1)
        generic_match = GENERIC_ENV_RE.search(line)
        if not generic_match:
            return None
        return generic_match.group(1) or generic_match.group(2)

    def _dedupe_capabilities(self, capabilities: list[Capability]) -> list[Capability]:
        deduped: dict[tuple[str, str, str], Capability] = {}
        for capability in capabilities:
            key = capability.key()
            if key not in deduped:
                deduped[key] = capability
        return sorted(deduped.values(), key=lambda item: item.key())
