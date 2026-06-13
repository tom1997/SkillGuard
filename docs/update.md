# Update SkillGuard

You are updating SkillGuard for the user.

## Goal

Pull the latest repository changes, reinstall if needed, run tests, and verify the CLI still works.

## Steps

1. Locate the existing SkillGuard checkout.

```bash
cd SkillGuard
```

2. Check local changes before pulling.

```bash
git status --short
```

If there are user changes, do not overwrite them. Explain the situation and ask before modifying those files.

3. Pull the latest version.

```bash
git pull --ff-only
```

4. Reinstall in editable mode.

```bash
python -m pip install -e ".[dev]"
```

5. Verify tests and CLI.

```bash
python -m pytest
python -m skillguard scan-all examples
```

## Agent Reporting

After updating, report:

- current branch and latest commit
- whether tests passed
- whether CLI verification passed
- any local changes that were preserved

Do not execute unknown target Skill code. SkillGuard is a static scanner.
