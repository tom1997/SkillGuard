from pathlib import Path

from skillguard.core.scanner import Scanner

ROOT = Path(__file__).resolve().parents[1]


def test_benign_skill_has_no_high_or_critical_findings() -> None:
    result = Scanner().scan(ROOT / "examples" / "benign-skill")

    assert not result.has_blocking_findings


def test_prompt_injection_skill_reports_prompt_findings() -> None:
    result = Scanner().scan(ROOT / "examples" / "prompt-injection-skill")
    rule_ids = {finding.rule_id for finding in result.findings}

    assert "SG-PROMPT-001" in rule_ids
    assert "SG-PROMPT-002" in rule_ids
    assert "SG-PROMPT-004" in rule_ids
    assert result.has_blocking_findings


def test_exfiltration_skill_reports_evidence_and_capabilities() -> None:
    result = Scanner().scan(ROOT / "examples" / "exfiltration-skill")
    rule_ids = {finding.rule_id for finding in result.findings}
    summary = result.capabilities_summary()

    assert "SG-PY-001" in rule_ids
    assert "SG-PY-003" in rule_ids
    assert "SG-SHELL-001" in rule_ids
    assert any(
        evidence.file.as_posix() == "scripts/collect.py" and evidence.start_line
        for finding in result.findings
        for evidence in finding.evidence
    )
    assert "~/.ssh/**" in summary["filesystem"]["sensitive"]
    assert "attacker.example" in summary["network"]
    assert "bash" in summary["commands"]
    assert "GITHUB_TOKEN" in summary["environment"]


def test_supply_chain_skill_reports_unpinned_dependencies() -> None:
    result = Scanner().scan(ROOT / "examples" / "supply-chain-risk-skill")
    rule_ids = {finding.rule_id for finding in result.findings}

    assert "SG-SUPPLY-001" in rule_ids
    assert "SG-SUPPLY-002" in rule_ids
    assert "SG-SUPPLY-003" in rule_ids


def test_scan_all_discovers_skill_directories() -> None:
    result = Scanner().scan_all(ROOT / "examples")

    scanned = {path.name for path in (scan.target for scan in result.results)}
    assert scanned == {
        "benign-skill",
        "prompt-injection-skill",
        "exfiltration-skill",
        "fake-search-exfiltration-skill",
        "supply-chain-risk-skill",
    }
    assert result.has_blocking_findings
    assert result.finding_counts()["critical"] > 0
