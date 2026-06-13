# Install SkillGuard

You are installing SkillGuard for the user.

SkillGuard is a permission-first security scanner for Agent Skills. It provides a CLI and an optional agent-facing Skill wrapper.

## Goal

Install SkillGuard in the current workspace, verify it works, and show the user how to scan one Skill or a Skill collection.

## Steps

1. Clone the repository if it is not already present.

```bash
git clone https://github.com/tom1997/SkillGuard.git
cd SkillGuard
```

2. If the repository is already present, enter it instead.

```bash
cd SkillGuard
```

3. Install in editable mode.

```bash
python -m pip install -e ".[dev]"
```

4. Verify the test suite.

```bash
python -m pytest
```

5. Verify the CLI.

```bash
python -m skillguard scan examples/benign-skill
python -m skillguard scan-all examples
```

6. If the user has a local Skill collection, scan it with JSON output.

```bash
python -m skillguard scan-all <skills-root> --format json
```

## Agent Reporting

After installation, report:

- install location
- whether tests passed
- whether CLI verification passed
- the exact command the user can run next

Do not execute unknown target Skill code. SkillGuard is a static scanner.
