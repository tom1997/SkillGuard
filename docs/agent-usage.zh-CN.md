# 智能体使用方法

SkillGuard 可以被允许运行本地命令的 AI 智能体直接调用。

推荐集成流程：

1. 智能体拿到一个 Skill 路径、Skill 集合路径，或一个仓库 checkout。
2. 智能体在本地运行 SkillGuard。
3. 智能体读取 JSON 输出。
4. 智能体向用户解释风险、权限和证据。
5. 用户信任某个 Skill 后，智能体创建权限锁文件。
6. 更新或再次使用前，智能体验证权限漂移。
7. 如果存在 high、critical 或新增权限，安装、更新或执行前必须让用户明确确认。

## 在智能体工作区安装

在 SkillGuard 仓库根目录运行：

```bash
python -m pip install -e ".[dev]"
```

如果不想安装，也可以直接通过模块运行：

```bash
python -m skillguard scan examples/benign-skill --format json
python -m skillguard scan-all examples --format json
python -m skillguard lock examples/benign-skill
python -m skillguard diff examples/benign-skill
```

## 扫描单个 Skill

```bash
python -m skillguard scan /path/to/skill --format json
```

智能体应该总结：

- 风险分数和风险等级
- 是否存在阻断级发现
- 按严重程度排序的关键发现
- 推断出的权限能力
- 数据流信号，尤其是用户输入或本地数据可能流向网络 sink 的情况
- 修复建议

## 扫描 Skill 集合

```bash
python -m skillguard scan-all /path/to/skills-root --format json
```

SkillGuard 会自动发现包含 `SKILL.md` 的目录，并分别扫描。

## 锁定并验证权限

审核后创建权限基线：

```bash
python -m skillguard lock /path/to/skill
```

后续版本用锁文件验证：

```bash
python -m skillguard diff /path/to/skill --format json
```

即使整体扫描分数没有变化，只要出现新增权限，智能体也应该提示用户复核。

## 推荐智能体策略

- 审核期间不要执行目标 Skill 的代码。
- 除非用户要求，不要输出很长的命中片段。
- 不要把真实本地密钥值粘贴到对话里。
- high 和 critical 发现需要用户明确复核。
- `verify` 发现新增权限时需要用户明确复核。
- 看到 `SG-FLOW-001` 时，需要检查 Skill 声称的用途和实际发送的数据是否一致。
- 解释清楚：静态扫描发现是证据，不等于证明恶意。
- 自动化场景优先使用 JSON 输出，人类阅读场景使用 text 输出。

## 可安装的智能体 Skill

本仓库包含一个 Skill 包装器：

```text
skills/skillguard-auditor/SKILL.md
```

支持本地 Skill 目录的智能体可以安装或引用这个目录。该 Skill 会指示智能体调用 SkillGuard CLI、解析结果，并解释目标 Skill 是否适合安装或运行。
