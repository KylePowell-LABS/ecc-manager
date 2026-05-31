# ECC Manager 使用文档

这份文档面向第一次使用 ECC Manager 的用户。你可以把它理解成一个本地装配器：它读取你的 ECC 仓库，根据你选择的阶段、架构、技术栈和能力包，把需要的 commands、skills、agents、rules 安装到当前项目里。

ECC Manager 默认只配置 Claude Code。Codex 和 Google Antigravity 都是可选目标，需要你在设置里明确打开后才会生成对应文件。

## 1. 你需要先准备什么

使用前需要有两类目录：

```text
ECC_HOME        ECC 源仓库，里面放 commands、skills、agents、rules
PROFILE_HOME    ECC Manager 的 profile 配置目录
```

默认路径是：

```text
ECC_HOME=~/everything-claude-code
PROFILE_HOME=~/.ecc-manager/profiles
```

`ECC_HOME` 至少应该包含：

```text
commands/
skills/
agents/
rules/
```

如果你的 ECC 仓库有这些元数据，ECC Manager 会优先读取它们，用来识别版本、组件关系和命令依赖：

```text
VERSION
manifests/install-profiles.json
manifests/install-modules.json
manifests/install-components.json
config/project-stack-mappings.json
docs/COMMAND-REGISTRY.json
```

## 2. 安装和启动

进入 ECC Manager 项目目录后，可以直接安装成本机命令：

```bash
python3 -m pip install .
```

安装后启动 Web UI：

```bash
ecc-manager
```

默认会打开：

```text
http://127.0.0.1:8765
```

如果 8765 被占用，ECC Manager 会自动尝试后续端口。

如果你不想安装，也可以在仓库里直接运行：

```bash
python3 -m ecc_manager.server
```

如果不想自动打开浏览器：

```bash
ecc-manager --no-open
```

指定端口：

```bash
ecc-manager --port 8770
```

## 3. 第一次打开 Web UI 后怎么做

推荐按这个顺序操作：

1. 打开 Web UI。
2. 在项目选择处选择你要管理的项目目录。
3. 进入“设置”，确认 `ECC_HOME` 和 `PROFILE_HOME` 是否正确。
4. 在“设置”里选择使用目标：
   - 只用 Claude Code：不要勾选 Codex / Antigravity。
   - 用 Codex：勾选“使用 Codex”。
   - 用 Antigravity：勾选“使用 Antigravity”。
   - 同一个项目同时给 Codex 和 Antigravity 用：两个都勾。
5. 回到主页面，选择阶段、架构、技术栈片段和能力包。
6. 先点预览计划，确认会写入哪些文件。
7. 如果没有缺失源文件和目标冲突，再执行装配。
8. 执行后打开 Doctor 检查结果。

不要一开始就手动复制文件到项目里。ECC Manager 会用 lock 记录哪些文件是它装配的，这样以后更新、删除、检查才不会乱。

## 4. 阶段、架构、技术栈和能力包怎么选

ECC Manager 的安装结果由这些选择共同决定：

```text
phase + architecture + project-type fragment + pack
```

你可以这样理解：

| 类型 | 用途 | 例子 |
| --- | --- | --- |
| phase | 当前项目阶段 | init、development、review |
| architecture | 项目架构 | web app、backend、desktop |
| project-type fragment | 技术栈片段 | next、postgres、python |
| pack | 额外能力包 | planning、testing、security |

第一次配置项目时，一般选择：

```text
1 个初始阶段
1 个主要架构
若干技术栈片段
按需选择 pack
```

后续项目变化时，不需要重来，可以用“添加”继续追加新的阶段、技术栈或能力包。

## 5. 选择不同使用目标会生成什么

### Claude Code

默认启用。会生成或维护：

```text
.claude/
CLAUDE.ecc.generated.md
.claude/ecc-lock/profile.json
```

Claude Code 会直接使用 `.claude/` 下的 commands、skills、agents、rules。

### Codex

只有你在设置里勾选“使用 Codex”后才会生成：

```text
AGENTS.md
AGENTS.ecc.generated.md
.agents/skills/
.codex/agents/
```

Codex 会读取 `AGENTS.md`。ECC Manager 只维护带 `ecc-manager` 标记的托管区，用户自己写在 `AGENTS.md` 里的内容会保留。

Codex 没有 Claude Code 那种完全相同的 slash command 文件加载机制，所以 ECC commands 会作为索引写进 `AGENTS.md` 和 `AGENTS.ecc.generated.md`。在 Codex 里可以这样说：

```text
按照 /plan-prd 的流程帮我规划这个功能
```

Codex 会根据项目说明和 `.agents/skills/ecc-*` command skill 执行对应流程。

### Google Antigravity

只有你在设置里勾选“使用 Antigravity”后才会生成：

```text
AGENTS.md
ANTIGRAVITY.ecc.generated.md
.agents/agents.md
.agents/skills/
.agents/rules/
.agents/workflows/
```

新版 Antigravity 默认使用 `.agents/...`。ECC Manager 会把多个 ECC agents 聚合进 `.agents/agents.md`，把 commands 转成 `.agents/workflows/`。旧的 `.agent/workflows/` 只作为旧版残留被 Doctor 识别和提示，不再作为新生成目标。

在 Antigravity 里打开同一个项目后，可以使用生成的 workflow，或者让 Antigravity 按项目里的 ECC workflow 执行。

## 6. 推荐工作流

### 新项目初始化

1. 启动 `ecc-manager`。
2. 选择项目目录。
3. 检查设置里的 `ECC_HOME`。
4. 选择使用目标。
5. 选择初始 phase、architecture、project-type fragment 和 pack。
6. 点预览计划。
7. 确认没有冲突后执行。
8. 运行 Doctor。
9. 在 Claude Code、Codex 或 Antigravity 中打开这个项目使用。

### 项目中途新增技术栈

比如项目后来加了 Postgres、Redis 或测试框架：

1. 在 Web UI 里选择当前项目。
2. 选择新的技术栈片段或 pack。
3. 使用“添加”而不是重新初始化。
4. 预览计划。
5. 执行。
6. 运行 Doctor。

### ECC 仓库更新后

每个人本机的 ECC 版本可能不同，所以更新 ECC 后建议这样做：

1. 确认 `ECC_HOME` 指向新的 ECC 仓库。
2. 打开 Web UI。
3. 看“ECC 版本兼容”状态。
4. 运行 ECC 扫描或 Doctor。
5. 如果某些 command、skill、agent、rule 在新版本中不存在，预览计划会显示缺失或降级。
6. 如果新版本新增了组件，不会盲目全部安装，只有当你的 profile、阶段、技术栈或 pack 需要它时才会进入计划。

这点很重要：ECC Manager 不是把 ECC 仓库里的所有东西都塞进项目，而是根据当前项目选择和 ECC 元数据计算需要的内容。

## 7. Doctor 是干什么的

Doctor 用来检查项目现在是否健康。它会检查：

```text
ECC_HOME 是否存在
PROFILE_HOME 是否存在
项目 lock 是否存在
已装配文件是否还在
symlink 是否断开
生成文件是否被破坏
Claude / Codex / Antigravity 目标文件是否冲突
旧 Antigravity .agent/workflows 是否有残留
```

在 Web UI 里可以直接进入 Doctor 页面。

命令行也可以运行：

```bash
ecc-use doctor --project /path/to/project
```

如果只是安全修复自动生成文件和可恢复的 symlink：

```bash
ecc-use doctor --project /path/to/project --fix
```

Doctor 不会随便删除用户自己的真实文件。遇到真实文件冲突时，它会提示你处理。

## 8. 命令行备用方式

Web UI 是推荐入口。命令行适合自动化或排查。

列出可用 profiles：

```bash
ecc-use list
```

只看 phases：

```bash
ecc-use list phases
```

初始化项目，先 dry-run：

```bash
ecc-use init ph-init arch-web-saas-next-postgres --project /path/to/project --dry-run
```

确认计划没问题后执行：

```bash
ecc-use init ph-init arch-web-saas-next-postgres --project /path/to/project
```

追加能力：

```bash
ecc-use add pack-testing --project /path/to/project
```

查看状态：

```bash
ecc-use status --project /path/to/project
```

移除某个 profile：

```bash
ecc-use remove pack-testing --project /path/to/project
```

## 9. 常见问题

### 我是不是需要同时生成 Claude Code、Codex、Antigravity 三套文件？

不需要。默认只生成 Claude Code。Codex 和 Antigravity 都要在设置里手动勾选。

### 为什么 Codex 也会用 AGENTS.md？

`AGENTS.md` 是 Codex 项目指令入口。ECC Manager 会在里面维护一个托管区，告诉 Codex 当前项目启用了哪些 ECC commands、skills 和 agents。

### 为什么 Antigravity 用的是 .agents/agents.md 和 .agents/workflows？

新版 Antigravity 默认使用 `.agents/...` 目录。ECC Manager 会把多个 agent persona 集中写入 `.agents/agents.md`，把 Antigravity workflows 生成到 `.agents/workflows/`。旧 `.agent/workflows/` 只用于识别旧版残留。

### 如果 ECC 版本变了怎么办？

打开 Web UI 看版本兼容状态，然后跑 Doctor。ECC Manager 会根据当前 `ECC_HOME` 重新扫描，不会假设所有人的 ECC 版本都一样。

### 如果某个 command 依赖 skill 或 agent 怎么办？

ECC Manager 会在预览计划里展开依赖。必需依赖缺失会阻止执行；可选依赖会提示确认或标记能力降级。

### 如果目标文件已经存在怎么办？

如果是 ECC Manager 之前生成的文件，可以更新。如果是用户自己写的真实文件，计划会标记冲突并阻止执行，避免覆盖你的内容。

### 我应该直接改生成文件吗？

不建议直接改这些文件：

```text
CLAUDE.ecc.generated.md
AGENTS.ecc.generated.md
ANTIGRAVITY.ecc.generated.md
AGENTS.md 中 ecc-manager 标记的托管区
```

如果要写项目自己的说明，写在 `CLAUDE.md` 或 `AGENTS.md` 的非托管区域。

## 10. 安全边界

ECC Manager 默认只监听本机：

```text
127.0.0.1
```

Web UI 的写入接口带本地会话 token，并且服务端会重新生成计划，避免浏览器端篡改目标路径。

不建议这样启动：

```bash
ecc-manager --host 0.0.0.0
```

除非你非常确定自己要把它暴露给局域网，并且知道风险。

## 11. 最简单的一句话流程

第一次使用时记住这一句就够了：

```text
启动 ecc-manager -> 选项目 -> 设置 ECC_HOME 和使用目标 -> 选 profile -> 预览计划 -> 执行 -> Doctor 检查 -> 打开对应 AI 工具使用
```
