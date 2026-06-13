# Real-World Smoke Tests

This page records lightweight smoke tests against real Agent Skill collections.

These are not endorsements, guarantees, or full security audits. They are used to check whether SkillGuard can scan real public Skill repositories without noisy false positives.

## Why These Samples

`skills.sh` describes Skills as reusable capabilities for AI agents and lists public Skill repositories across Claude Code, Codex, GitHub Copilot, Cursor, and other agent hosts.

The sample below uses visible public repositories from that ecosystem.

## Test Environment

- Date: 2026-06-13
- Scanner: SkillGuard `0.1.0`
- Mode: static scan
- Commands:

```bash
python -m skillguard scan-all <checkout>
python -m skillguard scan-all <checkout> --format json
```

## Results

| Source | Skills scanned | Critical | High | Medium | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| `vercel-labs/skills` | 1 | 0 | 0 | 0 | Public Skill collection listed on `skills.sh` |
| `mattpocock/skills` | 29 | 0 | 0 | 0 | Public Skill collection listed on `skills.sh` |

## Interpretation

SkillGuard should be treated as a triage tool:

- `INFO`: no current static findings
- `MEDIUM`: review permissions or documentation
- `HIGH`: review before install or execution
- `CRITICAL`: do not install without careful manual review

Static scanning cannot prove a Skill is safe. It can provide evidence before trust is granted.

Dataflow findings are especially important for fake search, fake storage, memory, diagnostics, sync, and upload Skills. They do not prove exfiltration by themselves, but they identify places where user input or local data may be sent to a network destination.
