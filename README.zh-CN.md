# SkillGuard

[English](README.md) | [简体中文](README.zh-CN.md)

SkillGuard 是一个面向 Agent Skill 的、以权限为中心的安全扫描器。

> 在安装之前，看清一个 Agent Skill 到底能访问什么。

Agent Skill 不只是提示词，它还可能包含自然语言指令、脚本、依赖清单和安装逻辑。SkillGuard 会在安装或使用之前扫描这些内容，并输出可验证证据，包括规则 ID、文件位置、命中片段、推断出的权限能力以及修复建议。

## 复制给你的智能体

把下面这句话发给你的编码智能体，让它安装 SkillGuard：

```text
请帮我安装 SkillGuard：https://raw.githubusercontent.com/tom1997/SkillGuard/main/docs/install.md
```

然后把目标 Skill 交给它：

```text
用 SkillGuard 在安装前扫描这个 Skill：<path-or-repo>
```

## 项目状态

SkillGuard 目前处于早期开源阶段。当前 `v0.1` 主要聚焦本地 Skill 目录的静态扫描，支持终端文本和 JSON 两种输出格式。

## 为什么要审核 Agent Skill

一个 Skill 不是单纯的文档。它可以要求 Agent 执行本地脚本、读取文件、调用 API、安装依赖，甚至修改配置。一个有价值的安全审核不应该只回答“看起来可不可疑”，还应该回答：

- 它看起来需要哪些权限。
- 它引用了哪些敏感文件、环境变量、命令和网络目标。
- 哪些发现带有可复现的文件和行号证据。
- 它是否包含高置信度的提示注入、数据外传、危险执行或供应链风险模式。
- 用户输入或本地数据是否出现在网络写入附近。

## 快速开始

```bash
python -m pip install -e ".[dev]"
skillguard scan examples/benign-skill
skillguard scan examples/exfiltration-skill --format json
skillguard scan-all examples
```

也可以不安装，直接运行：

```bash
python -m skillguard scan examples/exfiltration-skill
python -m skillguard scan examples/fake-search-exfiltration-skill
python -m skillguard scan-all examples --format json
```

## 智能体使用方法

SkillGuard 不只是给人类在终端里使用，也可以被 Codex、Claude Code、OpenClaw 等智能体作为本地 CLI 调用。

推荐智能体流程：

1. 在工作区克隆或安装本仓库。
2. 如果 `skillguard` 命令不可用，先运行 `python -m pip install -e ".[dev]"`。
3. 审核单个 Skill：运行 `python -m skillguard scan <skill-dir> --format json`。
4. 审核 Skill 集合：运行 `python -m skillguard scan-all <skills-root> --format json`。
5. 读取 JSON summary，再决定是否建议用户安装、升级或执行。
6. high 或 critical 发现必须明确提示用户确认。

本仓库也自带一个可安装的智能体 Skill：`skills/skillguard-auditor/SKILL.md`。完整说明见 [docs/agent-usage.zh-CN.md](docs/agent-usage.zh-CN.md)。

## 真实样本 Smoke Test

`skills.sh` 将 Skills 描述为 AI Agent 可复用的能力，并列出了适用于 Claude Code、Codex、GitHub Copilot、Cursor 等智能体的热门公开 Skill 仓库。SkillGuard 已经用其中一小组公开样本做过 smoke test：

| 来源 | 命令 | 结果 |
| --- | --- | --- |
| `vercel-labs/skills` | `skillguard scan-all <checkout>` | 扫描 1 个 Skill，0 个发现 |
| `mattpocock/skills` | `skillguard scan-all <checkout>` | 扫描 29 个 Skills，0 个发现 |

这些结果是 smoke test，不是安全背书或完整审计。它们用于调规则、压误报，并展示 SkillGuard 在真实 Skill 集合上的行为。详情见 [docs/real-world-smoke-tests.md](docs/real-world-smoke-tests.md)。

## 输出示例

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

如果一个目录下有多个 Skill，可以使用 `scan-all`：

```text
SkillGuard Skill Set Report
Target: examples
Skills scanned: 4
Highest risk score: 100/100 - CRITICAL

Findings: 3 critical, 5 high, 5 medium, 0 low, 0 info

Per-skill summary:
  CRITICAL 100/100   6 findings  examples/exfiltration-skill
  HIGH      60/100   3 findings  examples/prompt-injection-skill
  HIGH      30/100   2 findings  examples/fake-search-exfiltration-skill
```

## Permission-First 模型

SkillGuard 把“权限”视为核心产品表面。所有发现最终都会汇总成一个能力清单：

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

`v0.1` 只做静态扫描，不执行目标 Skill，也不使用 LLM 来直接给出最终高危结论。

数据流发现是启发式证据。它表示潜在用户输入或本地数据出现在网络写入附近，需要智能体或审核者继续判断这种行为是否符合 Skill 声称的用途。

## 规则格式

规则文件位于 `skillguard/rules/**/*.yml`，设计目标是易读、易扩展、易社区贡献：

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

当前规则类别包括：

- `prompt`：指令覆盖、隐瞒行为、敏感请求、删除审计记录
- `shell`：远程脚本执行、`eval`、`sudo`、危险删除、历史记录清理
- `python`：敏感 home 目录、环境变量访问、HTTP 外传、shell subprocess
- `javascript`：`process.env`、子进程执行、HTTP 调用、敏感路径访问
- `supply-chain`：未锁定依赖、远程安装器、Docker `latest`
- `dataflow`：识别用户输入/本地数据到网络请求的 source 与 sink 证据
- `permissions`：从安全证据推断权限需求

## 路线图

- `v0.2`：GitHub URL 扫描、SARIF 输出、GitHub Action、ignore 注释、增强依赖分析。
- `v0.3`：Docker 沙箱、fake secrets、文件和网络行为观测、`lock` 与 `verify`。
- 后续：Codex/Claude Skill 适配器、VS Code 集成、权限策略生成、最小权限执行。

## 参与方式

- 贡献指南：[CONTRIBUTING.md](CONTRIBUTING.md)
- 安全策略：[SECURITY.md](SECURITY.md)
- 行为准则：[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- 规则编写说明：[docs/rules.md](docs/rules.md)
