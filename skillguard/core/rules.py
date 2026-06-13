from __future__ import annotations

from pathlib import Path

import yaml

from skillguard.core.models import Rule, Severity


def default_rules_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "rules"


def load_rules(rules_dir: Path | None = None) -> list[Rule]:
    root = rules_dir or default_rules_dir()
    rules: list[Rule] = []
    for path in sorted(root.rglob("*.yml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not data:
            continue
        try:
            rules.append(
                Rule(
                    id=str(data["id"]),
                    title=str(data["title"]),
                    severity=Severity(str(data["severity"]).lower()),
                    category=str(data["category"]),
                    languages=tuple(data.get("languages", [])),
                    regex=str(data["match"]["regex"]),
                    message=str(data.get("message", data["title"])),
                    remediation=str(data.get("remediation", "")),
                    capability_templates=tuple(data.get("capabilities", [])),
                )
            )
        except KeyError as exc:
            raise ValueError(f"Invalid rule {path}: missing {exc}") from exc
    return rules
