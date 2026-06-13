# SkillGuard

[English](README.md) | [Simplified Chinese](README.zh-CN.md)

SkillGuard locks and diffs what an Agent Skill can access before you install or update it.

> See new filesystem, network, environment, and command permissions before trust is granted.

Agent Skills can contain natural-language instructions, scripts, dependency manifests, and installation logic. SkillGuard scans those files before installation or use, reports concrete evidence, and can lock a trusted permission baseline for later verification.

## Give This to Your Agent

Ask your coding agent to install SkillGuard with one copy-paste prompt:

```text
Please install SkillGuard: https://raw.githubusercontent.com/tom1997/SkillGuard/main/docs/install.md
```

Then point it at a Skill directory:

```text
Use SkillGuard to scan this Skill before I install it: <path-or-repo>
```

## Project Status

SkillGuard is an early open source project. The current `v0.1` scope focuses on local static scanning, permission lockfiles, permission diffs, and text/JSON reporting.

## Why Agent Skills Need Auditing

A Skill is not just documentation. It can ask an agent to follow instructions, run local scripts, read files, call APIs, install dependencies, or change configuration. A useful security review should therefore answer more than "does this look suspicious?"

SkillGuard focuses on:

- What permissions the Skill appears to need.
- What sensitive files, environment variables, commands, and network targets it references.
- Which findings are backed by reproducible file and line evidence.
- Whether the Skill contains high-confidence prompt injection, exfiltration, dangerous execution, or supply-chain risk patterns.
- Whether user input or local data appears near outbound network writes.

## Quick Start

```bash
python -m pip install -e ".[dev]"
skillguard scan examples/benign-skill
skillguard scan examples/exfiltration-skill --format json
skillguard scan-all examples
skillguard lock examples/benign-skill
skillguard diff examples/benign-skill
```

You can also run without installation:

```bash
python -m skillguard scan examples/exfiltration-skill
python -m skillguard scan examples/fake-search-exfiltration-skill
python -m skillguard scan-all examples --format json
```

## AI Agent Usage

SkillGuard is designed to be called by agents as a local CLI, not only by humans in a terminal.

Recommended agent flow:

1. Clone or install this repository in the workspace.
2. Run `python -m pip install -e ".[dev]"` if the `skillguard` command is not available.
3. For one Skill, run `python -m skillguard scan <skill-dir> --format json`.
4. For a Skill collection, run `python -m skillguard scan-all <skills-root> --format json`.
5. Parse the JSON summary before recommending install, update, or execution.
6. Treat high or critical findings as requiring explicit user review.

This repository also includes an installable agent Skill at `skills/skillguard-auditor/SKILL.md`. See [docs/agent-usage.md](docs/agent-usage.md) for copy-ready instructions.

## Permission Lockfiles

Use `lock` after reviewing a Skill you trust:

```bash
skillguard lock ./some-skill
```

This creates `skillguard.lock` with the current content hash, risk summary, inferred capabilities, and evidence-backed permission baseline.

After the Skill changes, run:

```bash
skillguard diff ./some-skill
```

Diff reports newly added or removed capabilities:

```text
Added capabilities:
+ network.connect: telemetry.example
  Evidence: scripts/sync.py:42

Review added capabilities before install, update, or execution.
```

The lockfile schema is documented in [docs/lockfile-schema.md](docs/lockfile-schema.md).

## Real-World Smoke Tests

`skills.sh` describes Skills as reusable capabilities for AI agents and lists popular public Skill repositories across Claude Code, Codex, GitHub Copilot, Cursor, and other agents. SkillGuard was tested against a small public sample from that ecosystem:

| Source | Command | Result |
| --- | --- | --- |
| `vercel-labs/skills` | `skillguard scan-all <checkout>` | 1 Skill scanned, 0 findings |
| `mattpocock/skills` | `skillguard scan-all <checkout>` | 29 Skills scanned, 0 findings |

These are smoke tests, not endorsements or full security audits. They help tune false positives and show how SkillGuard behaves on real Skill collections. See [docs/real-world-smoke-tests.md](docs/real-world-smoke-tests.md).

## Example Report

```text
SkillGuard Security Report
Target: examples/exfiltration-skill
Risk score: 100/100 - CRITICAL

Findings: 2 critical, 0 high, 1 medium, 0 low, 0 info

CRITICAL SG-PY-001 Sensitive SSH material referenced
  scripts/collect.py:5
  Path.home() / ".ssh" / "id_rsa"
  Reads or references SSH private key material.
  Remediation: Avoid reading SSH keys. Restrict file access to the skill workspace.

Required capabilities:
  filesystem.sensitive.read:
    - ~/.ssh/**
  network.connect:
    - attacker.example
```

For a directory containing multiple Skills, use `scan-all`:

```text
SkillGuard Skill Set Report
Target: examples
Skills scanned: 5
Highest risk score: 100/100 - CRITICAL

Findings: 3 critical, 6 high, 7 medium, 0 low, 0 info

Per-skill summary:
  CRITICAL 100/100   6 findings  examples/exfiltration-skill
  HIGH      60/100   3 findings  examples/prompt-injection-skill
  HIGH      30/100   2 findings  examples/fake-search-exfiltration-skill
```

## Permission-First Security Model

SkillGuard treats permissions as the primary product surface. Findings contribute to a generated capability summary:

```yaml
required_capabilities:
  filesystem:
    read:
      - "./**"
    sensitive:
      - "~/.ssh/**"
      - "~/.aws/**"
  network:
    - "api.github.com"
  commands:
    - "bash"
    - "python"
  environment:
    - "GITHUB_TOKEN"
  privileged: false
```

The v0.1 scanner is static. It does not execute target Skill code and does not use an LLM for final decisions.

Dataflow findings are heuristic. They show that potential input or local data appears near outbound network writes, so an agent or reviewer should verify whether the behavior matches the Skill's stated purpose.

## Rule Format

Rules live in `skillguard/rules/**/*.yml` and are intentionally easy to contribute:

```yaml
id: SG-SHELL-001
title: Remote script executed through shell
severity: high
category: dangerous-execution
languages:
  - shell
match:
  regex: 'curl\s+[^|]+\|\s*(bash|sh)'
message: Remote content is executed directly by a shell.
remediation: Download the script, pin its version, verify checksum, and require explicit user approval.
capabilities:
  - kind: command
    access: execute
    resource: bash
```

Current rule categories:

- `prompt`: instruction override, concealed action, secret requests, audit deletion
- `shell`: remote shell execution, `eval`, `sudo`, destructive deletion, shell history clearing
- `python`: sensitive home paths, environment access, HTTP exfiltration, shell subprocess
- `javascript`: `process.env`, child process execution, HTTP calls, sensitive home paths
- `supply-chain`: unpinned packages, remote installers, Docker `latest`
- `dataflow`: source and sink evidence for possible user/local data sent to network requests
- `permissions`: capability inference from security evidence

## Roadmap

- `v0.2`: GitHub URL scanning, SARIF output, GitHub Action, ignore comments, richer dependency parsing.
- `v0.3`: Docker sandbox, fake secrets, observed filesystem/network behavior, richer permission policies.
- Later: Codex/Claude Skill adapter, VS Code integration, policy generation, runtime least-privilege execution.

## Contributing Rules

Add focused, high-confidence rules with:

- stable `SG-*` IDs
- clear severity
- precise regex
- user-facing message
- actionable remediation
- capability hints when the match implies permissions

Please include a test fixture when adding a new rule category.

## Community

- Contribution guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security policy: [SECURITY.md](SECURITY.md)
- Code of conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- Rule authoring notes: [docs/rules.md](docs/rules.md)
