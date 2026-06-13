# AI Agent Usage

SkillGuard can be used directly by AI agents that are allowed to run local commands.

The recommended integration pattern is simple:

1. The agent receives a Skill path, a Skill collection path, or a repository checkout.
2. The agent runs SkillGuard locally.
3. The agent reads JSON output.
4. The agent explains risk, capabilities, and evidence to the user.
5. The agent asks for explicit confirmation before install, update, or execution when high-risk findings exist.

## Install for Agent Workspaces

From the SkillGuard repository root:

```bash
python -m pip install -e ".[dev]"
```

If installation is not desired, agents can call the module directly:

```bash
python -m skillguard scan examples/benign-skill --format json
python -m skillguard scan-all examples --format json
```

## Scan One Skill

```bash
python -m skillguard scan /path/to/skill --format json
```

Use this when the agent already knows the target Skill directory.

The agent should summarize:

- risk score and label
- blocking status
- top findings by severity
- inferred capabilities
- dataflow signals, especially possible user/local data sent to network sinks
- remediation suggestions

## Scan a Skill Collection

```bash
python -m skillguard scan-all /path/to/skills-root --format json
```

Use this for directories that contain many Skill directories. SkillGuard discovers directories containing `SKILL.md` and scans each one separately.

## Recommended Agent Policy

- Do not execute target Skill code during review.
- Do not print long matched snippets unless the user asks.
- Do not paste real local secret values into the conversation.
- Treat high and critical findings as requiring explicit user review.
- Treat `SG-FLOW-001` as a reason to inspect whether the Skill's claimed purpose matches the data being sent.
- Explain that static findings are evidence, not proof of malicious intent.
- Prefer JSON output for automation and text output for human-readable summaries.

## Installable Agent Skill

This repository includes a Skill wrapper at:

```text
skills/skillguard-auditor/SKILL.md
```

Agents that support local Skill directories can install or reference that directory. The Skill instructs the agent to call the SkillGuard CLI, parse the result, and explain whether the target Skill appears safe to install or run.
