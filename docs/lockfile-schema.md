# SkillGuard Lockfile Schema

SkillGuard lockfiles capture the permission baseline of a reviewed Agent Skill.

Default path:

```text
<skill-dir>/skillguard.lock
```

Create a lockfile:

```bash
skillguard lock ./skill
```

Compare a later version:

```bash
skillguard diff ./skill
```

## Top-Level Fields

```json
{
  "lockfile_version": 1,
  "skillguard_version": "0.1.0",
  "created_at": "2026-06-13T00:00:00+00:00",
  "target": "./skill",
  "content_hash": "sha256:...",
  "risk": {},
  "capabilities": [],
  "required_capabilities": {}
}
```

## `risk`

Risk summarizes the scan result at the time the user trusted the Skill.

```json
{
  "score": 30,
  "label": "high",
  "max_severity": "high",
  "finding_counts": {
    "critical": 0,
    "high": 1,
    "medium": 1,
    "low": 0,
    "info": 0
  }
}
```

## `capabilities`

Capabilities are the normalized permission facts used for diffing.

```json
[
  {
    "kind": "network",
    "access": "connect",
    "resource": "collector.example",
    "evidence": [
      {
        "file": "scripts/search.py",
        "start_line": 9,
        "end_line": 9,
        "snippet": "requests.post(...)",
        "explanation": "Python code sends outbound HTTP data."
      }
    ]
  }
]
```

Current capability kinds:

- `filesystem`
- `network`
- `command`
- `environment`
- `privilege`

## `required_capabilities`

This is a grouped summary for humans and agents. It is not the source of truth for diffs; `capabilities` is.

```json
{
  "filesystem": {
    "sensitive": ["~/.ssh/**"]
  },
  "network": ["collector.example"],
  "commands": ["bash"],
  "environment": ["GITHUB_TOKEN"],
  "privileged": false
}
```

## Compatibility

Consumers should check `lockfile_version`. Future versions may add fields, but existing fields should remain stable within the same lockfile version.
