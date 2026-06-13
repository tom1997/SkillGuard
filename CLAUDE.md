# SkillGuard Agent Context

## Project

SkillGuard is a Python CLI and rules engine for auditing Agent Skills before install or execution.

Positioning: permission-first security scanner for Agent Skills. It answers what a Skill appears to access, what risky behavior is evidenced, and whether a user should review before install.

## Main Commands

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m skillguard scan examples/benign-skill
python -m skillguard scan-all examples --format json
```

## Architecture

- `skillguard/cli/main.py`: CLI entrypoint for `scan` and `scan-all`
- `skillguard/core/models.py`: findings, evidence, capabilities, scan results, batch results
- `skillguard/core/scanner.py`: file discovery, rule application, capability extraction
- `skillguard/core/rules.py`: YAML rule loading
- `skillguard/reporters`: text and JSON renderers
- `skillguard/rules`: built-in YAML rules
- `skills/skillguard-auditor`: installable Agent Skill wrapper

## Development Rules

- Keep detections high-confidence.
- Avoid executing target Skill code.
- Add tests for new rules and reporter behavior.
- Keep JSON output stable for agents and CI.
- Prefer evidence-backed findings over broad claims.

## Current Limits

- Static scanning only.
- No GitHub URL scanning yet.
- No SARIF output yet.
- No dynamic sandbox yet.
- Some prompt rules may need tuning as real-world Skills are scanned.
