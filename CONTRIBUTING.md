# Contributing to SkillGuard

Thanks for helping improve SkillGuard.

## Development Setup

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

## Project Areas

- `skillguard/core`: models, rule loading, scanner orchestration
- `skillguard/reporters`: terminal and JSON output
- `skillguard/rules`: built-in detection rules
- `examples`: sample Skills used as fixtures and demos
- `tests`: regression coverage

## Contribution Guidelines

- Prefer high-confidence detections over broad but noisy matches.
- Add or update tests for every new rule or behavior change.
- Keep rule IDs stable once published.
- Keep CLI output machine-friendly and predictable.
- Use ASCII unless a file already uses another character set.

## Rule Contributions

When adding a rule:

1. Add a YAML file under the appropriate `skillguard/rules/` category.
2. Include a clear `message` and `remediation`.
3. Add a fixture under `examples/` if needed.
4. Add or update tests in `tests/`.

## Pull Requests

Please include:

- a short summary of the change
- why the change is needed
- test coverage for the new behavior
- any limitations or follow-up work

Small, focused pull requests are easier to review and merge.
