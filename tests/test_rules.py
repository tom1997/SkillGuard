from pathlib import Path

from skillguard.core.rules import load_rules


def test_builtin_rules_load() -> None:
    rules = load_rules()
    ids = {rule.id for rule in rules}

    assert "SG-PROMPT-001" in ids
    assert "SG-PROMPT-005" in ids
    assert "SG-SHELL-001" in ids
    assert "SG-PY-003" in ids
    assert "SG-JS-002" in ids
    assert all(rule.regex for rule in rules)


def test_rule_ids_are_unique() -> None:
    rules = load_rules()
    ids = [rule.id for rule in rules]

    assert len(ids) == len(set(ids))
