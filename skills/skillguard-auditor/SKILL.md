# SkillGuard Auditor

Use this Skill when the user asks to audit, review, scan, install-check, or compare Agent Skills for safety.

SkillGuard Auditor is a wrapper around the local `skillguard` CLI. It should not decide safety from natural-language inspection alone. It must call the scanner, read structured results, and explain concrete evidence.

The scanner is deterministic and evidence-first. The agent is responsible for second-pass review: interpreting whether the evidence matches the Skill's claimed purpose, spotting likely false positives, and asking the user before risky install or execution.

## When to Use

Use this Skill for:

- auditing a single local Skill directory
- auditing a directory that contains multiple Skills
- checking a Skill before install, update, or execution
- summarizing required capabilities and risky behavior
- comparing scan results before and after a Skill change

## Required Tool Behavior

Before giving a safety recommendation:

1. Locate the target path.
2. Prefer JSON output.
3. Run one of:

```bash
python -m skillguard scan <skill-dir> --format json
python -m skillguard scan-all <skills-root> --format json
```

If the `skillguard` command is installed, this is also acceptable:

```bash
skillguard scan <skill-dir> --format json
skillguard scan-all <skills-root> --format json
```

## Reporting Rules

When reporting to the user:

- Start with the overall risk label and score.
- Say how many Skills were scanned when using `scan-all`.
- List high and critical findings first.
- Include file path, line number, rule ID, and plain-language explanation.
- Summarize inferred capabilities, especially network, command execution, privileged behavior, sensitive filesystem access, and environment access.
- Review `dataflow_signals` and `SG-FLOW-001` findings carefully. These indicate possible movement from user input, local files, or environment data into outbound network requests.
- For fake search, fake storage, telemetry, diagnostics, upload, sync, or memory Skills, explicitly compare the claimed purpose with network sinks and payload-like variables.
- Treat high and critical findings as requiring explicit user review.
- Explain likely false positives kindly and clearly.

## Safety Rules

- Do not execute target Skill code during review.
- Do not paste long matched snippets unless the user asks.
- Do not reveal real local secret values.
- Do not install or update a target Skill unless the user explicitly confirms after reviewing findings.
- Static scan evidence should be described as risk evidence, not proof of malicious intent.
- Do not declare a Skill safe only because there are no prompt-injection findings. Check network, filesystem, environment, command, and dataflow evidence.

## Recommended Output Shape

For one Skill:

```text
Risk: HIGH, 70/100
Target: path/to/skill

Key findings:
- SG-PY-003 at scripts/example.py:79: outbound HTTP request
- SG-FLOW-001 at scripts/example.py:41 and scripts/example.py:79: possible user/local data sent to network

Inferred capabilities:
- network: external-network
- environment: model and provider configuration

Recommendation: review before install or execution.
```

For many Skills:

```text
Scanned: 20 Skills
Highest risk: HIGH, 70/100

Needs review:
- image-analyzer: SG-PY-003 at scripts/analyze_image.py:79

No blocking findings:
- agent-guide
- skill-manager
```
