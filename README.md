# ECC Manager

<p align="center">
  <img src="ecc_manager/web/logo.svg" alt="ECC Manager logo" width="96" height="96">
</p>

<p align="center">
  <a href="https://github.com/KylePowell-LABS/ecc-manager/actions/workflows/ci.yml"><img src="https://github.com/KylePowell-LABS/ecc-manager/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/ecc-manager/"><img src="https://img.shields.io/pypi/v/ecc-manager.svg" alt="PyPI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
</p>

<p align="center">
  <a href="#english">English</a> | <a href="#简体中文">简体中文</a>
</p>

## English

ECC Manager is a local capability assembler for `everything-claude-code` workflows. It reads commands, skills, agents, rules, workflows, runtime files, and profile metadata from `ECC_HOME`, then installs only the right capabilities into each project for Claude Code, Codex, and Google Antigravity.

It is designed for local-first agent workflows: preview what will be written, apply only managed files or symlinks, keep a project lock, and run Doctor checks when the project or ECC source changes.

### Why ECC Manager Exists

`everything-claude-code` is powerful, but a complete commands / skills / agents / rules library can become too large for everyday project context. Loading the whole capability set into every repo makes agent instructions heavier than necessary, increases noise, and spends context on tools the current project may never use.

ECC Manager turns that large library into a project-specific assembly flow: choose the current phase, architecture, stack fragments, and packs, then install only the Claude Code, Codex, or Google Antigravity capabilities the project actually needs. The project lock records what was installed, and Doctor checks make updates, missing sources, broken symlinks, generated files, and command readiness visible after the ECC source changes.

### Built for everything-claude-code Workflows

ECC Manager does not replace `everything-claude-code`. It sits next to it as a local Web UI and CLI for splitting, previewing, and applying ECC capabilities per project.

Use it when you want to keep a large ECC source repository in one place while giving each working project a smaller, targeted agent setup. A Next.js SaaS project can receive different commands, skills, agents, rules, and workflows from a Python API project or a code-review-only project, without copying the full upstream library into every repo.

### Tool Compatibility Matrix

| Source capability | Claude Code target | Codex target | Google Antigravity target |
| --- | --- | --- | --- |
| ECC commands | `.claude/commands/` symlinks and generated instructions | command index in `AGENTS.md` plus repo-scoped `.agents/skills/ecc-*` command skills | workflow Markdown in `.agents/workflows/` |
| ECC skills | `.claude/skills/` | `.agents/skills/` | `.agents/skills/` |
| ECC agents | `.claude/agents/` | Codex custom agent TOML in `.codex/agents/` | aggregated personas in `.agents/agents.md` |
| ECC rules | `.claude/rules/` | `.codex/rules/` and managed `AGENTS.md` context | `.agents/rules/` |
| Generated instructions | `CLAUDE.ecc.generated.md` | `AGENTS.ecc.generated.md` and managed `AGENTS.md` blocks | `ANTIGRAVITY.ecc.generated.md` and managed `AGENTS.md` blocks |
| Health and traceability | project lock plus Doctor checks | project lock plus Doctor checks | project lock plus Doctor checks |

### Web UI Screenshot

![ECC Manager English Web UI](https://raw.githubusercontent.com/KylePowell-LABS/ecc-manager/main/assets/screenshots/ecc-manager-web-en.png)

### Features

- Local Web UI bound to `127.0.0.1` by default.
- Profile-based assembly: phase + architecture + stack fragment + pack.
- Preview-before-apply flow for symlinks, generated files, optional dependencies, and target conflicts.
- Claude Code plugin-style commands, skills, agents, rules, and generated instruction files.
- Codex support through `AGENTS.md`, repo-scoped command skills, Codex custom agents, and rules.
- Google Antigravity support through `.agents/agents.md`, `.agents/skills/`, `.agents/rules/`, and `.agents/workflows/`.
- Doctor checks for missing sources, broken symlinks, generated files, legacy artifacts, and command readiness.
- Bilingual Web UI for English and Simplified Chinese.

### Install

Install from PyPI after the first release is published:

```bash
python3 -m pip install ecc-manager
```

Install from GitHub:

```bash
git clone https://github.com/KylePowell-LABS/ecc-manager.git
cd ecc-manager
python3 -m pip install .
```

Run without installing:

```bash
python3 -m ecc_manager.server
```

Create local wrapper commands:

```bash
bash scripts/install-local.sh
```

This creates:

```text
~/.local/bin/ecc-use
~/.local/bin/ecc-manager
```

Make sure `~/.local/bin` is on your `PATH`.

### Quick Start

Start the Web UI:

```bash
ecc-manager
```

The default URL is:

```text
http://127.0.0.1:8765
```

If the port is busy, ECC Manager tries the next available port. To start without opening a browser:

```bash
ecc-manager --no-open
```

To choose a port:

```bash
ecc-manager --port 8770
```

CLI examples:

```bash
ecc-use list
ecc-use doctor --project /path/to/project
ecc-use init ph-init arch-web-saas-next-postgres --project /path/to/project --dry-run
```

### Configuration

Default paths:

```text
ECC_HOME=~/everything-claude-code
PROFILE_HOME=~/.ecc-manager/profiles
```

You can change these paths in the Web UI Settings page or with environment variables:

```bash
ECC_HOME=/path/to/ecc-source PROFILE_HOME=/path/to/ecc-profiles ecc-manager
```

`ECC_HOME` should contain:

```text
commands/
skills/
agents/
rules/
```

ECC Manager also reads optional ECC metadata when present:

```text
VERSION
manifests/install-profiles.json
manifests/install-modules.json
manifests/install-components.json
config/project-stack-mappings.json
docs/COMMAND-REGISTRY.json
```

The currently tested ECC compatibility version is `2.0.0-rc.1`. Other versions can still be scanned, but Doctor and profile health should be reviewed before applying changes.

### Tool Targets

Claude Code is enabled by default. Codex and Antigravity are optional and must be enabled in Settings before ECC Manager generates their project files.

Managed targets can include:

```text
.claude/
CLAUDE.ecc.generated.md
AGENTS.md
AGENTS.ecc.generated.md
ANTIGRAVITY.ecc.generated.md
.agents/skills/
.agents/agents.md
.codex/agents/
.codex/rules/
.agents/rules/
.agents/workflows/
```

`AGENTS.md` is used as the project instruction entrypoint for Codex and Antigravity. ECC Manager only updates managed blocks marked with `ecc-manager`; existing user content is preserved.

### Safety

ECC Manager is a local tool. The Web UI binds to `127.0.0.1` by default, and write endpoints require a local session token. The server regenerates plans before applying them so browser-side mutations cannot change symlink targets.

Avoid exposing the server with `--host 0.0.0.0` unless you understand the local network risk.

### Development

Run tests:

```bash
python3 -m unittest
```

Build the package:

```bash
python3 -m build
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines and [docs/USER_GUIDE.md](docs/USER_GUIDE.md) for the detailed Chinese user guide.

### License

MIT. See [LICENSE](LICENSE).

## 简体中文

ECC Manager 是面向 `everything-claude-code` 工作流的本地能力装配器。它把 `ECC_HOME` 里的 `commands`、`skills`、`agents`、`rules`、`workflows` 和 profile 元数据，按 `phase + architecture + tech-stack fragment + pack` 组合，装配到当前项目的 Claude Code、Codex 和 Google Antigravity（反重力）本地配置里。

第一次使用建议先看完整教程：[ECC Manager 使用文档](docs/USER_GUIDE.md)。

### 为什么要做 ECC Manager

`everything-claude-code` 很强，但当 commands、skills、agents、rules 越来越完整时，也会变成一个很大的能力库。如果每个项目都直接加载全量内容，AI 工具要读的指令会变重，噪声会变多，也更容易占用宝贵的上下文窗口。

ECC Manager 的目标是把这套大型能力库拆成可以按项目装配的模块：根据当前阶段、技术架构、技术栈片段和能力包，只安装这个项目真正需要的部分。项目 lock 会记录已经装配的内容，Doctor 会检查源文件缺失、symlink 断开、生成文件异常、旧版残留和 command readiness，让更新和恢复都更可控。

### 它和 everything-claude-code 的关系

ECC Manager 不替代 `everything-claude-code`。它更像是放在大型 ECC 源仓库旁边的本地控制台：负责扫描、切分、预览、装配和检查。

你可以把 `everything-claude-code` 保持为统一的能力来源，然后让不同项目只拿自己需要的 commands、skills、agents、rules 和 workflows。比如 Next.js SaaS、Python API、代码审查项目、初始化项目，可以拥有不同的能力组合，而不是每个项目都复制整套上游库。

### Claude Code / Codex / Antigravity 适配关系

| ECC 源能力 | Claude Code 目标 | Codex 目标 | Google Antigravity（反重力）目标 |
| --- | --- | --- | --- |
| ECC commands | `.claude/commands/` symlink 和生成说明 | 写入 `AGENTS.md` 命令索引，并适配成 `.agents/skills/ecc-*` repo-scoped command skills | 转成 `.agents/workflows/` workflow Markdown |
| ECC skills | `.claude/skills/` | `.agents/skills/` | `.agents/skills/` |
| ECC agents | `.claude/agents/` | `.codex/agents/` Codex custom agent TOML | 聚合到 `.agents/agents.md` |
| ECC rules | `.claude/rules/` | `.codex/rules/` 和 `AGENTS.md` 托管区 | `.agents/rules/` |
| 生成说明 | `CLAUDE.ecc.generated.md` | `AGENTS.ecc.generated.md` 和 `AGENTS.md` 托管区 | `ANTIGRAVITY.ecc.generated.md` 和 `AGENTS.md` 托管区 |
| 可追踪性 | 项目 lock + Doctor 检查 | 项目 lock + Doctor 检查 | 项目 lock + Doctor 检查 |

### 网站截图

![ECC Manager 中文 Web UI](https://raw.githubusercontent.com/KylePowell-LABS/ecc-manager/main/assets/screenshots/ecc-manager-web-zh-cn.png)

它默认启动一个只监听本机的 Web UI，并自动打开浏览器：

```bash
ecc-manager
```

默认地址是：

```text
http://127.0.0.1:8765
```

如果端口被占用，会自动尝试后续端口。

### 安装

从 PyPI 安装：

```bash
python3 -m pip install ecc-manager
```

从 GitHub clone 后安装为本机命令：

```bash
git clone https://github.com/KylePowell-LABS/ecc-manager.git
cd ecc-manager
python3 -m pip install .
```

也可以不安装，直接在仓库里运行：

```bash
python3 -m ecc_manager.server
```

如果只想创建本地 wrapper：

```bash
bash scripts/install-local.sh
```

会创建：

```text
~/.local/bin/ecc-use
~/.local/bin/ecc-manager
```

请确认 `~/.local/bin` 已加入 `PATH`。

### 配置

默认路径：

```text
ECC_HOME=~/everything-claude-code
PROFILE_HOME=~/.ecc-manager/profiles
```

首次打开 Web UI 后，可以在“设置”里选择自己的 `ECC_HOME` 和 `PROFILE_HOME`。也可以用环境变量覆盖：

```bash
ECC_HOME=/path/to/ecc-source PROFILE_HOME=/path/to/ecc-profiles ecc-manager
```

`ECC_HOME` 需要包含：

```text
commands/
skills/
agents/
rules/
```

ECC Manager 会优先读取 ECC 仓库里的官方元数据：

```text
VERSION
manifests/install-profiles.json
manifests/install-modules.json
manifests/install-components.json
config/project-stack-mappings.json
docs/COMMAND-REGISTRY.json
```

当前测试兼容的 ECC 版本是 `2.0.0-rc.1`。如果用户的 ECC 版本不同，Web UI 和 Doctor 会提示兼容状态；仍可扫描本地资产，但建议先检查 profile health 和缺失引用后再执行装配。

### 使用目标选择

默认只生成 Claude Code 需要的 `.claude/` symlink、`CLAUDE.ecc.generated.md` 和项目 lock。Codex 和 Antigravity 是可选目标，需要用户在 Web UI 的“设置”里打开后才会生成对应文件。

可选目标适用于 Codex 桌面端、Codex CLI、Codex IDE 扩展，以及 Google Antigravity：

```text
AGENTS.md
AGENTS.ecc.generated.md
ANTIGRAVITY.ecc.generated.md
.agents/skills/
.agents/agents.md
.codex/agents/
.codex/rules/
.agents/rules/
.agents/workflows/
```

`AGENTS.md` 是 Codex 和 Antigravity 会读取的项目指令入口。ECC Manager 只维护带 `ecc-manager` 标记的托管区；用户已有内容会保留。启用 Codex 后，ECC skills 会链接或适配到 `.agents/skills/`，ECC agents 会转换成 Codex custom agent TOML 放到 `.codex/agents/`。

Codex 没有 Claude Code 的自定义 slash command 文件加载机制，所以 ECC commands 会适配成 repo-scoped skills，并以命令索引写入 AGENTS 托管区。用户在 Codex 里说 `/review-pr`、`/python-review` 这类 ECC 命令时，Codex 会按对应的 `.agents/skills/ecc-*` command skill 执行。

启用 Antigravity 后，ECC Manager 会把 ECC agents 聚合到 `.agents/agents.md`，把 ECC skills 链接或适配到 `.agents/skills/`，把 ECC rules 适配到 `.agents/rules/`，把 ECC commands 转成 `.agents/workflows/` 下的 workflow Markdown。`.agent/workflows/` 仅作为旧版残留被 Doctor 识别和提示，不再作为新生成目标。

### 使用

Web UI：

```bash
ecc-manager
```

不自动打开浏览器：

```bash
ecc-manager --no-open
```

指定端口：

```bash
ecc-manager --port 8770
```

命令行：

```bash
ecc-use list
ecc-use doctor --project /path/to/project
ecc-use init ph-init arch-web-saas-next-postgres --project /path/to/project --dry-run
```

### 安全说明

ECC Manager 是本地工具，默认只绑定 `127.0.0.1`。Web UI 的写入接口带有本地会话 token，并且执行时会在服务端重新生成计划，避免浏览器端篡改 symlink 目标。

不建议把 `--host` 设置成 `0.0.0.0` 暴露给局域网或公网。

### 开发

运行测试：

```bash
python3 -m unittest
```

构建包：

```bash
python3 -m build
```

贡献说明见 [CONTRIBUTING.md](CONTRIBUTING.md)，安全报告说明见 [SECURITY.md](SECURITY.md)。

### License

MIT. See [LICENSE](LICENSE).
