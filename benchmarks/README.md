# Benchmarks

This directory tracks small, repeatable SkillGuard benchmark sets.

The goal is not to claim broad security coverage. The goal is to make false positives, known malicious fixtures, and permission drift behavior visible.

## Current Fixture Groups

| Group | Source | Purpose |
| --- | --- | --- |
| Benign examples | `examples/benign-skill` | Should not produce high or critical findings |
| Prompt injection | `examples/prompt-injection-skill` | Should detect instruction override and concealment |
| Exfiltration | `examples/exfiltration-skill` | Should detect sensitive file access and outbound network writes |
| Fake search exfiltration | `examples/fake-search-exfiltration-skill` | Should detect user input near outbound network write |
| Supply chain risk | `examples/supply-chain-risk-skill` | Should detect unpinned dependencies and Docker latest |

## Local Benchmark Command

```bash
python -m pytest
python -m skillguard scan-all examples --fail-on critical
```

`scan-all examples --fail-on critical` is expected to exit with code `1` because the malicious fixtures intentionally contain critical findings.

## Next Benchmark Targets

- Public benign Skill collections from `skills.sh`
- Public OpenClaw Skill examples
- Known malicious fixtures generated for prompt injection, rug pull, and data exfiltration
- Comparison runs against other open-source scanners where licenses and tooling allow it
