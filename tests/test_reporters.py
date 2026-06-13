import json
from pathlib import Path

from skillguard.core.scanner import Scanner
from skillguard.reporters.json import JsonReporter
from skillguard.reporters.terminal import TerminalReporter

ROOT = Path(__file__).resolve().parents[1]


def test_json_report_is_machine_parseable() -> None:
    result = Scanner().scan(ROOT / "examples" / "exfiltration-skill")
    payload = json.loads(JsonReporter().render(result))

    assert payload["risk"]["score"] > 0
    assert payload["findings"]
    assert payload["required_capabilities"]["network"]


def test_text_report_includes_core_fields() -> None:
    result = Scanner().scan(ROOT / "examples" / "exfiltration-skill")
    report = TerminalReporter().render(result)

    assert "SkillGuard Security Report" in report
    assert "Risk score:" in report
    assert "SG-PY-001" in report
    assert "Required capabilities:" in report


def test_batch_json_report_is_machine_parseable() -> None:
    result = Scanner().scan_all(ROOT / "examples")
    payload = json.loads(JsonReporter().render(result))

    assert payload["summary"]["skills_scanned"] == 5
    assert payload["summary"]["blocking"] is True
    assert payload["results"]


def test_batch_text_report_includes_per_skill_summary() -> None:
    result = Scanner().scan_all(ROOT / "examples")
    report = TerminalReporter().render(result)

    assert "SkillGuard Skill Set Report" in report
    assert "Skills scanned: 5" in report
    assert "Per-skill summary:" in report
    assert "exfiltration-skill" in report
