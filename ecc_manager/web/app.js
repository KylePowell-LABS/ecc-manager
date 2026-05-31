const state = {
  cwd: "",
  config: {},
  scan: null,
  catalog: { phases: {}, architectures: {}, "project-types": {}, packs: {} },
  selectedPhase: "ph-init",
  selectedArchitecture: "arch-web-saas-next-postgres",
  selectedStagePhases: new Set(["ph-build"]),
  selectedProjectTypes: new Set(),
  selectedPacks: new Set(),
  currentPlan: null,
  lastActionPage: "init",
  assetScan: null,
  lastTaskRun: null,
  csrfToken: "",
  homeDir: "",
  lang: "",
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));
const PROJECT_PATH_STORAGE_KEY = "ecc-manager.session-project-path";
const PROJECT_RECENTS_STORAGE_KEY = "ecc-manager.recent-project-paths";
const LANGUAGE_STORAGE_KEY = "ecc-manager.language";
const DEFAULT_LANGUAGE = "zh-CN";
const SUPPORTED_LANGUAGES = ["zh-CN", "en"];

const I18N = {
  "zh-CN": {},
  en: {
    "本地 ECC 环境装配器": "Local ECC environment assembler",
    "项目": "Project",
    "未选择": "Not selected",
    "初始化": "Initialize",
    "阶段": "Phases",
    "能力包": "Packs",
    "能力治理": "Governance",
    "预览": "Preview",
    "任务结果": "Task result",
    "状态": "Status",
    "设置": "Settings",
    "项目选择": "Project selection",
    "先确定当前要管理的项目，后面的初始化、添加能力包和检查都围绕这个路径执行。": "Choose the project to manage first. Initialization, packs, and checks all run against this path.",
    "项目目录": "Project directory",
    "使用此路径": "Use this path",
    "使用启动目录": "Use launch directory",
    "扫描项目": "Scan project",
    "初始化 Profiles": "Initialize profiles",
    "打开 CLAUDE.md": "Open CLAUDE.md",
    "打开 .claude 目录": "Open .claude folder",
    "打开 AGENTS.md": "Open AGENTS.md",
    "打开 .codex 目录": "Open .codex folder",
    "初始化向导": "Initialization wizard",
    "第一次装配项目时，选择初始阶段、一个主技术架构、可选技术栈片段和初始能力包。": "For the first setup, choose the initial phase, one primary architecture, optional stack fragments, and starter packs.",
    "初始阶段": "Initial phase",
    "主技术架构": "Primary architecture",
    "高级：技术栈片段": "Advanced: stack fragments",
    "初始能力包": "Starter packs",
    "阶段演进": "Phase evolution",
    "项目初始化后，从这里追加新的阶段能力，保留初始阶段记录。": "After initialization, add new phase capabilities here while preserving the initial phase record.",
    "预览追加": "Preview additions",
    "追加阶段": "Add phase",
    "选择下一阶段（可多选）": "Choose next phase(s)",
    "能力包市场": "Pack marketplace",
    "按需添加完整能力包，required 依赖会自动处理，optional 项会清楚列出。": "Add complete capability packs as needed. Required dependencies are handled automatically, while optional items are listed clearly.",
    "本地 ECC 检测与能力治理": "Local ECC scan and governance",
    "先扫描本地 ECC 原库，再治理阶段、架构、能力包和命令依赖；检测本身不会写入任何文件。": "Scan the local ECC source first, then govern phases, architectures, packs, and command dependencies. Scans do not write files.",
    "检测本地 ECC": "Scan local ECC",
    "应用选中建议": "Apply selected suggestions",
    "依赖预览": "Dependency preview",
    "执行任何改动前，先看清楚将创建、跳过、缺失和不会修改的内容。": "Before applying changes, review what will be created, skipped, missing, and left untouched.",
    "返回修改选择": "Back to selection",
    "执行": "Run",
    "一次执行是否真正完成、完成标准是否通过，以及下一步应该做什么。": "See whether a run really completed, which criteria passed, and what should happen next.",
    "查看项目状态": "View project status",
    "查看 Doctor": "View Doctor",
    "当前项目状态": "Current project status",
    "查看当前项目启用了哪些 ECC 组件，以及每个组件来自哪个 profile 或 pack。": "See which ECC components are enabled for this project and which profile or pack provided each one.",
    "刷新状态": "Refresh status",
    "重新生成说明": "Regenerate instructions",
    "Doctor 检查": "Doctor checks",
    "把 ECC_HOME、profiles、symlink、lock 和 CLAUDE 引用问题解释清楚。": "Explain ECC_HOME, profile, symlink, lock, and CLAUDE reference issues.",
    "运行检查": "Run checks",
    "安全修复": "Safe repair",
    "选择 ECC_HOME 和 PROFILE_HOME；链接模式、覆盖策略和 settings.json 管理保持锁定。": "Choose ECC_HOME and PROFILE_HOME. Link mode, overwrite policy, and settings.json management stay locked.",
    "详情": "Details",
    "点击 phase / architecture / project-type / pack 查看依赖": "Click a phase, architecture, project type, or pack to inspect dependencies",
    "确认本次安装": "Confirm this installation",
    "执行前请确认本次会写入的内容。": "Review what will be written before continuing.",
    "关闭": "Close",
    "取消": "Cancel",
    "确认执行": "Confirm and run",
    "最近项目": "Recent projects",
    "还没有最近项目。": "No recent projects yet.",
    "无需操作": "No action needed",
    "每个问题都包含影响和下一步选项。": "Each issue includes impact and next-step options.",
    "没有需要处理的问题。": "No issues need attention.",
    "影响：": "Impact: ",
    "基础路径": "Base paths",
    "ECC 源仓库": "ECC source repository",
    "ECC 版本兼容": "ECC version compatibility",
    "Profile 配置": "Profile configuration",
    "当前项目检查结果": "Current project checks",
    "存在": "Exists",
    "不存在": "Does not exist",
    "已存在": "Already exists",
    "缺失": "Missing",
    "未启用": "Not enabled",
    "托管区已写入": "Managed block written",
    "当前阶段": "Current phase",
    "已追加阶段": "Added phases",
    "技术架构": "Architecture",
    "技术栈片段": "Stack fragments",
    "操作": "Actions",
    "组件": "Components",
    "最近任务": "Latest task",
    "下一步": "Next steps",
    "完成标准": "Completion criteria",
    "请选择项目目录": "Choose a project folder",
    "未选择内容。": "Nothing selected.",
    "无": "None",
    "暂无内容": "No content yet",
    "暂无建议。": "No suggestions yet.",
    "还没有预览内容。": "No preview yet.",
    "本次没有新增或更新内容。": "This run has no new or updated content.",
    "将创建 symlink": "Symlinks to create",
    "将创建 runtime symlink": "Runtime symlinks to create",
    "已存在，将跳过": "Already exists, will skip",
    "缺失源文件": "Missing source files",
    "Runtime 需要确认": "Runtime needs confirmation",
    "Runtime 本地文件缺失": "Runtime local files missing",
    "Codex 将写入": "Codex writes",
    "Codex 目标冲突": "Codex target conflicts",
    "Codex 缺失源文件": "Codex missing source files",
    "Antigravity 将写入": "Antigravity writes",
    "Antigravity 目标冲突": "Antigravity target conflicts",
    "Antigravity 缺失源文件": "Antigravity missing source files",
    "命令可运行性": "Command readiness",
    "将生成文件": "Files to generate",
    "不会修改": "Will not modify",
    "Optional，需要确认": "Optional items needing confirmation",
    "满配模式": "Full mode",
    "预览问题与选项": "Preview issues and options",
    "本次预览没有 warning/error。": "This preview has no warnings or errors.",
    "目标汇总": "Target summary",
    "已安装目标汇总": "Installed target summary",
    "Project files": "Project files",
    "Optional": "Optional",
    "待确认 optional": "Optional items pending confirmation",
    "Generated Project Files": "Generated project files",
    "未安装的可选项": "Optional items not installed",
    "命令关联图": "Command relation graph",
    "检测概览": "Scan overview",
    "归类建议": "Classification suggestions",
    "归类建议与应用区": "Classification suggestions and apply area",
    "命令依赖契约": "Command dependency contracts",
    "Profile 健康": "Profile health",
    "状态问题与选项": "Status issues and options",
    "当前状态没有 warning/error。": "Current status has no warnings or errors.",
    "项目问题与选项": "Project issues and options",
    "项目检查没有 warning/error。": "Project checks have no warnings or errors.",
    "任务问题与选项": "Task issues and options",
    "本次任务没有 warning/error。": "This task has no warnings or errors.",
    "Doctor 问题与选项": "Doctor issues and options",
    "Doctor 没有 warning/error。": "Doctor has no warnings or errors.",
    "能力治理问题与选项": "Governance issues and options",
    "能力治理没有 warning/error。": "Governance has no warnings or errors.",
    "安全修复记录": "Safe repair log",
    "ECC_HOME 不可用": "ECC_HOME unavailable",
    "Profile 配置不可用": "Profile configuration unavailable",
    "项目未初始化或缺少 lock": "Project is not initialized or lock is missing",
    "目标能力文件缺失": "Target capability files missing",
    "存在旧版或未记录产物": "Legacy or untracked artifacts found",
    "打开设置": "Open settings",
    "去初始化": "Go initialize",
    "跳过": "Skip",
    "应用选中建议": "Apply selected suggestions",
    "补齐或移除引用": "Add or remove references",
    "查看下方契约": "Review contracts below",
    "选择目录": "Choose folder",
    "保存设置": "Save settings",
    "恢复当前已保存值": "Restore saved values",
    "使用 Claude Code": "Use Claude Code",
    "使用 Codex": "Use Codex",
    "使用 Antigravity": "Use Antigravity",
    "托管 AGENTS.md": "Manage AGENTS.md",
    "Codex 生成文件": "Codex generated file",
    "Antigravity 生成文件": "Antigravity generated file",
    "请选择至少一个未启用阶段。": "Choose at least one phase that is not enabled.",
    "当前项目还没有 ECC lock。请先到“初始化”完成第一次装配，再从这里追加阶段。": "This project has no ECC lock yet. Initialize it first, then add phases here.",
    "已经添加过了": "Already added",
    "主架构": "Primary architecture",
    "命令由阶段/能力包提供": "Commands come from phases/packs",
    "添加到当前项目": "Add to current project",
    "预览添加": "Preview add",
    "当前项目还没有 ecc-use 管理的组件。": "This project has no ecc-use managed components yet.",
    "外部初始化：": "External install: ",
    "查看任务结果": "View task result",
    "选择要由 ECC Manager 管理的项目目录": "Choose the project folder for ECC Manager",
    "选择 ECC_HOME：包含 commands、skills、agents、rules 的 ECC 源目录": "Choose ECC_HOME: the ECC source folder containing commands, skills, agents, and rules",
    "选择 PROFILE_HOME：保存 ECC profiles 和 ecc-use.config.json 的目录": "Choose PROFILE_HOME: the folder for ECC profiles and ecc-use.config.json",
    "选择目录失败": "Folder selection failed",
    "未知错误": "Unknown error",
    "扫描中...": "Scanning...",
    "项目目录已选择": "Project folder selected",
    "请先输入或选择项目目录": "Enter or choose a project folder first",
    "请先选择项目目录": "Choose a project folder first",
    "设置已保存": "Settings saved",
    "已取消执行": "Run cancelled",
    "存在缺失源文件，不能执行": "Missing source files prevent this run",
    "界面语言": "Interface language",
    "首次打开会跟随浏览器语言，手动切换后会记住选择。": "On first open, ECC Manager follows your browser language. Manual changes are remembered.",
  },
};

Object.assign(I18N.en, {
  "未设置": "Not set",
  "未检测": "Not checked",
  "未声明": "Not declared",
  "已追加": "Added",
  "第一次初始化时选定，作为项目起点保留": "Chosen during initial setup and kept as the project starting point",
  "项目推进后追加的阶段能力": "Phase capabilities added as the project progresses",
  "本次将追加：": "This will add: ",
  "点击“选择项目目录”，选择要由 ECC Manager 管理的项目。": "Click \"Choose project folder\" and select the project ECC Manager should manage.",
  "ECC 组件的来源目录": "Source folder for ECC components",
  "未检测到兼容性信息": "No compatibility information detected",
  "阶段、技术架构、技术栈片段和能力包配置": "Phase, architecture, stack-fragment, and pack configuration",
  "当前被管理的项目路径": "Project path currently being managed",
  "请先创建目录或选择已有项目": "Create the folder first or choose an existing project",
  "项目级 Claude 配置目录": "Project-level Claude configuration folder",
  "项目说明入口": "Project instruction entrypoint",
  "ECC 自动生成内容": "ECC generated content",
  "Claude Code 目标未启用": "Claude Code target is not enabled",
  "Codex / Antigravity workspace skills；Codex commands 会适配为 skills": "Codex / Antigravity workspace skills; Codex commands are adapted as skills",
  "Codex / Antigravity 目标未启用": "Codex / Antigravity target is not enabled",
  "Codex 目标未启用": "Codex target is not enabled",
  "Antigravity 目标未启用": "Antigravity target is not enabled",
  "项目级 Claude 配置目录": "Project-level Claude configuration folder",
  "Antigravity agent personas": "Antigravity agent personas",
  "Antigravity workspace rules": "Antigravity workspace rules",
  "Antigravity workflows": "Antigravity workflows",
  "Codex / Antigravity 自动读取的项目指令入口": "Project instruction entrypoint read by Codex / Antigravity",
  "ECC 为 Codex 生成的完整说明": "Complete ECC instructions generated for Codex",
  "ECC 为 Antigravity 生成的完整说明": "Complete ECC instructions generated for Antigravity",
  "已记录安装的 profiles": "Installed profiles are recorded",
  "初始化后记录项目配置": "Project configuration is recorded after initialization",
  "旧版残留": "Legacy leftover",
  "旧版 Antigravity/Codex 产物。": "Legacy Antigravity/Codex artifacts.",
  "无法读取 ECC 源组件。": "ECC source components cannot be read.",
  "无法读取阶段、架构、能力包配置。": "Phase, architecture, and pack configuration cannot be read.",
  "系统无法确认当前项目已安装哪些 ECC 能力。": "The system cannot confirm which ECC capabilities are installed in this project.",
  "这些目标缺失时，对应 AI 工具读取不到完整 ECC 能力。": "When these targets are missing, the corresponding AI tool cannot read the full ECC capabilities.",
  "旧产物可能造成工具读取混乱。": "Legacy artifacts may confuse tool loading.",
  "检查 ECC_HOME。": "Check ECC_HOME.",
  "检查 PROFILE_HOME。": "Check PROFILE_HOME.",
  "选择 profile 后生成初始化预览。": "Choose profiles and generate an initialization preview.",
  "生成初始化或追加能力预览。": "Generate an initialization or add-capability preview.",
  "检查是否可安全修复。": "Check whether this can be repaired safely.",
  "打开 Doctor 检查遗留产物。": "Open Doctor to inspect legacy artifacts.",
  "需要确认后处理。": "Review before handling.",
  "刷新资产盘点失败": "Failed to refresh asset inventory",
  "刷新状态失败": "Failed to refresh status",
  "Doctor 检查失败": "Doctor check failed",
  "扫描当前目录失败": "Failed to scan launch directory",
  "扫描项目失败": "Failed to scan project",
  "处理操作失败": "Failed to handle action",
  "初始化 Profiles 失败": "Failed to initialize profiles",
  "生成初始化预览失败": "Failed to generate initialization preview",
  "初始化失败": "Initialization failed",
  "生成阶段追加预览失败": "Failed to generate phase preview",
  "追加阶段失败": "Failed to add phase",
  "执行失败": "Run failed",
  "应用建议失败": "Failed to apply suggestions",
  "重新生成说明文件失败": "Failed to regenerate instruction files",
  "Doctor 修复失败": "Doctor repair failed",
  "切换项目失败": "Failed to switch project",
  "生成能力包预览失败": "Failed to generate pack preview",
  "添加能力包失败": "Failed to add pack",
  "保存设置失败": "Failed to save settings",
  "扫描失败": "Scan failed",
  "扫描完成：项目目录存在": "Scan complete: project folder exists",
  "扫描完成：项目目录不存在": "Scan complete: project folder does not exist",
  "项目目录不存在，无法打开": "Project folder does not exist; cannot open it",
  "不存在，请先创建或初始化": "does not exist; create or initialize it first",
  "已向系统发送打开请求：": "Sent open request to the system: ",
  "无法打开目录选择窗口": "Could not open the folder picker",
  "项目目录已选择，但扫描失败": "Project folder selected, but scan failed",
  "没有找到上一任务的 profile，无法生成满配预览": "No profiles were found for the last task, so full preview cannot be generated",
  "请按提示手动处理": "Follow the guidance manually",
  "确认运行 Doctor 安全修复？只会修复托管且可恢复的项目，不会覆盖用户文件。": "Run Doctor safe repair? It only repairs managed, recoverable items and will not overwrite user files.",
  "已取消安全修复": "Safe repair cancelled",
  "接口未返回 JSON，可能是服务进程还没有重启": "The API did not return JSON. The server may not have restarted yet",
  "请求失败": "Request failed",
  "本次新增：symlink": "New this run: symlink",
  "本次新增：生成文件": "New this run: generated file",
  "本次更新：托管文件": "Updated this run: managed file",
  "本次写入：lock": "Written this run: lock",
  "本次生成": "Generated this run",
  "本次更新：托管段落": "Updated this run: managed block",
  "冲突：已有真实文件": "Conflict: real file exists",
  "冲突：非 ECC symlink": "Conflict: non-ECC symlink",
  "待确认：外部初始化": "Pending: external initialization",
  "缺失：runtime": "Missing: runtime",
  "待确认：optional": "Pending: optional",
  "命令 blocked": "Command blocked",
  "命令待确认": "Command needs confirmation",
  "命令降级": "Command degraded",
  "命令 unknown": "Command unknown",
  "曾跳过：目标冲突": "Previously skipped: target conflict",
  "待处理": "Pending",
  "新增": "Add",
  "更新": "Update",
  "已经添加": "Already added",
  "待确认": "Pending",
  "问题": "Issues",
  "项": "items",
  "来源：": "Source: ",
  "源：": "Source: ",
  "目标：": "Target: ",
  "已存在": "Already exists",
  "缺少必需组件：": "Missing required components: ",
  "Runtime 待确认：": "Runtime pending: ",
  "Optional 未启用：": "Optional not enabled: ",
  "原因：": "Reason: ",
  "安装时检测到目标冲突，已跳过。": "A target conflict was detected during installation and skipped.",
  "Claude Code 托管说明文件": "Claude Code managed instruction file",
  "Codex 托管说明文件": "Codex managed instruction file",
  "Antigravity 托管说明文件": "Antigravity managed instruction file",
  "ECC Manager 安装记录": "ECC Manager installation record",
  "Codex / Antigravity 托管入口": "Codex / Antigravity managed entrypoint",
  "来自": "From",
  "来自 .ecc-manager/ecc-lock/profile.json": "From .ecc-manager/ecc-lock/profile.json",
  "这里来自项目 lock 的已安装记录，是刷新 / 重启后恢复的只读汇总，不代表本次将写入的计划。": "These installed records come from the project lock. They are a read-only summary restored after refresh or restart, not the plan that will be written this time.",
  "这里汇总当前项目总目标，并标出本次预览新增、更新、待确认项和问题；按工具和类型分组，父级和子集都可以折叠。": "This summarizes all current project targets and marks new, updated, pending, and problem items from this preview. Groups are organized by tool and type and can be collapsed.",
  "ECC commands 适配为 Codex skills": "ECC commands are adapted as Codex skills",
  ".agents/agents.md 聚合 personas": ".agents/agents.md aggregates personas",
  "ECC commands 转 workflows": "ECC commands become workflows",
  "Generated / lock": "Generated / lock",
  "Command health": "Command health",
  "任务完成": "Task completed",
  "任务完成但需要跟进": "Task completed with follow-up",
  "还没有任务结果。执行初始化、追加阶段或添加能力包后，这里会显示完成证明。": "No task result yet. After initialization, phase additions, or pack additions, completion evidence appears here.",
  "执行失败": "Run failed",
  "初始化项目能力": "Initialize project capabilities",
  "添加项目能力": "Add project capabilities",
  "追加项目阶段能力": "Add project phase capabilities",
  "执行项目能力变更": "Run project capability change",
  "新建 symlink": "New symlinks",
  "required 组件": "required components",
  "全局运行时": "global runtime",
  "Codex 写入": "Codex writes",
  "Antigravity 写入": "Antigravity writes",
  "需要跟进": "Needs follow-up",
  "下一步命令": "Next commands",
  "这些检查决定本次任务是否真的完成。": "These checks decide whether this task is really complete.",
  "这里是系统根据验证结果给出的后续动作。": "These are follow-up actions suggested from the verification result.",
  "查看下方“下一步”处理。": "Review the Next steps section below.",
  "源组件存在": "Source components exist",
  "required symlink 可创建": "required symlinks can be created",
  "lock 写入": "lock written",
  "说明文件生成": "Instruction file generated",
  "命令可运行性": "Command readiness",
  "Claude 说明文件": "Claude instruction file",
  "Codex 兼容层": "Codex compatibility layer",
  "Antigravity 兼容层": "Antigravity compatibility layer",
  "Doctor 自动验证": "Doctor automatic verification",
  "所有 required 源组件都存在。": "All required source components exist.",
  "执行后检查所有 required symlink。": "All required symlinks are checked after execution.",
  "执行后写入 .ecc-manager/ecc-lock/profile.json。": ".ecc-manager/ecc-lock/profile.json is written after execution.",
  "执行后生成 AGENTS.md 托管区、Codex skills 和 Codex agents。": "AGENTS.md managed blocks, Codex skills, and Codex agents are generated after execution.",
  "执行后生成 Antigravity agents、workflows、rules 和项目说明。": "Antigravity agents, workflows, rules, and project instructions are generated after execution.",
  "本次任务没有新增 command。": "This task did not add commands.",
  "本次 command 的必需依赖完整。": "Required dependencies for this run's commands are complete.",
  "Codex 支持未启用。": "Codex support is not enabled.",
  "Antigravity 支持未启用。": "Antigravity support is not enabled.",
  "Doctor 未发现阻断项。": "Doctor found no blocking issues.",
  "Doctor 未发现需要自动修复的项目": "Doctor found nothing that needs automatic repair",
  "任务已经完成，当前没有必须跟进的动作。": "The task is complete. No required follow-up remains.",
  "已完成": "Done",
  "没有需要处理的问题。": "No issues need attention.",
  "运行下一步命令": "Run next commands",
  "环境已装配，可以进入下一步工作。": "The environment is assembled and ready for the next step.",
  "复制命令使用": "Copy and use commands",
  "在对应 AI 工具中运行建议命令。": "Run the suggested commands in the corresponding AI tool.",
  "可完整运行": "Ready",
  "必须依赖完整": "Required dependencies complete",
  "必需依赖完整": "Required dependencies complete",
  "已写入": "Written",
  "如果不处理，相关能力可能不可用或继续显示 warning。": "If not handled, related capabilities may be unavailable or keep showing warnings.",
  "AGENTS.md Antigravity 托管区": "AGENTS.md Antigravity managed block",
  "可完整运行：必需依赖完整": "Ready: required dependencies complete",
  "registry": "registry",
  "legacy": "legacy",
  "源组件缺失会阻止计划安全执行。": "Missing source components prevent safe plan execution.",
  "目标冲突时不会覆盖用户文件。": "Target conflicts will not overwrite user files.",
  "Codex 可能无法读取完整 ECC 能力。": "Codex may not be able to read the full ECC capabilities.",
  "Antigravity 可能无法读取完整 ECC 能力。": "Antigravity may not be able to read the full ECC capabilities.",
  "blocked command 可能无法运行。": "Blocked commands may not run.",
  "未确认 runtime 会让命令能力不完整。": "Unconfirmed runtime leaves command capabilities incomplete.",
  "系统无法自动判断该命令是否满配。": "The system cannot automatically decide whether this command is fully configured.",
  "命令可运行，但增强能力不是满配。": "The command can run, but enhanced capabilities are not fully configured.",
  "Doctor warning 可能影响工具读取生成说明或兼容层。": "Doctor warnings may affect tool loading of generated instructions or compatibility layers.",
  "未引用生成说明时，Claude Code 可能不会自动读取 ECC 配置。": "If generated instructions are not referenced, Claude Code may not automatically read the ECC configuration.",
  "补齐源组件": "Add missing source components",
  "处理目标冲突": "Resolve target conflicts",
  "修复 Codex 兼容层": "Repair Codex compatibility layer",
  "修复 Antigravity 兼容层": "Repair Antigravity compatibility layer",
  "修复命令必需依赖": "Repair command required dependencies",
  "确认 runtime": "Confirm runtime",
  "补充命令契约": "Add command contracts",
  "启用 optional 依赖": "Enable optional dependencies",
  "查看 Doctor warning": "Review Doctor warnings",
  "连接 CLAUDE.md": "Connect CLAUDE.md",
  "手动加入引用": "Add reference manually",
  "查看冲突详情。": "Review conflict details.",
  "检查 Codex 目标。": "Check Codex targets.",
  "检查 Antigravity 目标。": "Check Antigravity targets.",
  "打开 Doctor 检查详情。": "Open Doctor details.",
  "确认后重新生成托管文件。": "Regenerate managed files after confirmation.",
  "在对应 AI 工具中运行建议命令。": "Run the suggested commands in the matching AI tool.",
  "Profiles 和 ecc-use.config.json 的保存目录。": "Folder for profiles and ecc-use.config.json.",
  "ECC 组件来源目录，需要包含 commands、skills、agents、rules 等子目录。": "ECC component source folder. It must contain commands, skills, agents, rules, and related subfolders.",
  "生成给 Codex 看的完整说明文件名。": "Full instruction filename generated for Codex.",
  "生成给 Google Antigravity 看的完整说明文件名。": "Full instruction filename generated for Google Antigravity.",
  "选中后才生成 Claude Code 的 .claude/commands、skills、agents、rules 和 CLAUDE 说明文件。": "When selected, generate Claude Code .claude/commands, skills, agents, rules, and CLAUDE instruction files.",
  "选中后才生成 Codex 的 AGENTS.md 托管区、.agents/skills、.codex/agents 和 .codex/rules；ECC commands 会适配为 skills。": "When selected, generate Codex AGENTS.md managed blocks, .agents/skills, .codex/agents, and .codex/rules. ECC commands are adapted as skills.",
  "选中后才生成 Antigravity 的 AGENTS.md 托管区、.agents/agents.md、.agents/skills、.agents/rules 和 .agents/workflows。": "When selected, generate Antigravity AGENTS.md managed blocks, .agents/agents.md, .agents/skills, .agents/rules, and .agents/workflows.",
  "Codex / Antigravity 需要这个入口才能稳定读取本次装配；只更新带 ecc-manager 标记的托管区，不覆盖用户已有内容。": "Codex / Antigravity need this entrypoint to read this assembly reliably. Only ecc-manager managed blocks are updated; existing user content is preserved.",
  "移除": "Remove",
  "本地 runtime 文件缺失，需要单独确认外部初始化。": "The local runtime file is missing and requires separate external initialization confirmation.",
  "可安装的 optional 依赖已纳入本次预览；hooks / MCP / external install 仍需单独确认。": "Installable optional dependencies are included in this preview. Hooks / MCP / external install still require separate confirmation.",
  "确认执行本次安装？": "Confirm this installation?",
  "本次没有新增或更新内容。": "This run has no new or updated content.",
  "可选项，本次不会安装": "Optional item, not installed this time",
  "需要手动处理，本次不会安装": "Manual handling required, not installed this time",
  "需要手动执行，本次不会执行": "Manual execution required, not run this time",
  "无来源": "No source",
  "缺少必需组件": "Missing required components",
  "候选未确认": "Unconfirmed candidates",
  "契约引用的本地组件都存在。": "All local components referenced by the contract exist.",
  "未发现明确关联。": "No clear relation found.",
  "明确关联": "Explicit relation",
  "强关联": "Strong relation",
  "弱线索": "Weak signal",
  "Profile 引用": "Profile reference",
  "关联": "Relation",
  "目标": "Target",
  "命令依赖": "Command dependency",
  "全局基础能力": "Global core capability",
  "暂不收编": "Hold",
  "加入 profile required": "Add to profile required",
  "写入 command frontmatter": "Write command frontmatter",
  "建议": "Suggestion",
  "本地资产总量": "Local assets total",
  "新增未归类": "New unclassified",
  "缺失引用": "Missing references",
  "命令契约覆盖率": "Command contract coverage",
  "ECC 有，但 profile 未引用": "Exists in ECC but is not referenced by profiles",
  "profile 引用但 ECC 不存在": "Referenced by profiles but missing from ECC",
  "已声明": "declared",
  "待整理内容": "Pending classification",
  "找不到源文件": "Source file missing",
  "已加入可选项": "Included in optional items",
  "未加入可选项": "Not included in optional items",
  "没有找不到源文件的引用": "No references with missing source files",
  "没有未加入可选项的内容": "No unassigned optional items",
  "查看已加入可选项的内容": "View included optional items",
  "暂无已加入可选项的内容": "No included optional items yet",
  "总数": "total",
  "待整理内容的多关联分类": "Multi-relation classification for pending content",
  "一个内容可以同时出现在多个分类里；这里先呈现关联关系，后续再决定哪些要沉淀成能力包、技术栈片段或主架构。": "One item can appear in multiple categories. This view shows relations first; later you can decide what should become packs, stack fragments, or primary architectures.",
  "待人工判断": "Needs manual judgment",
  "名称和说明暂时无法稳定归类，需要人工看内容后决定。": "The name and description cannot be classified reliably yet; review the content manually.",
  "命令关联图": "Command relation graph",
  "按 command 展示它建议关联的 skills、agents、rules。这里是审计建议，不会自动改变安装结果。": "Shows suggested skills, agents, and rules for each command. These are audit suggestions and do not automatically change installation results.",
  "有关系": "related",
  "建议关系": "suggested relations",
  "frontmatter 的 requires / optional 是机器契约；Related 只作为候选线索。": "frontmatter requires / optional fields are machine contracts. Related is only a candidate signal.",
  "候选": "candidates",
  "缺失": "missing",
  "阶段、技术架构、技术栈片段和能力包引用的本地资产是否还存在。": "Checks whether local assets referenced by phases, architectures, stack fragments, and packs still exist.",
  "需要处理": "need attention",
  "没有发现缺失引用。": "No missing references found.",
  "没有找到源文件的引用": "No missing source references",
  "请先勾选要应用的建议": "Select suggestions to apply first",
  "已取消应用建议": "Suggestion application cancelled",
  "Doctor 未发现需要自动修复的项目": "Doctor found nothing that needs automatic repair",
  "安全修复已执行": "Safe repair completed",
  "项": "items",
  "类": "types",
  "skipped_existing": "Previously skipped",
  "runtime / external 待确认": "runtime / external pending",
  "还没有挂到阶段 / 架构 / 类型 / 能力包": "Not attached to a phase / architecture / type / pack yet",
  "当前阶段、架构、类型和能力包会使用": "Used by the current phase, architecture, type, and packs",
  "下方按 commands / skills / agents / rules 展开": "Expanded below by commands / skills / agents / rules",
  "可选项引用了但 ECC_HOME 不存在": "Optional references exist but are missing from ECC_HOME",
  "Claude 命令，比如 review-pr.md、python-review.md": "Claude commands such as review-pr.md and python-review.md",
  "技能目录，比如 nextjs-turbopack、github-ops": "Skill folders such as nextjs-turbopack and github-ops",
  "agent 文件，比如 rust-reviewer.md、architect.md": "Agent files such as rust-reviewer.md and architect.md",
  "规则目录，比如 rust、java、swift": "Rule folders such as rust, java, and swift",
  "勾选后才会写入 profile JSON 或 command frontmatter；未勾选的建议只作为参考。": "Only selected suggestions write profile JSON or command frontmatter. Unselected suggestions remain reference-only.",
  "找不到源文件的引用": "References with missing source files",
  "Profiles 已初始化": "Profiles initialized",
  "执行完成": "Run completed",
  ".claude 目录": ".claude folder",
  ".codex 目录": ".codex folder",
});

const PROFILE_EN = {
  "ph-init": ["Early Project", "Best for early 0-to-1 projects focused on requirements, MVP scope, technical choices, and architecture planning."],
  "ph-build": ["Feature Build", "Best for building MVP and core features with small iterations and a tight validation loop."],
  "ph-onboard": ["Existing Project Onboarding", "Best for first understanding an existing project structure, stack, key modules, and validation commands."],
  "ph-iterate": ["Existing Project Iteration", "Best for feature iteration after understanding the current structure, with small changes that follow local patterns."],
  "ph-qa": ["Late Quality Check", "Best for build fixes, code review, test coverage, and security checks after core functionality is mostly complete."],
  "ph-launch": ["Pre-launch Release", "Best for final security, deployment, performance, cost, and quality checks before release."],
  "arch-web-saas-next-postgres": ["Website / SaaS Full Stack", "Complete web app architecture: Next.js frontend, TypeScript, API, Postgres, Prisma, migrations, and error handling."],
  "arch-ai-agent-fastapi-web": ["AI Agent App", "Complete AI app architecture: Python agent, FastAPI API, Web UI, evals, prompt optimization, and cost control."],
  "arch-crawler-data-platform": ["Crawler and Data Platform", "Complete data platform architecture: Python ingestion, data cleaning, Postgres storage, API service, and lightweight web UI."],
  "arch-browser-extension-with-api": ["Browser Extension + API", "Complete extension architecture: Chrome extension, Web UI, E2E, security checks, and Node API backend."],
  "arch-devops-automation-platform": ["DevOps Automation Platform", "Complete automation platform architecture: Python automation scripts, Docker, deployment, security, cost, and network checks."],
  "saas-next-fullstack": ["Next.js SaaS Full Stack", "For Next.js / TypeScript / SaaS full-stack projects."],
  "web-react-frontend": ["React Frontend", "For React / TypeScript / Web UI projects."],
  "api-node-backend": ["Node API Backend", "For Node.js / NestJS / TypeScript API services."],
  "api-python-fastapi": ["FastAPI Backend", "For Python / FastAPI API services."],
  "api-python-django": ["Django Backend", "For Python / Django backend projects."],
  "ai-agent-python": ["Python AI Agent", "For Python agents, LLM workflows, evals, and agent harness projects."],
  "automation-script-python": ["Python Automation Scripts", "For local automation, ops scripts, and small CLI tools."],
  "crawler-python-data": ["Python Crawling and Data", "For crawling, data ingestion, cleaning, and storage projects."],
  "browser-extension-chrome": ["Chrome Browser Extension", "For Chrome extension / WebExtension projects."],
  "ml-python-pipeline": ["Python ML Pipeline", "For machine learning, eval, and experiment pipelines."],
  "infra-docker-devops": ["Docker / DevOps", "For Docker, deployment, infrastructure, and network configuration checks."],
  "code-review-pack": ["Code Review Pack", "Adds commands, skills, and agents for local code review."],
  "build-fix-pack": ["Build Fix Pack", "Adds capabilities for locating build failures, type errors, and silent failures."],
  "test-coverage-pack": ["Test Coverage Pack", "Adds test coverage analysis and test-writing capabilities."],
  "security-audit-pack": ["Security Audit Pack", "Adds security scanning, production audit, and security reviewer capabilities."],
  "content-docs-pack": ["Docs Update Pack", "Adds README, help docs, product copy, and documentation update capabilities."],
  "research-writing-pack": ["Research Writing Pack", "Adds deep research, market research, and product capability analysis."],
  "seo-content-pack": ["SEO Content Pack", "Adds SEO content, brand voice, and content production capabilities."],
  "multi-model-planning-pack": ["Multi-model Planning Pack", "Adds multi-* planning commands. External ccg-workflow runtime and ace-tool MCP require separate confirmation."],
  "prp-workflow-pack": ["PRP Requirements-to-Delivery Pack", "Adds PRP planning, requirements, implementation, commit, and PR workflow commands."],
  "github-pr-pack": ["GitHub / PR Collaboration Pack", "Adds PR creation, PR review, GitHub collaboration, and multi-reviewer analysis capabilities."],
  "session-memory-pack": ["Session / Memory Management Pack", "Adds session save/resume, project lists, checkpoints, and aside-question capabilities."],
  "continuous-learning-pack": ["Continuous Learning Pack", "Adds long-term learning and capability refinement commands such as learn, instinct, evolve, promote, and prune."],
  "ops-runtime-pack": ["Runtime / Cost Ops Pack", "Adds PM2, package-manager setup, cost reporting, and ECC auto-update commands."],
  "ecc-governance-pack": ["ECC Governance Pack", "Adds ECC guides, skill creation/health checks, codemap updates, and hookify configuration commands."],
  "language-python-pack": ["Python Language Pack", "Adds Python / FastAPI review commands, testing skills, and reviewers."],
  "language-cpp-pack": ["C++ Language Pack", "Adds C++ build / review / test commands, rules, and reviewers."],
  "language-go-pack": ["Go Language Pack", "Adds Go build / review / test commands, rules, and reviewers."],
  "language-rust-pack": ["Rust Language Pack", "Adds Rust build / review / test commands, rules, and reviewers."],
  "language-flutter-dart-pack": ["Flutter / Dart Language Pack", "Adds Flutter build / review / test commands, Dart rules, and reviewers."],
  "language-kotlin-pack": ["Kotlin / Android Language Pack", "Adds Kotlin build / review / test commands, rules, and reviewers."],
};

function sourceText(value) {
  const text = String(value ?? "");
  const match = Object.entries(I18N.en).find(([, translated]) => translated === text);
  return match ? match[0] : text;
}

function normalizeLanguage(lang) {
  const value = String(lang || "").toLowerCase();
  if (value.startsWith("en")) return "en";
  if (value.startsWith("zh")) return "zh-CN";
  return DEFAULT_LANGUAGE;
}

function initialLanguage() {
  try {
    const saved = localStorage.getItem(LANGUAGE_STORAGE_KEY);
    if (SUPPORTED_LANGUAGES.includes(saved)) return saved;
  } catch {
    // Language persistence is optional.
  }
  return normalizeLanguage(navigator.language || DEFAULT_LANGUAGE);
}

function currentLang() {
  return SUPPORTED_LANGUAGES.includes(state.lang) ? state.lang : DEFAULT_LANGUAGE;
}

function t(key, params = {}) {
  const lang = currentLang();
  const template = I18N[lang]?.[key] || I18N[DEFAULT_LANGUAGE]?.[key] || key;
  return String(template).replace(/\{(\w+)\}/g, (_match, name) => params[name] ?? "");
}

function uiText(value) {
  return uiSentence(value);
}

function uiStatusLabel(value) {
  const labels = {
    completed: "Task completed",
    completed_with_warnings: "Task completed with follow-up",
    failed: "Failed",
    ready: "Ready",
    blocked: "Blocked",
    degraded: "Degraded",
    needs_confirmation: "Needs confirmation",
    unknown: "Unknown",
    pass: "pass",
    warning: "warning",
    fail: "fail",
    ok: "ok",
    info: "info",
    error: "error",
  };
  if (currentLang() !== "en") return value ?? "";
  return labels[value] || uiSentence(value);
}

function translateProfileFragments(text) {
  const fragments = {
    "项目初期": "Early Project",
    "功能开发中": "Feature Build",
    "接手已有项目": "Existing Project Onboarding",
    "已有项目二次开发": "Existing Project Iteration",
    "后期质量检查": "Late Quality Check",
    "上线发布前": "Pre-launch Release",
    "网站 / SaaS 全栈": "Website / SaaS Full Stack",
    "AI Agent 应用": "AI Agent App",
    "爬虫与数据平台": "Crawler and Data Platform",
    "浏览器扩展 + API": "Browser Extension + API",
    "DevOps 自动化平台": "DevOps Automation Platform",
    "Next.js SaaS 全栈": "Next.js SaaS Full Stack",
    "React 前端": "React Frontend",
    "Node API 后端": "Node API Backend",
    "FastAPI 后端": "FastAPI Backend",
    "Django 后端": "Django Backend",
    "Python 自动化脚本": "Python Automation Scripts",
    "Python 爬虫与数据": "Python Crawling and Data",
    "Chrome 浏览器扩展": "Chrome Browser Extension",
    "代码审查包": "Code Review Pack",
    "构建修复包": "Build Fix Pack",
    "测试覆盖包": "Test Coverage Pack",
    "安全审计包": "Security Audit Pack",
    "文档更新包": "Docs Update Pack",
    "调研写作包": "Research Writing Pack",
    "SEO 内容包": "SEO Content Pack",
    "多模型规划包": "Multi-model Planning Pack",
    "PRP 需求到交付包": "PRP Requirements-to-Delivery Pack",
    "GitHub / PR 协作包": "GitHub / PR Collaboration Pack",
    "会话 / 记忆管理包": "Session / Memory Management Pack",
    "连续学习包": "Continuous Learning Pack",
    "运行时 / 成本运维包": "Runtime / Cost Ops Pack",
    "ECC 治理包": "ECC Governance Pack",
    "Python 语言包": "Python Language Pack",
    "C++ 语言包": "C++ Language Pack",
    "Go 语言包": "Go Language Pack",
    "Rust 语言包": "Rust Language Pack",
    "Flutter / Dart 语言包": "Flutter / Dart Language Pack",
    "Kotlin / Android 语言包": "Kotlin / Android Language Pack",
  };
  return Object.entries(fragments).reduce((out, [from, to]) => out.replaceAll(from, to), text);
}

function uiSentence(value) {
  if (value === null || value === undefined) return "";
  const original = String(value);
  if (currentLang() !== "en") return original;
  let text = sourceText(original);
  const exact = t(text);
  if (exact !== text) return exact;
  text = translateProfileFragments(text);
  const replacements = [
    [/^(\d+) 项$/, "$1 items"],
    [/^(\d+) 个$/, "$1"],
    [/^(.+) 类$/, "$1 types"],
    [/^(.+) 个 profile$/, "$1 profiles"],
    [/^Profiles 已初始化：(.+) 个文件$/, "Profiles initialized: $1 files"],
    [/^扫描失败：(.+)$/, "Scan failed: $1"],
    [/^已向系统发送打开请求：(.+)$/, "Sent open request to the system: $1"],
    [/^无法打开 (.+)：(.+)$/, "Could not open $1: $2"],
    [/^无法打开目录选择窗口：(.+)$/, "Could not open the folder picker: $1"],
    [/^选择项目目录失败：(.+)$/, "Project folder selection failed: $1"],
    [/^选择目录失败：(.+)$/, "Folder selection failed: $1"],
    [/^项目目录已选择，但扫描失败：(.+)$/, "Project folder selected, but scan failed: $1"],
    [/^初始化项目能力：(.+)$/, "Initialize project capabilities: $1"],
    [/^添加项目能力：(.+)$/, "Add project capabilities: $1"],
    [/^追加项目阶段能力：(.+)$/, "Add project phase capabilities: $1"],
    [/^执行项目能力变更：(.+)$/, "Run project capability change: $1"],
    [/^已经添加 (\d+)$/, "already added $1"],
    [/^新增 (\d+)$/, "add $1"],
    [/^更新 (\d+)$/, "update $1"],
    [/^待确认 (\d+)$/, "pending $1"],
    [/^问题 (\d+)$/, "issues $1"],
    [/^(.+) 个关联内容$/, "$1 related items"],
    [/^(.+) 个未加入可选项$/, "$1 not included in optional items"],
    [/^(.+) 总数$/, "$1 total"],
    [/^(.+) 已加入可选项$/, "$1 included"],
    [/^(.+) 未加入可选项$/, "$1 not included"],
    [/^(.+) 找不到源文件$/, "$1 source files missing"],
    [/^(.+) 条建议$/, "$1 suggestions"],
    [/^(.+) 个 profile 或 command 依赖引用找不到源文件。$/, "$1 profile or command dependency references cannot find source files."],
    [/^(.+) 条建议可用于归类或补充命令依赖。$/, "$1 suggestions can classify content or supplement command dependencies."],
    [/^(.+) blocked，(.+) degraded，(.+) unknown。$/, "$1 blocked, $2 degraded, $3 unknown."],
    [/^(.+) 个 command 缺少必需组件。$/, "$1 commands are missing required components."],
    [/^(.+) 个源组件缺失。$/, "$1 source components are missing."],
    [/^(.+) 个目标已有冲突，执行时会跳过。$/, "$1 targets have conflicts and will be skipped during execution."],
    [/^执行后生成 (.+)。$/, "Generate $1 after execution."],
    [/^已验证 (.+) 个 required symlink。$/, "Verified $1 required symlinks."],
    [/^已验证 (.+) 个 Codex command\/skill\/agent\/rule 组件。$/, "Verified $1 Codex command/skill/agent/rule components."],
    [/^已验证 (.+) 个 Antigravity agent\/workflow\/rule\/skill 组件。$/, "Verified $1 Antigravity agent/workflow/rule/skill components."],
    [/^已验证 (.+) 个 Antigravity workflow\/rule\/skill 组件。$/, "Verified $1 Antigravity workflow/rule/skill components."],
    [/^可完整运行：(.+)$/, "Ready: $1"],
    [/^(.+) 个 error，需要先处理。$/, "$1 errors need to be handled first."],
    [/^(.+) 个 warning，需要跟进。$/, "$1 warnings need follow-up."],
    [/^已检查 (.+) 个源组件，未发现缺失$/, "Checked $1 source components; no missing files found"],
    [/^下一步可在 Claude Code 中运行：(.+)$/, "Next commands to run in Claude Code: $1"],
    [/^在项目 CLAUDE.md 中加入 @(.+)，让 Claude Code 自动读取生成说明。$/, "Add @$1 to CLAUDE.md so Claude Code automatically reads the generated instructions."],
    [/^查看 Doctor 的 (.+) 个 warning，能自动修复的可运行安全修复。$/, "Review $1 Doctor warnings. Run safe repair for items that can be fixed automatically."],
    [/^确认应用 (.+) 条治理建议？这会写入 profile JSON 或 command frontmatter。$/, "Apply $1 governance suggestions? This writes profile JSON or command frontmatter."],
    [/^已应用 (.+) 条建议，跳过 (.+) 条$/, "Applied $1 suggestions, skipped $2."],
    [/^安全修复已执行：(.+) 项$/, "Safe repair completed: $1 items"],
    [/^移除 (.+)$/, "Remove $1"],
    [/^确认移除 (.+)？\n\n只会删除仍然指向 ECC 源文件的 symlink；真实文件和冲突项会保留。$/, "Remove $1?\n\nOnly symlinks that still point to ECC source files will be deleted. Real files and conflict items are preserved."],
    [/^已移除 (.+)$/, "Removed $1"],
    [/^移除 (.+) 失败$/, "Failed to remove $1"],
    [/^来源：(.+)$/, "Source: $1"],
    [/^源：(.+) · 目标：(.+)$/, "Source: $1 · Target: $2"],
    [/^目标：(.+)$/, "Target: $1"],
    [/^外部初始化：(.+)$/, "External install: $1"],
    [/^缺少必需组件：(.+)$/, "Missing required components: $1"],
    [/^Runtime 待确认：(.+)$/, "Runtime pending: $1"],
    [/^Optional 未启用：(.+)$/, "Optional not enabled: $1"],
    [/^原因：(.+)$/, "Reason: $1"],
  ];
  for (const [pattern, replacement] of replacements) {
    if (pattern.test(text)) return text.replace(pattern, replacement);
  }
  return text;
}

function profileName(profile) {
  if (!profile) return "";
  return currentLang() === "en"
    ? profile.name_en || PROFILE_EN[profile.id]?.[0] || profile.name_zh || profile.id || ""
    : profile.name_zh || profile.name_en || profile.id || "";
}

function profileDescription(profile) {
  if (!profile) return "";
  return currentLang() === "en"
    ? profile.description_en || PROFILE_EN[profile.id]?.[1] || profile.description_zh || ""
    : profile.description_zh || profile.description_en || "";
}

function localizedName(item) {
  if (!item) return "";
  return currentLang() === "en"
    ? item.name_en || t(item.name_zh || item.name || item.id || "")
    : item.name_zh || item.name_en || item.name || item.id || "";
}

function localizedDescription(item) {
  if (!item) return "";
  return currentLang() === "en"
    ? item.description_en || t(item.description_zh || item.description || "")
    : item.description_zh || item.description_en || item.description || "";
}

function translateText(value) {
  return currentLang() === DEFAULT_LANGUAGE ? value : t(value);
}

function localizeElementText(el) {
  if (!el.dataset.i18nOriginal) el.dataset.i18nOriginal = sourceText(el.textContent);
  else el.dataset.i18nOriginal = sourceText(el.dataset.i18nOriginal);
  const next = translateText(el.dataset.i18nOriginal);
  if (el.textContent !== next) el.textContent = next;
}

function localizeElementAttribute(el, attr, dataKey) {
  if (!el.dataset[dataKey]) el.dataset[dataKey] = sourceText(el.getAttribute(attr) || "");
  else el.dataset[dataKey] = sourceText(el.dataset[dataKey]);
  const original = el.dataset[dataKey];
  if (original) {
    const next = translateText(original);
    if (el.getAttribute(attr) !== next) el.setAttribute(attr, next);
  }
}

function localizeTree(root = document.body) {
  if (!root) return;
  document.documentElement.lang = currentLang();
  $$("[data-i18n]").forEach(localizeElementText);
  $$("[data-i18n-placeholder]").forEach((el) => localizeElementAttribute(el, "placeholder", "i18nPlaceholderOriginal"));
  $$("[data-i18n-aria-label]").forEach((el) => localizeElementAttribute(el, "aria-label", "i18nAriaLabelOriginal"));
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT);
  const elements = root.nodeType === Node.ELEMENT_NODE ? [root] : [];
  while (walker.nextNode()) elements.push(walker.currentNode);
  for (const el of elements) {
    if (el.dataset?.i18n || el.closest?.("script, style, code")) continue;
    if (el.childNodes.length === 1 && el.firstChild.nodeType === Node.TEXT_NODE) {
      const text = el.textContent.trim();
      if (text && (I18N.en[text] || sourceText(text) !== text)) localizeElementText(el);
    }
    if (el.hasAttribute?.("placeholder")) localizeElementAttribute(el, "placeholder", "i18nPlaceholderOriginal");
    if (el.hasAttribute?.("aria-label")) localizeElementAttribute(el, "aria-label", "i18nAriaLabelOriginal");
    if (el.hasAttribute?.("title")) localizeElementAttribute(el, "title", "i18nTitleOriginal");
  }
  updateLanguageSwitcher();
}

function refreshCurrentView() {
  updateTopbar();
  renderCatalog();
  renderSettings();
  if (state.scan) renderProjectCards(state.scan);
  else renderNoProjectSelected();
  if (state.currentPlan && activePageId() === "preview") renderPreview(state.currentPlan);
  else if (activePageId() === "task") renderTaskResult(state.lastTaskRun);
  else if (activePageId() === "status") refreshStatus().catch((error) => toast(`${t("刷新状态失败")}：${error.message}`));
  else if (activePageId() === "assets" && state.assetScan) refreshAssets().catch((error) => toast(`${t("刷新资产盘点失败")}：${error.message}`));
  else if (state.currentPlan) renderPlanDetail(state.currentPlan);
  else renderInstalledDetail(state.scan);
  localizeTree();
}

function setLang(lang) {
  state.lang = normalizeLanguage(lang);
  try {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, state.lang);
  } catch {
    // Language persistence is optional.
  }
  refreshCurrentView();
}

function updateLanguageSwitcher() {
  $$(".language-option").forEach((button) => {
    const active = button.dataset.lang === currentLang();
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  });
}

function savedProjectPath() {
  try {
    return sessionStorage.getItem(PROJECT_PATH_STORAGE_KEY) || loadRecentProjects()[0] || "";
  } catch {
    return "";
  }
}

function saveProjectPath(path) {
  if (!path) return;
  try {
    sessionStorage.setItem(PROJECT_PATH_STORAGE_KEY, path);
    rememberProjectPath(path);
  } catch {
    // Browser storage may be unavailable in private or restricted contexts.
  }
}

function loadRecentProjects() {
  try {
    const paths = JSON.parse(localStorage.getItem(PROJECT_RECENTS_STORAGE_KEY) || "[]");
    return Array.isArray(paths) ? paths.filter(Boolean) : [];
  } catch {
    return [];
  }
}

function rememberProjectPath(path) {
  try {
    const next = [path, ...loadRecentProjects().filter((item) => item !== path)].slice(0, 6);
    localStorage.setItem(PROJECT_RECENTS_STORAGE_KEY, JSON.stringify(next));
  } catch {
    // Recent projects are a convenience, not required for core behavior.
  }
}

function hasProjectPath() {
  return Boolean(currentProjectPath());
}

function currentProjectPath() {
  return (($("#projectPath").value || $("#projectPickerPath")?.value || "")).trim();
}

async function api(path, body = null) {
  const headers = { "Content-Type": "application/json" };
  if (state.csrfToken) headers["X-ECC-Manager-Token"] = state.csrfToken;
  const options = body
    ? { method: "POST", headers, body: JSON.stringify(body) }
    : {};
  const response = await fetch(path, options);
  const contentType = response.headers.get("Content-Type") || "";
  if (!contentType.includes("application/json")) {
    const text = await response.text();
    const hint = text.trim().startsWith("<")
      ? "接口未返回 JSON，可能是服务进程还没有重启"
      : text.trim();
    throw new Error(hint || `请求失败：${response.status}`);
  }
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `请求失败：${response.status}`);
  return data;
}

function toast(message) {
  const el = $("#toast");
  el.textContent = uiSentence(message);
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2600);
}

async function withToast(action, failurePrefix) {
  try {
    return await action();
  } catch (error) {
    toast(`${t(failurePrefix)}：${error.message}`);
    return null;
  }
}

function shortPath(value) {
  if (!value) return t("未设置");
  return state.homeDir && value.startsWith(state.homeDir)
    ? value.replace(state.homeDir, "~")
    : value;
}

function escapeAttr(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function escapeList(values, separator = ", ", empty = "无") {
  const items = (values || []).map((item) => escapeHtml(item));
  return items.length ? items.join(separator) : t(empty);
}

function badge(status) {
  const map = {
    ok: "ok",
    linked: "ok",
    created: "ok",
    missing: "warning",
    missing_source: "error",
    broken: "error",
    warning: "warning",
    error: "error",
    info: "info",
    existing_real: "warning",
    foreign_symlink: "warning",
  };
  return `<span class="badge ${map[status] || ""}">${escapeHtml(uiStatusLabel(status || "unknown"))}</span>`;
}

function issueLevelBadge(level) {
  const map = { info: "info", warning: "warning", error: "error", fail: "error" };
  return `<span class="badge ${map[level] || ""}">${escapeHtml(t(level || "info"))}</span>`;
}

function renderIssueActions(issue) {
  const actions = issue?.actions || [];
  if (!actions.length) {
    return `<span class="muted">${escapeHtml(t("无需操作"))}</span>`;
  }
  return actions.map((action) => {
    if (action.mode === "manual" || action.kind === "manual_guide") {
      return `<span class="issue-guide">${escapeHtml(uiSentence(action.label))}：${escapeHtml(uiSentence(action.description || ""))}</span>`;
    }
    return `<button type="button" class="secondary issue-action" data-issue-action="${escapeAttr(action.kind)}" data-action="${escapeAttr(JSON.stringify(action))}">${escapeHtml(uiSentence(action.label || action.kind))}</button>`;
  }).join("");
}

function renderIssuesPanel(title, issues, emptyText = "没有需要处理的问题。") {
  const visible = (issues || []).filter((issue) => ["info", "warning", "error", "fail"].includes(issue.level));
  if (!visible.length) {
    return `<section class="issue-panel"><h2>${escapeHtml(t(title))}</h2><div class="empty">${escapeHtml(t(emptyText))}</div></section>`;
  }
  return `
    <section class="issue-panel">
      <div class="asset-classification-head">
        <div>
          <h2>${escapeHtml(t(title))}</h2>
          <p class="muted">${escapeHtml(t("每个问题都包含影响和下一步选项。"))}</p>
        </div>
        <div class="pack-meta">
          <span class="badge warning">${escapeHtml(visible.filter((item) => item.level === "warning").length)} warning</span>
          <span class="badge error">${escapeHtml(visible.filter((item) => item.level === "error" || item.level === "fail").length)} error</span>
          <span class="badge info">${escapeHtml(visible.filter((item) => item.level === "info").length)} info</span>
        </div>
      </div>
      <div class="issue-list">
        ${visible.map((issue) => `
          <article class="issue-row">
            ${issueLevelBadge(issue.level)}
            <div>
              <strong>${escapeHtml(uiSentence(issue.title || issue.id))}</strong>
              <p>${escapeHtml(uiSentence(issue.message || ""))}</p>
              <p class="muted">${escapeHtml(t("影响："))}${escapeHtml(uiSentence(issue.impact || "需要确认后处理。"))}</p>
            </div>
            <div class="issue-actions">${renderIssueActions(issue)}</div>
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

async function runDoctorFixWithConfirm() {
  if (!window.confirm(uiSentence("确认运行 Doctor 安全修复？只会修复托管且可恢复的项目，不会覆盖用户文件。"))) {
    toast("已取消安全修复");
    return;
  }
  await runDoctor(true);
  setPage("doctor");
}

async function handleIssueAction(action) {
  if (!action) return;
  if (action.kind === "navigate") {
    setPage(action.page || "status");
    return;
  }
  if (action.kind === "preview_full_config") {
    const profiles = state.lastTaskRun?.profiles || state.scan?.lock?.last_task_run?.profiles || [];
    if (!profiles.length) {
      toast("没有找到上一任务的 profile，无法生成满配预览");
      return;
    }
    state.lastActionPage = "task";
    await makePlan("add", profiles, { includeOptional: true });
    return;
  }
  if (action.kind === "doctor_fix") {
    await runDoctorFixWithConfirm();
    return;
  }
  if (action.kind === "apply_suggestions") {
    await applySelectedSuggestions();
    return;
  }
  toast(action.description || "请按提示手动处理");
}

function setPage(page) {
  $$(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.page === page));
  $$(".page").forEach((item) => item.classList.toggle("active", item.id === `page-${page}`));
  if (page === "phases") renderCatalog();
  if (page === "assets") withToast(refreshAssets, "刷新资产盘点失败");
  if (page === "preview") {
    if (state.currentPlan) renderPlanDetail(state.currentPlan);
    else renderInstalledDetail(state.scan);
  }
  if (page === "task") renderTaskResult(state.lastTaskRun);
  if (page === "status") withToast(refreshStatus, "刷新状态失败");
  if (page === "doctor") withToast(() => runDoctor(false), "Doctor 检查失败");
  localizeTree();
}

function updateTopbar() {
  const topProject = $("#topProject");
  const topEcc = $("#topEcc");
  const topProfiles = $("#topProfiles");
  const topPlan = $("#topPlan");
  if (topProject) topProject.textContent = $("#projectPath").value ? shortPath($("#projectPath").value) : t("未选择");
  if (topEcc) topEcc.textContent = state.scan ? state.scan.ecc_status : t("未检测");
  if (topProfiles) topProfiles.textContent = state.scan ? state.scan.profiles_status : t("未检测");
  if (topPlan) topPlan.textContent = state.scan ? state.scan.global_plan_status : t("未检测");
  renderProjectPicker();
}

function renderProjectPicker() {
  const recentContainer = $("#recentProjects");
  if (!recentContainer) return;
  const current = $("#projectPath").value || savedProjectPath() || "";
  const pickerInput = $("#projectPickerPath");
  if (pickerInput && document.activeElement !== pickerInput) pickerInput.value = current;
  const recentProjects = loadRecentProjects();
  recentContainer.innerHTML = recentProjects.length
    ? `
      <div class="recent-title">${escapeHtml(t("最近项目"))}</div>
      ${recentProjects.map((path) => `
        <button class="recent-project ${path === current ? "active" : ""}" type="button" data-recent-project="${escapeAttr(path)}">
          <span>${escapeHtml(shortPath(path))}</span>
          <small>${escapeHtml(path)}</small>
        </button>
      `).join("")}
    `
    : `<div class="empty compact-empty">${escapeHtml(t("还没有最近项目。"))}</div>`;
}

function setProjectPickerOpen(isOpen) {
  const picker = $("#projectPicker");
  if (!picker) return;
  picker.hidden = !isOpen;
  $("#topProjectPicker")?.classList.toggle("active", isOpen);
  if (isOpen) {
    renderProjectPicker();
    $("#projectPickerPath")?.focus();
    $("#projectPickerPath")?.select();
  }
}

function activePageId() {
  return $(".page.active")?.id?.replace(/^page-/, "") || "";
}

function profileCounts(profile) {
  const collected = collectProfileItems(profile);
  return {
    commands: collected.commands.size,
    skills: collected.skills.size,
    agents: collected.agents.size,
    rules: collected.rules.size,
    runtime: collected.runtime.size,
    optional: collected.optional.size,
  };
}

function profileIncludeIds(profile) {
  const includes = profile?.includes;
  if (Array.isArray(includes)) return includes.filter(Boolean);
  if (!includes || typeof includes !== "object") return [];
  return Object.values(includes).flatMap((items) => Array.isArray(items) ? items : [items]).filter(Boolean);
}

function collectProfileItems(profile, seen = new Set()) {
  const out = {
    commands: new Set(),
    skills: new Set(),
    agents: new Set(),
    rules: new Set(),
    runtime: new Set(),
    optional: new Set(),
  };
  if (!profile || seen.has(profile.id)) return out;
  seen.add(profile.id);
  for (const includeId of profileIncludeIds(profile)) {
    const child = profileById(includeId);
    const childItems = collectProfileItems(child, seen);
    Object.keys(out).forEach((key) => childItems[key].forEach((item) => out[key].add(item)));
  }
  const required = profile.required || {};
  const optional = profile.optional || {};
  ["commands", "skills", "agents", "rules", "runtime"].forEach((kind) => {
    (required[kind] || []).forEach((item) => out[kind].add(item));
  });
  Object.entries(optional).forEach(([kind, items]) => {
    (items || []).forEach((item) => out.optional.add(`${kind}/${item}`));
  });
  return out;
}

function isArchitectureProfile(profile) {
  return profile?.type === "architecture" || profile?.preset_kind === "architecture" || String(profile?.id || "").startsWith("arch-");
}

function normalizedCatalogProfiles() {
  const rawArchitectures = Object.values(state.catalog.architectures || {});
  const rawProjectTypes = Object.values(state.catalog["project-types"] || {});
  const byId = new Map();
  [...rawArchitectures, ...rawProjectTypes.filter(isArchitectureProfile)].forEach((profile) => {
    byId.set(profile.id, { ...profile, type: "architecture" });
  });
  return {
    architectures: Array.from(byId.values()),
    projectTypes: rawProjectTypes.filter((profile) => !isArchitectureProfile(profile)),
  };
}

function renderProjectCards(scan) {
  const generatedName = scan.generated_claude_file || "CLAUDE.ecc.generated.md";
  const generatedCodexName = scan.generated_codex_file || "AGENTS.ecc.generated.md";
  const generatedAntigravityName = scan.generated_antigravity_file || "ANTIGRAVITY.ecc.generated.md";
  const compatibility = scan.ecc_compatibility || {};
  const obsoleteCodexCount = (scan.obsolete_codex_artifacts || []).length;
  const legacyAntigravityRows = scan.has_antigravity_legacy_workflows
    ? [[".agent/workflows", "旧版残留", "warning", "Antigravity 新版默认使用 .agents/workflows；Doctor 会提示未记录旧产物"]]
    : [];
  const obsoleteCodexRows = obsoleteCodexCount
    ? [[".codex/commands", `${obsoleteCodexCount} 个旧版 command 残留`, "warning", "旧版 ECC Manager 写入的位置；现在 commands 适配为 .agents/skills，可在 Doctor 里安全修复"]]
    : [];
  const targetRow = (enabled, exists, label, enabledNote, disabledNote = `${label} 目标未启用`) => [
    label,
    exists ? (enabled ? "存在" : "已存在") : (enabled ? "缺失" : "未启用"),
    exists ? (enabled ? "ok" : "info") : (enabled ? "warning" : "info"),
    enabled ? enabledNote : disabledNote,
  ];
  const cards = [
    {
      title: "基础路径",
      rows: [
        ["ECC 源仓库", shortPath(scan.ecc_home), scan.ecc_status, "ECC 组件的来源目录"],
        ["ECC 版本兼容", compatibility.status || "unknown", compatibility.status === "supported" ? "ok" : "warning", compatibility.message || "未检测到兼容性信息"],
        ["Profile 配置", shortPath(scan.profile_home), scan.profiles_status, "阶段、技术架构、技术栈片段和能力包配置"],
      ],
    },
    {
      title: "当前项目检查结果",
      rows: [
        ["项目目录", scan.exists ? "存在" : "不存在", scan.exists ? "ok" : "error", scan.exists ? "当前被管理的项目路径" : "请先创建目录或选择已有项目"],
        targetRow(scan.claude_enabled, scan.has_claude_dir, ".claude", "项目级 Claude 配置目录", "Claude Code 目标未启用"),
        targetRow(scan.claude_enabled, scan.has_claude_md, "CLAUDE.md", "项目说明入口", "Claude Code 目标未启用"),
        targetRow(scan.claude_enabled, scan.has_generated, generatedName, "ECC 自动生成内容", "Claude Code 目标未启用"),
        targetRow(scan.codex_enabled || scan.antigravity_enabled, scan.has_codex_skills, ".agents/skills", "Codex / Antigravity workspace skills；Codex commands 会适配为 skills", "Codex / Antigravity 目标未启用"),
        targetRow(scan.codex_enabled, scan.has_codex_dir, ".codex/agents", "Codex custom agents", "Codex 目标未启用"),
        targetRow(scan.codex_enabled, scan.has_codex_rules, ".codex/rules", "Codex project rules", "Codex 目标未启用"),
        targetRow(scan.antigravity_enabled, scan.has_antigravity_agents, ".agents/agents.md", "Antigravity agent personas", "Antigravity 目标未启用"),
        targetRow(scan.antigravity_enabled, scan.has_antigravity_rules, ".agents/rules", "Antigravity workspace rules", "Antigravity 目标未启用"),
        targetRow(scan.antigravity_enabled, scan.has_antigravity_workflows, ".agents/workflows", "Antigravity workflows", "Antigravity 目标未启用"),
        ...legacyAntigravityRows,
        ...obsoleteCodexRows,
        ["AGENTS.md", scan.has_agents_md_managed_block || scan.has_agents_md_antigravity_block ? "托管区已写入" : (scan.has_agents_md ? "存在" : (scan.codex_enabled || scan.antigravity_enabled ? "缺失" : "未启用")), scan.has_agents_md_managed_block || scan.has_agents_md_antigravity_block ? "ok" : (scan.codex_enabled || scan.antigravity_enabled ? "warning" : "info"), scan.codex_enabled || scan.antigravity_enabled ? "Codex / Antigravity 自动读取的项目指令入口" : "Codex / Antigravity 目标未启用"],
        targetRow(scan.codex_enabled, scan.has_generated_codex, generatedCodexName, "ECC 为 Codex 生成的完整说明", "Codex 目标未启用"),
        targetRow(scan.antigravity_enabled, scan.has_generated_antigravity, generatedAntigravityName, "ECC 为 Antigravity 生成的完整说明", "Antigravity 目标未启用"),
        [".ecc-manager/ecc-lock/profile.json", scan.has_lock ? "存在" : "缺失", scan.has_lock ? "ok" : "warning", scan.has_lock ? "已记录安装的 profiles" : "初始化后记录项目配置"],
      ],
    },
  ];
  $("#projectCards").innerHTML = cards
    .map((card) => `
      <article class="status-card">
        <h3>${escapeHtml(t(card.title))}</h3>
        ${card.rows.map(([label, value, status, note]) => `
          <div class="status-line">
            <span class="status-label">
              <span>${escapeHtml(t(label))}</span>
              <small>${escapeHtml(t(note))}</small>
            </span>
            <span>${escapeHtml(t(value))} ${badge(status)}</span>
          </div>
        `).join("")}
      </article>
    `)
    .join("");
  const issues = [];
  if (scan.ecc_status !== "ok") {
    issues.push({ id: "project-ecc-home", level: "error", title: "ECC_HOME 不可用", message: scan.ecc_home, impact: "无法读取 ECC 源组件。", actions: [{ kind: "navigate", label: "打开设置", description: "检查 ECC_HOME。", mode: "navigation", page: "settings" }] });
  }
  if (scan.profiles_status !== "ok") {
    issues.push({ id: "project-profiles", level: "warning", title: "Profile 配置不可用", message: scan.profile_home, impact: "无法读取阶段、架构、能力包配置。", actions: [{ kind: "navigate", label: "打开设置", description: "检查 PROFILE_HOME。", mode: "navigation", page: "settings" }] });
  }
  if (!scan.has_lock) {
    issues.push({ id: "project-lock", level: "warning", title: "项目未初始化或缺少 lock", message: ".ecc-manager/ecc-lock/profile.json 缺失。", impact: "系统无法确认当前项目已安装哪些 ECC 能力。", actions: [{ kind: "navigate", label: "去初始化", description: "选择 profile 后生成初始化预览。", mode: "navigation", page: "init" }] });
  }
  const missingTargets = [];
  if ((scan.codex_enabled || scan.antigravity_enabled) && !scan.has_codex_skills) missingTargets.push(".agents/skills");
  if (scan.codex_enabled && !scan.has_codex_dir) missingTargets.push(".codex/agents");
  if (scan.codex_enabled && !scan.has_codex_rules) missingTargets.push(".codex/rules");
  if (scan.antigravity_enabled && !scan.has_antigravity_agents) missingTargets.push(".agents/agents.md");
  if (scan.antigravity_enabled && !scan.has_antigravity_rules) missingTargets.push(".agents/rules");
  if (scan.antigravity_enabled && !scan.has_antigravity_workflows) missingTargets.push(".agents/workflows");
  if ((scan.codex_enabled || scan.antigravity_enabled) && !(scan.has_agents_md_managed_block || scan.has_agents_md_antigravity_block)) missingTargets.push("AGENTS.md 托管区");
  if (missingTargets.length) {
    issues.push({ id: "project-targets-missing", level: "warning", title: "目标能力文件缺失", message: missingTargets.slice(0, 5).join("；") + (missingTargets.length > 5 ? `；另有 ${missingTargets.length - 5} 个` : ""), impact: "这些目标缺失时，对应 AI 工具读取不到完整 ECC 能力。", actions: [{ kind: "navigate", label: "去初始化", description: "生成初始化或追加能力预览。", mode: "navigation", page: "init" }, { kind: "navigate", label: "查看 Doctor", description: "检查是否可安全修复。", mode: "navigation", page: "doctor" }] });
  }
  if (scan.has_antigravity_legacy_workflows || obsoleteCodexCount) {
    issues.push({ id: "project-legacy-artifacts", level: "warning", title: "存在旧版或未记录产物", message: "检测到旧版 Antigravity/Codex 产物。", impact: "旧产物可能造成工具读取混乱。", actions: [{ kind: "navigate", label: "查看 Doctor", description: "打开 Doctor 检查遗留产物。", mode: "navigation", page: "doctor" }] });
  }
  $("#projectCards").insertAdjacentHTML("afterbegin", renderIssuesPanel("项目问题与选项", issues, "项目检查没有 warning/error。"));
}

function renderNoProjectSelected() {
  state.scan = null;
  $("#projectCards").innerHTML = `
    <article class="status-card">
      <h3>${escapeHtml(t("请选择项目目录"))}</h3>
      <div class="empty">${escapeHtml(t("点击“选择项目目录”，选择要由 ECC Manager 管理的项目。"))}</div>
    </article>
  `;
  updateTopbar();
}

function profileCard(profile, selected, type) {
  const counts = profileCounts(profile);
  const alreadyAdded = type === "init-pack" && packStatus(profile.id);
  const presetLabel = type === "architecture" ? `<span class="badge ok">${escapeHtml(t("主架构"))}</span>` : "";
  const commandBadge = counts.commands
    ? `<span class="badge">${counts.commands} commands</span>`
    : type === "architecture" || type === "project-type"
      ? `<span class="badge info">${escapeHtml(t("命令由阶段/能力包提供"))}</span>`
      : '<span class="badge">0 commands</span>';
  return `
    <div class="choice ${selected ? "selected" : ""} ${alreadyAdded ? "is-installed" : ""}" data-profile="${escapeAttr(profile.id)}" data-type="${escapeAttr(type)}">
      <div class="choice-title">
        <strong>${escapeHtml(profileName(profile) || profile.id)}</strong>
        ${presetLabel}
        ${alreadyAdded ? `<span class="badge ok">${escapeHtml(t("已经添加过了"))}</span>` : ""}
      </div>
      <div class="muted">${escapeHtml(profileDescription(profile))}</div>
      <span class="id">${escapeHtml(profile.id)}</span>
      <div class="pack-meta">
        ${commandBadge}
        <span class="badge">${counts.skills} skills</span>
        <span class="badge">${counts.agents} agents</span>
      </div>
    </div>
  `;
}

function phaseStatus(id) {
  const lock = state.scan?.lock || {};
  if (lock.initial_phase === id) return t("初始阶段");
  if ((lock.added_phases || []).includes(id)) return t("已追加");
  return "";
}

function packStatus(id) {
  return (state.scan?.lock?.packs || []).includes(id) ? t("已经添加过了") : "";
}

function stagePhaseCard(profile, selected) {
  const counts = profileCounts(profile);
  const status = phaseStatus(profile.id);
  return `
    <div class="choice ${selected ? "selected" : ""} ${status ? "is-installed" : ""}" data-profile="${escapeAttr(profile.id)}" data-type="stage-phase">
      <div class="choice-title">
        <strong>${escapeHtml(profileName(profile) || profile.id)}</strong>
        ${status ? `<span class="badge ok">${status}</span>` : ""}
      </div>
      <div class="muted">${escapeHtml(profileDescription(profile))}</div>
      <span class="id">${escapeHtml(profile.id)}</span>
      <div class="pack-meta">
        <span class="badge">${counts.commands} commands</span>
        <span class="badge">${counts.skills} skills</span>
        <span class="badge">${counts.agents} agents</span>
      </div>
    </div>
  `;
}

function selectedStagePhaseIds() {
  return Array.from(state.selectedStagePhases);
}

function actionableSelectedStagePhaseIds() {
  return selectedStagePhaseIds().filter((id) => !phaseStatus(id));
}

function ensureSelectedStagePhases(phases) {
  if (!phases.length) {
    state.selectedStagePhases.clear();
    return;
  }
  for (const id of selectedStagePhaseIds()) {
    if (!state.catalog.phases[id] || phaseStatus(id)) state.selectedStagePhases.delete(id);
  }
  if (state.selectedStagePhases.size) return;
  const next = phases.find((phase) => !phaseStatus(phase.id));
  if (next) state.selectedStagePhases.add(next.id);
}

function renderStageSummary() {
  const hasLock = Boolean(state.scan?.has_lock);
  const lock = state.scan?.lock || {};
  const selectedIds = selectedStagePhaseIds();
  const actionIds = actionableSelectedStagePhaseIds();
  $("#previewStageBtn").disabled = !hasLock || !actionIds.length;
  $("#applyStageBtn").disabled = !hasLock || !actionIds.length;
  $("#stageSummary").innerHTML = `
    <article class="status-card">
      <h3>${escapeHtml(t("当前阶段"))}</h3>
      <div class="status-line">
        <span class="status-label"><span>${escapeHtml(t("初始阶段"))}</span><small>${escapeHtml(t("第一次初始化时选定，作为项目起点保留"))}</small></span>
        <span>${escapeHtml(lock.initial_phase || t("未设置"))}</span>
      </div>
      <div class="status-line">
        <span class="status-label"><span>${escapeHtml(t("已追加阶段"))}</span><small>${escapeHtml(t("项目推进后追加的阶段能力"))}</small></span>
        <span>${escapeList(lock.added_phases)}</span>
      </div>
      ${hasLock ? "" : `<div class="empty">${escapeHtml(t("当前项目还没有 ECC lock。请先到“初始化”完成第一次装配，再从这里追加阶段。"))}</div>`}
      ${hasLock && !actionIds.length ? `<div class="empty">${escapeHtml(t("请选择至少一个未启用阶段。"))}</div>` : ""}
      ${selectedIds.length ? `<div class="empty compact-empty">${escapeHtml(t("本次将追加："))}${escapeList(actionIds, "、", t("无"))}</div>` : ""}
    </article>
  `;
}

function renderCatalog() {
  const phases = Object.values(state.catalog.phases);
  const { architectures, projectTypes } = normalizedCatalogProfiles();
  const packs = Object.values(state.catalog.packs);
  ensureSelectedStagePhases(phases);
  if (architectures.length && !architectures.some((profile) => profile.id === state.selectedArchitecture)) {
    state.selectedArchitecture = architectures[0].id;
  }

  $("#phaseChoices").innerHTML = phases.map((p) => profileCard(p, state.selectedPhase === p.id, "phase")).join("");
  $("#stagePhaseChoices").innerHTML = phases.map((p) => stagePhaseCard(p, state.selectedStagePhases.has(p.id))).join("");
  $("#architectureTypeChoices").innerHTML = architectures.map((p) => profileCard(p, state.selectedArchitecture === p.id, "architecture")).join("");
  $("#projectTypeChoices").innerHTML = projectTypes.map((p) => profileCard(p, state.selectedProjectTypes.has(p.id), "project-type")).join("");
  $("#initPackChoices").innerHTML = packs.map((p) => profileCard(p, state.selectedPacks.has(p.id), "init-pack")).join("");
  renderStageSummary();

  $("#packList").innerHTML = packs.map((pack) => {
    const counts = profileCounts(pack);
    const hasRuntime = counts.runtime > 0;
    const hasOptional = counts.optional > 0;
    const status = packStatus(pack.id);
    return `
      <div class="pack-row ${status ? "is-installed" : ""}" data-profile="${escapeAttr(pack.id)}">
        <div>
          <h3>${escapeHtml(profileName(pack) || pack.id)} ${status ? `<span class="badge ok">${escapeHtml(t("已经添加过了"))}</span>` : ""}</h3>
          <p class="muted">${escapeHtml(profileDescription(pack))}</p>
          <div class="pack-meta">
            <span class="badge">${escapeHtml(pack.id)}</span>
            <span class="badge">${counts.commands} commands</span>
            <span class="badge">${counts.skills} skills</span>
            <span class="badge">${counts.agents} agents</span>
            ${hasRuntime ? '<span class="badge warning">runtime</span>' : ""}
            ${hasOptional ? '<span class="badge warning">optional</span>' : ""}
          </div>
        </div>
        <div class="button-pair">
          ${status
            ? `<button disabled>${escapeHtml(t("已经添加过了"))}</button>`
            : `<button data-pack-preview="${escapeAttr(pack.id)}">${escapeHtml(t("预览添加"))}</button>
              <button class="primary" data-pack-add="${escapeAttr(pack.id)}">${escapeHtml(t("添加到当前项目"))}</button>`}
        </div>
      </div>
    `;
  }).join("");
}

function profileById(id) {
  const { architectures, projectTypes } = normalizedCatalogProfiles();
  return state.catalog.phases[id]
    || architectures.find((profile) => profile.id === id)
    || projectTypes.find((profile) => profile.id === id)
    || state.catalog.packs[id];
}

function renderDetail(profile) {
  if (!profile) {
    $("#detailSubtitle").textContent = t("点击 phase / architecture / project-type / pack 查看依赖");
    $("#detailContent").innerHTML = `<div class="empty">${escapeHtml(t("未选择内容。"))}</div>`;
    return;
  }
  $("#detailSubtitle").textContent = `${profile.id} · ${profileName(profile)}`;
  const required = profile.required || {};
  const optional = profile.optional || {};
  const includes = profileIncludeIds(profile);
  const section = (title, items) => `
    <div class="detail-section">
      <h3>${title}</h3>
      ${(items || []).length ? `<ul>${items.map((item) => `<li><code>${escapeHtml(item)}</code></li>`).join("")}</ul>` : `<div class="empty">${escapeHtml(t("无"))}</div>`}
    </div>
  `;
  $("#detailContent").innerHTML = [
    `<div class="panel"><strong>${escapeHtml(profileName(profile) || profile.id)}</strong><p class="muted">${escapeHtml(profileDescription(profile))}</p></div>`,
    section("Includes", includes),
    section("Required · Commands", required.commands),
    section("Required · Skills", required.skills),
    section("Required · Agents", required.agents),
    section("Required · Rules", required.rules),
    section("Required · Runtime", required.runtime),
    section("Optional · Hooks", optional.hooks),
    section("Optional · MCP", optional.mcp),
    section("Optional · External install", optional.external_install),
  ].join("");
}

function targetPath(item) {
  return item?.display_path || item?.generated_file || item?.target || item?.path || item?.source || item?.component || item?.name || "";
}

function shortTargetPath(value) {
  if (!value) return "";
  const normalized = String(value);
  const parts = normalized.split("/");
  if (parts.length <= 3) return normalized;
  const useful = parts.slice(-3).join("/");
  return useful.startsWith(".") ? useful : `.../${useful}`;
}

function ownersText(item) {
  return (item?.required_by || item?.owners || []).length ? uiSentence(`来源：${escapeList(item.required_by || item.owners)}`) : "";
}

function detailText(item) {
  const details = [];
  if (item?.detail) details.push(item.detail);
  if (item?.summary) details.push(item.summary);
  if (item?.source && item?.target) details.push(`源：${item.source} · 目标：${item.target}`);
  if (item?.targets?.length) {
    details.push(`目标：${item.targets.map((target) => `${target.path || target}${target.exists ? " 已存在" : target.exists === false ? " 缺失" : ""}`).join("；")}`);
  }
  if (item?.external_install?.length) details.push(`外部初始化：${escapeList(item.external_install)}`);
  if (item?.required_missing?.length) details.push(`缺少必需组件：${item.required_missing.map((dep) => dep.component || `${dep.kind}/${dep.name}`).join("；")}`);
  if (item?.runtime_pending?.length) details.push(`Runtime 待确认：${item.runtime_pending.map((dep) => dep.component || dep.name).join("；")}`);
  if (item?.optional_pending?.length) details.push(`Optional 未启用：${item.optional_pending.map((dep) => dep.component || `${dep.kind}/${dep.name}`).join("；")}`);
  return details.map(uiSentence).join(" · ");
}

function statusLabel(item) {
  const status = item?.status || "";
  const labels = {
    create_symlink: "本次新增：symlink",
    generate_file: "本次新增：生成文件",
    update_generated: "本次更新：托管文件",
    already_linked: "已经添加过了",
    already_generated: "已经添加过了",
    already_exists: "已经添加过了",
    write_lock: "本次写入：lock",
    generate: "本次生成",
    upsert_managed_block: "本次更新：托管段落",
    missing_source: "缺失源文件",
    existing_real: "冲突：已有真实文件",
    foreign_symlink: "冲突：非 ECC symlink",
    external_required: "待确认：外部初始化",
    runtime_missing: "缺失：runtime",
    optional_pending: "待确认：optional",
    command_blocked: "命令 blocked",
    command_needs_confirmation: "命令待确认",
    command_degraded: "命令降级",
    command_unknown: "命令 unknown",
    installed: "已经添加过了",
    installed_generated: "已经添加过了",
    skipped_existing: "曾跳过：目标冲突",
  };
  return uiSentence(labels[status] || status || "待处理");
}

function statusClass(item) {
  const status = item?.status || "";
  if (status.startsWith("already_")) return "ok";
  if (status === "installed" || status === "installed_generated") return "ok";
  if (status === "update_generated" || status === "upsert_managed_block") return "warning";
  if (status === "create_symlink" || status === "generate_file" || status === "generate" || status === "write_lock") return "info";
  if (status === "external_required" || status === "optional_pending" || status === "command_needs_confirmation" || status === "command_degraded") return "warning";
  if (status === "existing_real" || status === "foreign_symlink" || status === "missing_source" || status === "runtime_missing" || status === "command_blocked") return "error";
  if (status === "skipped_existing") return "warning";
  if (status === "command_unknown") return "info";
  return "";
}

function bucketSummary(items) {
  const counts = { add: 0, update: 0, existing: 0, pending: 0, problem: 0 };
  for (const item of items || []) {
    const status = item?.status || "";
    if (status.startsWith("already_")) counts.existing += 1;
    else if (["installed", "installed_generated"].includes(status)) counts.existing += 1;
    else if (["update_generated", "upsert_managed_block"].includes(status)) counts.update += 1;
    else if (["external_required", "optional_pending", "command_needs_confirmation", "command_degraded", "skipped_existing"].includes(status)) counts.pending += 1;
    else if (["existing_real", "foreign_symlink", "missing_source", "runtime_missing", "command_blocked", "command_unknown"].includes(status)) counts.problem += 1;
    else counts.add += 1;
  }
  const parts = [];
  if (counts.add) parts.push(uiSentence(`新增 ${counts.add}`));
  if (counts.update) parts.push(uiSentence(`更新 ${counts.update}`));
  if (counts.existing) parts.push(uiSentence(`已经添加 ${counts.existing}`));
  if (counts.pending) parts.push(uiSentence(`待确认 ${counts.pending}`));
  if (counts.problem) parts.push(uiSentence(`问题 ${counts.problem}`));
  return parts.join(" · ") || t("无");
}

function detailTargetRow(item, label = "") {
  const fullPath = targetPath(item) || item.name || item.component || "item";
  const meta = [uiSentence(label), detailText(item), ownersText(item)].filter(Boolean).join(" · ");
  return `
    <div class="detail-target" title="${escapeAttr(fullPath)}">
      <div class="detail-target-head">
        <code>${escapeHtml(shortTargetPath(fullPath))}</code>
        <span class="badge ${statusClass(item)} detail-target-status">${escapeHtml(statusLabel(item))}</span>
      </div>
      ${fullPath !== shortTargetPath(fullPath) ? `<span class="muted">${escapeHtml(fullPath)}</span>` : ""}
      ${meta ? `<span class="muted">${escapeHtml(meta)}</span>` : ""}
    </div>
  `;
}

function detailBucket(title, items, label = "") {
  const safeItems = items || [];
  const quietStatuses = ["already_linked", "already_generated", "already_exists", "installed", "installed_generated"];
  const hasWork = safeItems.some((item) => !quietStatuses.includes(item?.status || ""));
  return `
    <details class="detail-bucket" ${hasWork ? "open" : ""}>
      <summary>
        <span>${escapeHtml(uiText(title))}</span>
        <span class="detail-summary-meta">
          <span class="badge">${escapeHtml(uiSentence(`${safeItems.length} 项`))}</span>
          <span class="muted">${escapeHtml(bucketSummary(safeItems))}</span>
        </span>
      </summary>
      ${safeItems.length ? safeItems.map((item) => detailTargetRow(item, label)).join("") : `<div class="empty">${escapeHtml(t("无"))}</div>`}
    </details>
  `;
}

function withStatus(items, status, extra = {}) {
  return (items || []).map((item) => ({ ...item, ...extra, status: item.status || status }));
}

function forceStatus(items, status, extra = {}) {
  return (items || []).map((item) => ({ ...item, ...extra, status }));
}

function missingItems(items, extra = {}) {
  return (items || []).map((item) => ({ ...item, ...extra, status: extra.status || item.status || "missing_source", display_path: item.source || item.target || item.component || item.name }));
}

function optionalDetailItems(optional) {
  return Object.entries(optional || {}).flatMap(([kind, items]) =>
    Object.keys(items || {}).map((name) => ({
      kind,
      name,
      component: `${kind}/${name}`,
      owners: items[name],
      status: "optional_pending",
      detail: "optional 依赖默认不自动写入；可通过满配预览纳入确认流程。",
    }))
  );
}

function commandHealthDetailItems(health) {
  const statusMap = {
    blocked: "command_blocked",
    needs_confirmation: "command_needs_confirmation",
    degraded: "command_degraded",
    unknown: "command_unknown",
  };
  return (health?.commands || [])
    .filter((command) => command.status && command.status !== "ready")
    .map((command) => ({
      ...command,
      display_path: command.name,
      status: statusMap[command.status] || `command_${command.status}`,
    }));
}

function componentBucket(items, prefix) {
  return (items || []).filter((item) => (item.component || "").startsWith(prefix));
}

function lockComponentItems(components, status = "installed") {
  return Object.entries(components || {}).map(([component, item]) => ({
    ...item,
    component,
    display_path: item.generated_file || item.target || component,
    name: item.name || component.split("/").pop(),
    required_by: item.required_by || [],
    status,
  }));
}

function installedOptionalItems(optional) {
  return Object.entries(optional || {}).flatMap(([kind, items]) => {
    if (Array.isArray(items)) {
      return items.map((name) => ({ kind, name, component: `${kind}/${name}`, status: "optional_pending" }));
    }
    return Object.keys(items || {}).map((name) => ({
      kind,
      name,
      component: `${kind}/${name}`,
      owners: items[name],
      status: "optional_pending",
      detail: "安装记录中的 optional 待确认项；不会在刷新后自动写入。",
    }));
  });
}

function installedRuntimeItems(items) {
  return forceStatus(items || [], "external_required").map((item) => ({
    ...item,
    component: item.component || `runtime/${item.name || "runtime"}`,
    display_path: item.name || item.component || "runtime",
  }));
}

function installedSkippedItems(items) {
  return forceStatus(items || [], "skipped_existing").map((item) => ({
    ...item,
    display_path: item.target || item.component,
    detail: item.reason ? `原因：${item.reason}` : "安装时检测到目标冲突，已跳过。",
  }));
}

function generatedInstalledItems(scan, lock) {
  const items = [];
  if (lock?.enable_claude !== false && scan?.has_generated) {
    items.push({ path: scan.generated_claude_file || "CLAUDE.ecc.generated.md", status: "installed_generated", detail: "Claude Code 托管说明文件" });
  }
  if (lock?.enable_codex !== false && scan?.has_generated_codex) {
    items.push({ path: lock.generated_codex_file || scan.generated_codex_file || "AGENTS.ecc.generated.md", status: "installed_generated", detail: "Codex 托管说明文件" });
  }
  if (lock?.enable_antigravity !== false && scan?.has_generated_antigravity) {
    items.push({ path: lock.generated_antigravity_file || scan.generated_antigravity_file || "ANTIGRAVITY.ecc.generated.md", status: "installed_generated", detail: "Antigravity 托管说明文件" });
  }
  if (scan?.has_lock) {
    items.push({ path: ".ecc-manager/ecc-lock/profile.json", status: "installed_generated", detail: "ECC Manager 安装记录" });
  }
  if (scan?.has_agents_md_managed_block || scan?.has_agents_md_antigravity_block) {
    items.push({ path: "AGENTS.md", status: "installed_generated", detail: "Codex / Antigravity 托管入口" });
  }
  return items;
}

function detailItemKey(item) {
  return item?.component || item?.generated_file || item?.target || item?.path || item?.display_path || item?.source || item?.name || JSON.stringify(item);
}

function mergeDetailItems(...groups) {
  const merged = new Map();
  for (const items of groups) {
    for (const item of items || []) {
      merged.set(detailItemKey(item), item);
    }
  }
  return Array.from(merged.values());
}

function installedDetailGroups(scan) {
  const lock = scan?.lock || {};
  const claudeItems = lockComponentItems(lock.components || {});
  const skippedItems = installedSkippedItems(lock.skipped_existing || []);
  const claudeAll = [...claudeItems, ...skippedItems];
  return {
    hasLock: Boolean(scan?.has_lock || Object.keys(lock).length),
    claudeItems: claudeAll,
    runtimeItems: [
      ...claudeAll.filter((item) => item.kind === "runtime" || item.component?.startsWith("runtime/")),
      ...installedRuntimeItems(lock.runtime_external_required || []),
    ],
    codexItems: lockComponentItems(lock.codex_components || {}),
    antigravityItems: lockComponentItems(lock.antigravity_components || {}),
    optionalItems: installedOptionalItems(lock.optional_pending || {}),
    commandItems: commandHealthDetailItems(lock.command_health || {}),
    projectFiles: generatedInstalledItems(scan, lock),
  };
}

function renderDetailTree({ title, description, claudeItems, runtimeItems, codexItems, antigravityItems, optionalItems, commandItems, projectFiles }) {
  const byKind = (kind) => (claudeItems || []).filter((item) => item.kind === kind || item.component?.startsWith(`${kind}s/`) || item.component?.startsWith(`${kind}/`));
  $("#detailContent").innerHTML = `
    <div class="panel">
      <strong>${escapeHtml(uiText(title))}</strong>
      <p class="muted">${escapeHtml(uiSentence(description))}</p>
    </div>
    <div class="detail-tree">
      ${detailParent("Claude Code", [
        { title: "Commands", items: byKind("command") },
        { title: "Skills", items: byKind("skill") },
        { title: "Agents", items: byKind("agent") },
        { title: "Rules", items: byKind("rule") },
        { title: "Runtime", items: runtimeItems || [] },
        { title: "Command health", items: commandItems || [] },
      ])}
      ${detailParent("Codex", [
        { title: "Command skills", items: componentBucket(codexItems, "codex/commands/"), label: "ECC commands 适配为 Codex skills" },
        { title: "Skills", items: componentBucket(codexItems, "codex/skills/") },
        { title: "Agents", items: componentBucket(codexItems, "codex/agents/") },
        { title: "Rules", items: componentBucket(codexItems, "codex/rules/") },
      ], true)}
      ${detailParent("Antigravity", [
        { title: "Agents", items: componentBucket(antigravityItems, "antigravity/agents/"), label: ".agents/agents.md 聚合 personas" },
        { title: "Workflows", items: componentBucket(antigravityItems, "antigravity/workflows/"), label: "ECC commands 转 workflows" },
        { title: "Skills", items: componentBucket(antigravityItems, "antigravity/skills/") },
        { title: "Rules", items: componentBucket(antigravityItems, "antigravity/rules/") },
      ], true)}
      ${detailParent("Project files", [
        { title: "Generated / lock", items: projectFiles || [] },
      ], false)}
      ${detailParent("Optional", [
        { title: "待确认 optional", items: optionalItems || [] },
      ], (optionalItems || []).length > 0)}
    </div>
  `;
}

function detailParent(title, buckets, open = true) {
  const count = buckets.reduce((sum, bucket) => sum + (bucket.items || []).length, 0);
  const allItems = buckets.flatMap((bucket) => bucket.items || []);
  return `
    <details ${open ? "open" : ""}>
      <summary>
        <span>${escapeHtml(uiText(title))}</span>
        <span class="detail-summary-meta">
          <span class="badge">${escapeHtml(uiSentence(`${count} 项`))}</span>
          <span class="muted">${escapeHtml(bucketSummary(allItems))}</span>
        </span>
      </summary>
      ${buckets.map((bucket) => detailBucket(bucket.title, bucket.items, bucket.label)).join("")}
    </details>
  `;
}

function renderPlanDetail(plan) {
  if (!plan) return;
  $("#detailSubtitle").textContent = `${uiSentence(plan.action || "plan")} · ${plan.profiles?.join("、") || t("未选择") + " profile"}`;
  const installed = installedDetailGroups(state.scan);
  const create = withStatus(plan.create || [], "create_symlink");
  const existing = plan.existing_ok || [];
  const skipped = plan.skipped || [];
  const missing = missingItems(plan.missing || []);
  const claudeItems = mergeDetailItems(installed.claudeItems, create, existing, skipped, missing);
  const runtime = plan.runtime || {};
  const runtimeItems = [
    ...installed.runtimeItems,
    ...withStatus(runtime.create || [], "create_symlink"),
    ...(runtime.existing_ok || []),
    ...withStatus(runtime.skipped || [], "existing_real"),
    ...missingItems(runtime.missing || [], { status: "runtime_missing" }),
    ...forceStatus(runtime.external_required || [], "external_required"),
  ];
  const codexItems = mergeDetailItems(installed.codexItems, [
    ...(plan.codex?.write || []),
    ...(plan.codex?.existing_ok || []),
    ...(plan.codex?.skipped || []),
    ...missingItems(plan.codex?.missing || []),
  ]);
  const antigravityItems = mergeDetailItems(installed.antigravityItems, [
    ...(plan.antigravity?.write || []),
    ...(plan.antigravity?.existing_ok || []),
    ...(plan.antigravity?.skipped || []),
    ...missingItems(plan.antigravity?.missing || []),
  ]);
  const optionalItems = mergeDetailItems(installed.optionalItems, optionalDetailItems(plan.optional || {}));
  const commandItems = mergeDetailItems(installed.commandItems, commandHealthDetailItems(plan.command_health || {}));
  const projectFiles = mergeDetailItems(installed.projectFiles, plan.generated || []);
  renderDetailTree({
    title: "目标汇总",
    description: "这里汇总当前项目总目标，并标出本次预览新增、更新、待确认项和问题；按工具和类型分组，父级和子集都可以折叠。",
    claudeItems,
    runtimeItems: mergeDetailItems(runtimeItems),
    codexItems,
    antigravityItems,
    optionalItems,
    commandItems,
    projectFiles,
  });
}

function renderInstalledDetail(scan) {
  const installed = installedDetailGroups(scan);
  if (!installed.hasLock) {
    renderDetail(null);
    return;
  }
  $("#detailSubtitle").textContent = uiSentence("来自 .ecc-manager/ecc-lock/profile.json");
  renderDetailTree({
    title: "已安装目标汇总",
    description: "这里来自项目 lock 的已安装记录，是刷新 / 重启后恢复的只读汇总，不代表本次将写入的计划。",
    ...installed,
  });
}

function selectedInitProfiles() {
  return [
    state.selectedPhase,
    state.selectedArchitecture,
    ...Array.from(state.selectedProjectTypes),
    ...Array.from(state.selectedPacks),
  ].filter(Boolean);
}

async function makePlan(action, profiles, options = {}) {
  const project = $("#projectPath").value;
  const plan = await api("/api/plan", { action, profiles, project, include_optional: options.includeOptional === true });
  state.currentPlan = plan;
  renderPreview(plan);
  setPage("preview");
  return plan;
}

function renderPreview(plan) {
  $("#executePlanBtn").disabled = !plan || !plan.can_apply;
  if (!plan) {
    $("#previewContent").innerHTML = `<div class="empty">${escapeHtml(t("还没有预览内容。"))}</div>`;
    return;
  }
  const rows = (items, render) => items.length
    ? `<ul class="preview-list">${items.map(render).join("")}</ul>`
    : `<div class="empty">${escapeHtml(t("无"))}</div>`;
  const create = rows(plan.create || [], (item) => `<li><code>${escapeHtml(item.target)}</code><div class="muted">${escapeHtml(t("来源："))}${escapeList(item.required_by)}</div></li>`);
  const skipped = rows(plan.skipped || [], (item) => `<li><code>${escapeHtml(item.target)}</code><div class="muted">${escapeHtml(uiStatusLabel(item.status))} · ${escapeList(item.required_by)}</div></li>`);
  const missing = rows(plan.missing || [], (item) => `<li><code>${escapeHtml(item.source)}</code><div class="muted">${escapeHtml(t("目标："))}${escapeHtml(item.target)}</div></li>`);
  const generated = rows(plan.generated || [], (item) => `<li><code>${escapeHtml(item.path)}</code><div class="muted">${escapeHtml(uiStatusLabel(item.status))}</div></li>`);
  const untouched = rows((plan.untouched || []).map((path) => ({ path })), (item) => `<li><code>${escapeHtml(item.path)}</code></li>`);
  const optional = Object.entries(plan.optional || {}).flatMap(([kind, items]) =>
    Object.keys(items || {}).map((name) => ({ kind, name, owners: items[name] }))
  );
  const optionalRows = rows(optional, (item) => `<li><code>${escapeHtml(item.kind)}: ${escapeHtml(item.name)}</code><div class="muted">${escapeHtml(t("来自"))}: ${escapeList(item.owners)}</div></li>`);
  const runtime = plan.runtime || {};
  const runtimeCreate = rows(runtime.create || [], (item) => `<li><code>${escapeHtml(item.target)}</code><div class="muted">runtime: ${escapeHtml(item.name)} · 来源：${escapeList(item.required_by)}</div></li>`);
  const runtimeExternal = rows(runtime.external_required || [], (item) => {
    const targets = (item.targets || []).map((target) => `${escapeHtml(target.path)} ${target.exists ? escapeHtml(t("已存在")) : escapeHtml(t("缺失"))}`).join("；");
    return `<li><code>${escapeHtml(item.name)}</code><div class="muted">${escapeHtml(localizedDescription(item))}</div><div class="muted">${escapeHtml(t("目标："))}${targets || t("未声明")}</div><div class="muted">${escapeHtml(t("外部初始化："))}${escapeList(item.external_install)}</div></li>`;
  });
  const runtimeMissing = rows(runtime.missing || [], (item) => `<li><code>${escapeHtml(item.name)}</code><div class="muted">${escapeHtml(t("本地 runtime 文件缺失，需要单独确认外部初始化。"))}</div></li>`);
  const codex = plan.codex || {};
  const codexWrite = rows(codex.write || [], (item) => `<li><code>${escapeHtml(item.generated_file || item.target)}</code><div class="muted">${escapeHtml(uiStatusLabel(item.status))} · ${escapeList(item.required_by)}</div></li>`);
  const codexSkipped = rows(codex.skipped || [], (item) => `<li><code>${escapeHtml(item.generated_file || item.target)}</code><div class="muted">${escapeHtml(uiStatusLabel(item.status))} · ${escapeList(item.required_by)}</div></li>`);
  const codexMissing = rows(codex.missing || [], (item) => `<li><code>${escapeHtml(item.source)}</code><div class="muted">Codex ${escapeHtml(t("目标："))}${escapeHtml(item.target)}</div></li>`);
  const antigravity = plan.antigravity || {};
  const antigravityWrite = rows(antigravity.write || [], (item) => `<li><code>${escapeHtml(item.generated_file || item.target)}</code><div class="muted">${escapeHtml(uiStatusLabel(item.status))} · ${escapeList(item.required_by)}</div></li>`);
  const antigravitySkipped = rows(antigravity.skipped || [], (item) => `<li><code>${escapeHtml(item.generated_file || item.target)}</code><div class="muted">${escapeHtml(uiStatusLabel(item.status))} · ${escapeList(item.required_by)}</div></li>`);
  const antigravityMissing = rows(antigravity.missing || [], (item) => `<li><code>${escapeHtml(item.source)}</code><div class="muted">Antigravity ${escapeHtml(t("目标："))}${escapeHtml(item.target)}</div></li>`);
  const commandHealth = renderCommandHealth(plan.command_health);
  renderPlanDetail(plan);

  $("#previewContent").innerHTML = `
    ${renderIssuesPanel("预览问题与选项", plan.issues || [], "本次预览没有 warning/error。")}
    ${plan.include_optional ? `<div class="preview-group"><h3>${escapeHtml(t("满配模式"))}</h3><div class="empty">${escapeHtml(t("可安装的 optional 依赖已纳入本次预览；hooks / MCP / external install 仍需单独确认。"))}</div></div>` : ""}
    <div class="preview-group"><h3>${escapeHtml(t("将创建 symlink"))}</h3>${create}</div>
    <div class="preview-group"><h3>${escapeHtml(t("将创建 runtime symlink"))}</h3>${runtimeCreate}</div>
    <div class="preview-group"><h3>${escapeHtml(t("已存在，将跳过"))}</h3>${skipped}</div>
    <div class="preview-group"><h3>${escapeHtml(t("缺失源文件"))}</h3>${missing}</div>
    <div class="preview-group"><h3>${escapeHtml(t("Runtime 需要确认"))}</h3>${runtimeExternal}</div>
    <div class="preview-group"><h3>${escapeHtml(t("Runtime 本地文件缺失"))}</h3>${runtimeMissing}</div>
    <div class="preview-group"><h3>${escapeHtml(t("Codex 将写入"))}</h3>${codexWrite}</div>
    <div class="preview-group"><h3>${escapeHtml(t("Codex 目标冲突"))}</h3>${codexSkipped}</div>
    <div class="preview-group"><h3>${escapeHtml(t("Codex 缺失源文件"))}</h3>${codexMissing}</div>
    <div class="preview-group"><h3>${escapeHtml(t("Antigravity 将写入"))}</h3>${antigravityWrite}</div>
    <div class="preview-group"><h3>${escapeHtml(t("Antigravity 目标冲突"))}</h3>${antigravitySkipped}</div>
    <div class="preview-group"><h3>${escapeHtml(t("Antigravity 缺失源文件"))}</h3>${antigravityMissing}</div>
    ${commandHealth}
    <div class="preview-group"><h3>${escapeHtml(t("将生成文件"))}</h3>${generated}</div>
    <div class="preview-group"><h3>${escapeHtml(t("不会修改"))}</h3>${untouched}</div>
    <div class="preview-group"><h3>${escapeHtml(t("Optional，需要确认"))}</h3>${optionalRows}</div>
  `;
}

function planInstallSections(plan) {
  const sections = [];
  const addSection = (title, items) => {
    if (items.length) sections.push({ title, items });
  };
  const formatOwners = (owners) => owners?.length ? `${t("来源：")}${owners.join("、")}` : "";
  const create = plan.create || [];
  const byKind = (kind) => create.filter((item) => item.kind === kind);
  const codexWrite = plan.codex?.write || [];
  const antigravityWrite = plan.antigravity?.write || [];
  const component = (item) => item.component || "";
  const nameOf = (item) => item.name || (item.target || item.path || "").split("/").pop() || "item";
  const labelOf = (label, item) => typeof label === "function" ? label(item) : label;
  const lines = (items, label, pathFor = (item) => item.generated_file || item.target || item.path) =>
    items.map((item) => `${labelOf(label, item)}: ${pathFor(item)}`);
  const groupedItems = (items, label, pathFor) => {
    const grouped = new Map();
    for (const item of items) {
      const name = nameOf(item);
      if (!grouped.has(name)) grouped.set(name, { path: name, detail: formatOwners(item.required_by), targets: [] });
      grouped.get(name).targets.push(...lines([item], label, pathFor));
    }
    return Array.from(grouped.values());
  };
  const commands = groupedItems(byKind("command"), "Claude");
  for (const item of codexWrite.filter((entry) => component(entry).startsWith("codex/commands/"))) {
    const name = nameOf(item);
    const existing = commands.find((entry) => entry.path === name) || { path: name, detail: formatOwners(item.required_by), targets: [] };
    if (!commands.includes(existing)) commands.push(existing);
    existing.targets.push(`Codex skill adapter: ${item.generated_file || item.target}`);
  }
  for (const item of antigravityWrite.filter((entry) => component(entry).startsWith("antigravity/workflows/"))) {
    const name = nameOf(item);
    const existing = commands.find((entry) => entry.path === name) || { path: name, detail: formatOwners(item.required_by), targets: [] };
    if (!commands.includes(existing)) commands.push(existing);
    existing.targets.push(`Antigravity workflow: ${item.generated_file || item.target}`);
  }
  addSection("Commands", commands);
  const skills = groupedItems(byKind("skill"), "Claude");
  const sharedSkillWrites = [
    ...codexWrite.filter((entry) => component(entry).startsWith("codex/skills/")),
    ...antigravityWrite.filter((entry) => component(entry).startsWith("antigravity/skills/")),
  ];
  for (const item of sharedSkillWrites) {
    const name = nameOf(item);
    const existing = skills.find((entry) => entry.path === name) || { path: name, detail: formatOwners(item.required_by), targets: [] };
    if (!skills.includes(existing)) skills.push(existing);
    existing.targets.push(`Workspace skill: ${item.generated_file || item.target}`);
  }
  addSection("Skills", skills);
  addSection("Agents", groupedItems([
    ...byKind("agent"),
    ...codexWrite.filter((item) => component(item).startsWith("codex/agents/")),
    ...antigravityWrite.filter((item) => component(item).startsWith("antigravity/agents/")),
  ], (item) => {
    if (component(item).startsWith("codex/agents/")) return "Codex";
    if (component(item).startsWith("antigravity/agents/")) return "Antigravity";
    return "Claude";
  }));
  addSection("Rules", groupedItems([
    ...byKind("rule"),
    ...codexWrite.filter((item) => component(item).startsWith("codex/rules/")),
    ...antigravityWrite.filter((item) => component(item).startsWith("antigravity/rules/")),
  ], (item) => {
    if (component(item).startsWith("codex/rules/")) return "Codex";
    if (component(item).startsWith("antigravity/rules/")) return "Antigravity";
    return "Claude";
  }));
  addSection("Runtime", (plan.runtime?.create || []).map((item) => ({ path: item.name || "runtime", detail: formatOwners(item.required_by), targets: [`Runtime symlink: ${item.target}`] })));
  addSection("Generated Project Files", (plan.generated || []).map((item) => ({ path: item.path, detail: item.status || "generate", targets: [] })));
  const installedKeys = new Set([
    ...byKind("command").map((item) => `commands:${item.name}`),
    ...byKind("skill").map((item) => `skills:${item.name}`),
    ...byKind("agent").map((item) => `agents:${item.name}`),
    ...byKind("rule").map((item) => `rules:${item.name}`),
    ...(plan.runtime?.create || []).map((item) => `runtime:${item.name}`),
  ]);
  const optional = Object.entries(plan.optional || {}).flatMap(([kind, items]) =>
    Object.keys(items || {})
      .filter((name) => !installedKeys.has(`${kind}:${name}`))
      .map((name) => ({ path: `${kind}: ${name}`, detail: `${t("可选项，本次不会安装")} · ${formatOwners(items[name])}`, targets: [] }))
  );
  const runtimeExternal = (plan.runtime?.external_required || []).flatMap((item) => [
    { path: `runtime: ${item.name}`, detail: t("需要手动处理，本次不会安装"), targets: [] },
    ...(item.external_install || []).map((name) => ({ path: `external install: ${name}`, detail: t("需要手动执行，本次不会执行"), targets: [] })),
  ]);
  addSection("未安装的可选项", [...optional, ...runtimeExternal]);
  return sections;
}

function renderInstallSections(sections) {
  if (!sections.length) {
    return `<div class="empty">${escapeHtml(t("本次没有新增或更新内容。"))}</div>`;
  }
  return sections.map((section) => `
    <section class="install-summary">
      <h3>${escapeHtml(uiText(section.title))} <span class="badge">${section.items.length}</span></h3>
      <ul class="preview-list">
        ${section.items.map((item) => `
          <li>
            <code>${escapeHtml(item.path)}</code>
            ${item.detail ? `<div class="muted">${escapeHtml(item.detail)}</div>` : ""}
            ${(item.targets || []).map((target) => `<div class="muted">${escapeHtml(target)}</div>`).join("")}
          </li>
        `).join("")}
      </ul>
    </section>
  `).join("");
}

function confirmInstallPlan(plan) {
  const modal = $("#installConfirmModal");
  const content = $("#installConfirmContent");
  const apply = $("#installConfirmApply");
  const cancel = $("#installConfirmCancel");
  const close = $("#installConfirmClose");
  if (!modal || !content || !apply || !cancel || !close) {
    return Promise.resolve(window.confirm(t("确认执行本次安装？")));
  }
  const sections = planInstallSections(plan);
  const total = sections.reduce((sum, section) => sum + section.items.length, 0);
  $("#installConfirmSubtitle").textContent = currentLang() === "en"
    ? `This will write, create, or update ${total} items. Cancelling will not modify files.`
    : `本次将写入 / 创建 / 更新 ${total} 项；取消不会修改任何文件。`;
  content.innerHTML = renderInstallSections(sections);
  modal.hidden = false;
  apply.focus();
  return new Promise((resolve) => {
    const cleanup = (value) => {
      modal.hidden = true;
      apply.removeEventListener("click", onApply);
      cancel.removeEventListener("click", onCancel);
      close.removeEventListener("click", onCancel);
      modal.removeEventListener("click", onBackdrop);
      document.removeEventListener("keydown", onKeydown);
      resolve(value);
    };
    const onApply = () => cleanup(true);
    const onCancel = () => cleanup(false);
    const onBackdrop = (event) => {
      if (event.target === modal) cleanup(false);
    };
    const onKeydown = (event) => {
      if (event.key === "Escape") cleanup(false);
    };
    apply.addEventListener("click", onApply);
    cancel.addEventListener("click", onCancel);
    close.addEventListener("click", onCancel);
    modal.addEventListener("click", onBackdrop);
    document.addEventListener("keydown", onKeydown);
  });
}

function commandHealthBadgeClass(status) {
  if (status === "ready") return "ok";
  if (status === "blocked") return "error";
  if (status === "needs_confirmation" || status === "degraded") return "warning";
  if (status === "unknown") return "info";
  return "";
}

function renderCommandHealth(health) {
  const commands = health?.commands || [];
  if (!commands.length) return `<div class="preview-group"><h3>${escapeHtml(t("命令可运行性"))}</h3><div class="empty">${escapeHtml(t("无"))}</div></div>`;
  const dependencyLine = (title, items) => items.length
    ? `<div class="muted">${escapeHtml(t(title))}：${items.map((item) => `<code>${escapeHtml(item.component || `${item.kind}/${item.name}`)}</code> <span>${escapeHtml(uiStatusLabel(item.status))}</span>`).join("；")}</div>`
    : "";
  return `
    <div class="preview-group command-health">
      <h3>${escapeHtml(t("命令可运行性"))}</h3>
      <div class="command-relation-list">
        ${commands.map((command) => `
          <details class="command-relation">
            <summary>
              <span>
                <strong>${escapeHtml(command.name)}</strong>
                <small>${escapeHtml(uiSentence(command.summary || ""))}</small>
              </span>
              <span class="pack-meta">
                <span class="badge ${commandHealthBadgeClass(command.status)}">${escapeHtml(uiStatusLabel(command.label || command.status))}</span>
                <span class="badge">${escapeHtml(command.contract_source || "contract")}</span>
                <span class="badge">${escapeList(command.required_by, ", ", t("无来源"))}</span>
              </span>
            </summary>
            ${dependencyLine("缺少必需组件", command.required_missing || [])}
            ${dependencyLine("Runtime 待确认", command.runtime_pending || [])}
            ${dependencyLine("Optional 未启用", command.optional_pending || [])}
          </details>
        `).join("")}
      </div>
    </div>
  `;
}

function taskStatusBadgeClass(status) {
  if (status === "completed") return "ok";
  if (status === "completed_with_warnings") return "warning";
  if (status === "failed") return "error";
  return "info";
}

function criterionBadgeClass(status) {
  if (status === "pass") return "ok";
  if (status === "warning" || status === "pending") return "warning";
  if (status === "fail") return "error";
  return "info";
}

function renderTaskResult(taskRun) {
  const target = $("#taskResultContent");
  if (!target) return;
  if (!taskRun) {
    target.innerHTML = `<div class="empty">${escapeHtml(t("还没有任务结果。执行初始化、追加阶段或添加能力包后，这里会显示完成证明。"))}</div>`;
    return;
  }
  const criteria = taskRun.verification?.criteria || [];
  const summary = taskRun.verification?.summary || {};
  const taskIssues = taskRun.issues || [];
  const nextActions = taskRun.next_actions || [];
  const nextCommands = taskRun.next_commands || [];
  const criterionActions = (criterion) => {
    if (criterion.status === "pass") return "";
    const issueMatches = {
      sources_available: ["plan-missing-sources"],
      required_symlinks: ["plan-target-conflicts"],
      command_health: ["plan-command", "optional-not-enabled", "runtime-confirmation"],
      codex_bridge: ["codex-"],
      antigravity_bridge: ["antigravity-"],
      doctor_checks: ["doctor-"],
    }[criterion.id] || [];
    const issue = taskIssues.find((item) => issueMatches.some((prefix) => String(item.id || "").startsWith(prefix)));
    if (issue) return renderIssueActions(issue);
    const action = nextActions.find((item) => String(item.kind || "").includes(criterion.id) || String(item.message || "").includes(criterion.label));
    return action ? renderIssueActions(action) : `<span class="issue-guide">${escapeHtml(t("查看下方“下一步”处理。"))}</span>`;
  };
  target.innerHTML = `
    <section class="asset-classification task-result">
      <div class="asset-classification-head">
        <div>
          <h2>${escapeHtml(uiSentence(taskRun.goal || "任务结果"))}</h2>
          <p class="muted">${escapeHtml(taskRun.created_at || "")}</p>
        </div>
        <div class="pack-meta">
          <span class="badge ${taskStatusBadgeClass(taskRun.status)}">${escapeHtml(uiStatusLabel(taskRun.label || taskRun.status))}</span>
          <span class="badge ok">${escapeHtml(summary.pass || 0)} pass</span>
          <span class="badge warning">${escapeHtml(summary.warning || 0)} warning</span>
          <span class="badge error">${escapeHtml(summary.fail || 0)} fail</span>
        </div>
      </div>
      <div class="asset-breakdown task-breakdown">
        <article><strong>${escapeHtml(taskRun.apply?.applied ?? 0)}</strong><span>${escapeHtml(t("新建 symlink"))}</span><b>${escapeHtml(t("required 组件"))}</b></article>
        <article><strong>${escapeHtml(taskRun.apply?.runtime_applied ?? 0)}</strong><span>runtime symlink</span><b>${escapeHtml(t("全局运行时"))}</b></article>
        <article><strong>${escapeHtml(taskRun.apply?.codex_applied ?? 0)}</strong><span>${escapeHtml(t("Codex 写入"))}</span><b>commands / skills / agents / rules</b></article>
        <article><strong>${escapeHtml(taskRun.apply?.antigravity_applied ?? 0)}</strong><span>${escapeHtml(t("Antigravity 写入"))}</span><b>agents / workflows / rules / skills</b></article>
        <article><strong>${escapeHtml(taskRun.verification?.doctor?.warnings ?? 0)}</strong><span>Doctor warning</span><b>${escapeHtml(t("需要跟进"))}</b></article>
        <article><strong>${escapeHtml(nextCommands.length)}</strong><span>${escapeHtml(t("下一步命令"))}</span><b>${escapeHtml(nextCommands.join(", ") || t("无"))}</b></article>
      </div>
    </section>
    ${renderIssuesPanel("任务问题与选项", taskIssues, "本次任务没有 warning/error。")}
    <section class="asset-relations">
      <div class="asset-classification-head">
        <div>
          <h2>${escapeHtml(t("完成标准"))}</h2>
          <p class="muted">${escapeHtml(t("这些检查决定本次任务是否真的完成。"))}</p>
        </div>
      </div>
      <div class="command-relation-list">
        ${criteria.map((item) => `
          <div class="relation-edge task-criterion">
            <span class="badge ${criterionBadgeClass(item.status)}">${escapeHtml(uiStatusLabel(item.status))}</span>
            <strong>${escapeHtml(uiSentence(item.label))}</strong>
            <span class="muted">${escapeHtml(uiSentence(item.message))}</span>
            <span class="issue-actions">${criterionActions(item)}</span>
          </div>
        `).join("")}
      </div>
    </section>
    <section class="asset-classification">
      <div class="asset-classification-head">
        <div>
          <h2>${escapeHtml(t("下一步"))}</h2>
          <p class="muted">${escapeHtml(t("这里是系统根据验证结果给出的后续动作。"))}</p>
        </div>
      </div>
      <div class="asset-list">
        ${nextActions.map((item) => `
          <div class="asset-row task-action">
            <span class="badge">${escapeHtml(item.kind)}</span>
            <span class="muted">${escapeHtml(uiSentence(item.message))}</span>
            <span class="issue-actions">${renderIssueActions(item)}</span>
          </div>
        `).join("")}
      </div>
    </section>
  `;
}

function setScanBusy(isBusy) {
  [$("#scanProjectBtn")].filter(Boolean).forEach((button) => {
    button.disabled = isBusy;
    button.textContent = isBusy ? t("扫描中...") : t("扫描项目");
  });
}

async function scanProject(options = {}) {
  const notify = options.notify === true;
  if (!($("#projectPath").value || "").trim() && ($("#projectPickerPath")?.value || "").trim()) {
    $("#projectPath").value = $("#projectPickerPath").value.trim();
  }
  if (!hasProjectPath()) {
    const scan = await chooseProjectDirectory({ notifySuccess: notify });
    if (!scan && notify) toast("请先选择项目目录");
    return scan;
  }
  setScanBusy(true);
  try {
    const scan = await api("/api/project/scan", { project: currentProjectPath() });
    state.scan = scan;
    state.lastTaskRun = scan.lock?.last_task_run || state.lastTaskRun;
    $("#projectPath").value = scan.project;
    saveProjectPath(scan.project);
    renderProjectCards(scan);
    renderCatalog();
    updateTopbar();
    if (activePageId() !== "preview" || !state.currentPlan) {
      renderInstalledDetail(scan);
    }
    if (notify) {
      toast(scan.exists ? "扫描完成：项目目录存在" : "扫描完成：项目目录不存在");
    }
    return scan;
  } catch (error) {
    if (notify) toast(`扫描失败：${error.message}`);
    throw error;
  } finally {
    setScanBusy(false);
  }
}

async function openProjectPath(label, relativePath, existsInScan) {
  try {
    const scan = await scanProject();
    if (!scan) return;
    if (!scan.exists) {
      toast("项目目录不存在，无法打开");
      return;
    }
    if (!existsInScan(scan)) {
      toast(`${label} 不存在，请先创建或初始化`);
      return;
    }

    await api("/api/open-path", { path: `${scan.project}/${relativePath}` });
    toast(`已向系统发送打开请求：${label}`);
  } catch (error) {
    toast(`无法打开 ${label}：${error.message}`);
  }
}

async function chooseProjectDirectory(options = {}) {
  const notifySuccess = options.notifySuccess !== false;
  const current = options.current || $("#projectPath").value || savedProjectPath() || state.cwd;
  let result;
  try {
    result = await api("/api/choose-project", {
      current,
      prompt: t("选择要由 ECC Manager 管理的项目目录"),
    });
  } catch (error) {
    const visibleProjectInput = $("#projectPickerPath");
    visibleProjectInput?.focus();
    visibleProjectInput?.select();
    toast(`无法打开目录选择窗口：${error.message}`);
    return null;
  }
  if (!result.ok || !result.path) {
    if (!result.cancelled) toast(`选择项目目录失败：${result.error || "未知错误"}`);
    if (!hasProjectPath()) renderNoProjectSelected();
    return null;
  }
  $("#projectPath").value = result.path;
  saveProjectPath(result.path);
  try {
    const scan = await scanProject();
    if (notifySuccess) toast("项目目录已选择");
    return scan;
  } catch (error) {
    toast(`项目目录已选择，但扫描失败：${error.message}`);
    return null;
  }
}

async function switchProject(path, notify = true) {
  const nextPath = (path || "").trim();
  if (!nextPath) {
    toast("请先输入或选择项目目录");
    return null;
  }
  $("#projectPath").value = nextPath;
  saveProjectPath(nextPath);
  const scan = await scanProject({ notify });
  return scan;
}

async function chooseConfigDirectory(key) {
  const input = $(`#setting-${key}`);
  const prompts = {
    ecc_home: t("选择 ECC_HOME：包含 commands、skills、agents、rules 的 ECC 源目录"),
    profile_home: t("选择 PROFILE_HOME：保存 ECC profiles 和 ecc-use.config.json 的目录"),
  };
  let result;
  try {
    result = await api("/api/choose-folder", {
      current: input.value || state.config[key] || state.cwd,
      prompt: prompts[key] || t("选择目录"),
    });
  } catch (error) {
    input.focus();
    input.select();
    toast(`无法打开目录选择窗口：${error.message}`);
    return;
  }
  if (!result.ok || !result.path) {
    if (!result.cancelled) toast(`选择目录失败：${result.error || "未知错误"}`);
    return;
  }
  input.value = result.path;
}

async function saveSettings() {
  const eccHome = $("#setting-ecc_home").value.trim();
  const profileHome = $("#setting-profile_home").value.trim();
  const generatedCodexFile = $("#setting-generated_codex_file").value.trim();
  const generatedAntigravityFile = $("#setting-generated_antigravity_file").value.trim();
  const result = await api("/api/settings", {
    ecc_home: eccHome,
    profile_home: profileHome,
    generated_codex_file: generatedCodexFile,
    generated_antigravity_file: generatedAntigravityFile,
    enable_claude: $("#setting-enable_claude").checked,
    enable_codex: $("#setting-enable_codex").checked,
    enable_antigravity: $("#setting-enable_antigravity").checked,
    manage_agents_md: $("#setting-manage_agents_md").checked,
  });
  state.config = result.config;
  await loadCatalog();
  if (hasProjectPath()) await scanProject();
  else renderNoProjectSelected();
  toast("设置已保存");
}

async function refreshStatus() {
  const data = await api("/api/status", { project: $("#projectPath").value });
  state.lastTaskRun = data.last_task_run || state.lastTaskRun;
  const components = Object.entries(data.components || {});
  const runtimeExternal = data.runtime_external_required || [];
  const skipped = data.skipped_existing || [];
  const commandHealth = renderCommandHealth(data.command_health);
  const profileSummary = `
    <div class="grid two">
      <article class="status-card"><h3>Profile</h3>
        <div class="status-line"><span>${escapeHtml(t("初始阶段"))}</span><strong>${escapeHtml(data.initial_phase || t("未设置"))}</strong></div>
        <div class="status-line"><span>${escapeHtml(t("已追加阶段"))}</span><strong>${escapeList(data.added_phases)}</strong></div>
        <div class="status-line"><span>${escapeHtml(t("技术架构"))}</span><strong>${escapeHtml(data.architecture || t("未设置"))}</strong></div>
        <div class="status-line"><span>${escapeHtml(t("技术栈片段"))}</span><strong>${escapeList(data.project_types)}</strong></div>
        <div class="status-line"><span>${escapeHtml(t("能力包"))}</span><strong>${escapeList(data.packs)}</strong></div>
      </article>
      <article class="status-card"><h3>${escapeHtml(t("操作"))}</h3>
        ${data.architecture ? `<button data-remove-profile="${escapeAttr(data.architecture)}">${escapeHtml(t("移除"))} ${escapeHtml(data.architecture)}</button>` : ""}
        ${(data.packs || []).map((id) => `<button data-remove-profile="${escapeAttr(id)}">${escapeHtml(t("移除"))} ${escapeHtml(id)}</button>`).join(" ")}
        ${(data.project_types || []).map((id) => `<button data-remove-profile="${escapeAttr(id)}">${escapeHtml(t("移除"))} ${escapeHtml(id)}</button>`).join(" ")}
        ${(data.added_phases || []).map((id) => `<button data-remove-profile="${escapeAttr(id)}">${escapeHtml(t("移除"))} ${escapeHtml(id)}</button>`).join(" ")}
      </article>
    </div>
  `;
  const componentRows = components.length
    ? components.map(([component, item]) => `
      <div class="component-row">
        <code>${escapeHtml(component)}</code>
        <span class="muted">${escapeList(item.required_by)}</span>
        <span class="badge">${escapeHtml(uiText(item.kind))}</span>
      </div>
    `).join("")
    : `<div class="empty">${escapeHtml(t("当前项目还没有 ecc-use 管理的组件。"))}</div>`;
  const skippedRows = skipped.length
    ? skipped.map((item) => `<li><code>${escapeHtml(item.component)}</code><div class="muted">${escapeHtml(uiSentence(item.reason))} · ${escapeHtml(item.target)}</div></li>`).join("")
    : `<div class="empty">${escapeHtml(t("无"))}</div>`;
  const runtimeRows = runtimeExternal.length
    ? runtimeExternal.map((item) => `<li><code>${escapeHtml(item.name)}</code><div class="muted">${escapeHtml(t("外部初始化："))}${escapeList(item.external_install)}</div></li>`).join("")
    : `<div class="empty">${escapeHtml(t("无"))}</div>`;
  const lastTask = data.last_task_run
    ? `<div class="preview-group"><h3>${escapeHtml(t("最近任务"))}</h3>
        <div class="component-row task-status-row">
          <code>${escapeHtml(uiSentence(data.last_task_run.goal))}</code>
          <span class="badge ${taskStatusBadgeClass(data.last_task_run.status)}">${escapeHtml(uiStatusLabel(data.last_task_run.label || data.last_task_run.status))}</span>
          <button data-page-jump="task">${escapeHtml(t("查看任务结果"))}</button>
        </div>
      </div>`
    : "";
  $("#statusContent").innerHTML = `
    ${renderIssuesPanel("状态问题与选项", data.issues || [], "当前状态没有 warning/error。")}
    ${profileSummary}
    ${lastTask}
    ${commandHealth}
    <div class="section-block"><h2>${escapeHtml(t("组件"))}</h2>${componentRows}</div>
    <div class="preview-group"><h3>${escapeHtml(t("skipped_existing"))}</h3><ul class="preview-list">${skippedRows}</ul></div>
    <div class="preview-group"><h3>${escapeHtml(t("runtime / external 待确认"))}</h3><ul class="preview-list">${runtimeRows}</ul></div>
  `;
}

function renderAssetItems(items, emptyText) {
  if (!items.length) return `<div class="empty">${escapeHtml(uiSentence(emptyText))}</div>`;
  return `
    <div class="asset-list">
      ${items.map((item) => {
        const owners = (item.owners || []).map((owner) => owner.label || owner.profile_id).join("；");
        return `
          <div class="asset-row">
            <code>${escapeHtml(item.name)}</code>
            <span class="badge ${item.status === "covered" ? "ok" : item.status === "missing_reference" ? "error" : "warning"}">
              ${escapeHtml(item.status === "covered" ? t("已加入可选项") : item.status === "missing_reference" ? t("找不到源文件") : t("未加入可选项"))}
            </span>
            <span class="muted">${escapeHtml(owners || t("还没有挂到阶段 / 架构 / 类型 / 能力包"))}</span>
          </div>
        `;
      }).join("")}
    </div>
  `;
}

function renderClassifiedItems(items) {
  if (!items.length) return `<div class="empty">${escapeHtml(t("暂无内容"))}</div>`;
  return `
    <div class="asset-chip-list">
      ${items.map((item) => `
        <span class="asset-chip">
          <span class="badge">${escapeHtml(item.kind)}</span>
          <code>${escapeHtml(item.name)}</code>
          <small>${escapeHtml(uiSentence(item.reason || ""))}</small>
        </span>
      `).join("")}
    </div>
  `;
}

function renderAssetClassification(classification) {
  const categories = classification?.categories || [];
  const uncategorized = classification?.uncategorized || [];
  if (!categories.length && !uncategorized.length) return "";
  return `
    <section class="asset-classification">
      <div class="asset-classification-head">
        <div>
          <h2>${escapeHtml(t("待整理内容的多关联分类"))}</h2>
          <p class="muted">${escapeHtml(t("一个内容可以同时出现在多个分类里；这里先呈现关联关系，后续再决定哪些要沉淀成能力包、技术栈片段或主架构。"))}</p>
        </div>
      </div>
      <div class="asset-category-list">
        ${categories.map((category) => {
          const kindBadges = Object.entries(category.counts || {})
            .filter(([, value]) => value)
            .map(([kind, value]) => `<span class="badge">${escapeHtml(kind)} ${escapeHtml(value)}</span>`)
            .join("");
          return `
            <details class="asset-category">
              <summary>
                <span>
                  <strong>${escapeHtml(localizedName(category))}</strong>
                  <small>${escapeHtml(localizedDescription(category))}</small>
                </span>
                <span class="pack-meta">
                  <span class="badge ok">${escapeHtml(uiSentence(`${category.items.length} 个关联内容`))}</span>
                  ${kindBadges}
                </span>
              </summary>
              ${renderClassifiedItems(category.items)}
            </details>
          `;
        }).join("")}
        ${uncategorized.length ? `
          <details class="asset-category">
            <summary>
              <span>
                <strong>${escapeHtml(t("待人工判断"))}</strong>
                <small>${escapeHtml(t("名称和说明暂时无法稳定归类，需要人工看内容后决定。"))}</small>
              </span>
              <span class="pack-meta"><span class="badge warning">${escapeHtml(uiSentence(`${uncategorized.length} 个`))}</span></span>
            </summary>
            ${renderClassifiedItems(uncategorized)}
          </details>
        ` : ""}
      </div>
    </section>
  `;
}

function relationTypeLabel(type) {
  if (type === "explicit") return t("明确关联");
  if (type === "strong") return t("强关联");
  if (type === "mention") return t("弱线索");
  if (type === "profile") return t("Profile 引用");
  return type || t("关联");
}

function relationBadgeClass(type) {
  if (type === "explicit") return "ok";
  if (type === "strong") return "warning";
  if (type === "mention") return "";
  return "";
}

function renderCommandRelations(relations) {
  const commands = relations?.commands || [];
  if (!commands.length) return "";
  const stats = relations?.stats || {};
  return `
    <section class="asset-relations">
      <div class="asset-classification-head">
        <div>
          <h2>${escapeHtml(t("命令关联图"))}</h2>
          <p class="muted">${escapeHtml(t("按 command 展示它建议关联的 skills、agents、rules。这里是审计建议，不会自动改变安装结果。"))}</p>
        </div>
        <div class="pack-meta">
          <span class="badge">${escapeHtml(stats.commands || commands.length)} commands</span>
          <span class="badge ok">${escapeHtml(stats.commands_with_relations || 0)} ${escapeHtml(t("有关系"))}</span>
          <span class="badge warning">${escapeHtml(stats.suggested_edges || 0)} ${escapeHtml(t("建议关系"))}</span>
        </div>
      </div>
      <div class="command-relation-list">
        ${commands.map((command) => `
          <details class="command-relation">
            <summary>
              <span>
                <strong>${escapeHtml(command.name)}</strong>
                <small>${escapeHtml(uiSentence(command.message || `${command.relation_count} 个关联`))}</small>
              </span>
              <span class="pack-meta">
                <span class="badge ${command.status === "covered" ? "ok" : "warning"}">${escapeHtml(command.status === "covered" ? t("已加入可选项") : t("未加入可选项"))}</span>
                <span class="badge">${escapeHtml(command.relation_count)} edges</span>
              </span>
            </summary>
            ${command.relations.length ? `
              <div class="relation-edge-list">
                ${command.relations.map((edge) => `
                  <div class="relation-edge">
                    <code>${escapeHtml(edge.target)}</code>
                    <span class="badge ${relationBadgeClass(edge.relation_type)}">${relationTypeLabel(edge.relation_type)}</span>
                    <span class="muted">${escapeHtml(uiText(edge.type))}</span>
                    <span class="muted">${edge.line_hint ? `L${escapeHtml(edge.line_hint)}: ` : ""}${escapeHtml(edge.evidence || "")}</span>
                  </div>
                `).join("")}
              </div>
            ` : `<div class="empty">${escapeHtml(t("未发现明确关联。"))}</div>`}
          </details>
        `).join("")}
      </div>
    </section>
  `;
}

function targetTypeLabel(type) {
  const labels = {
    phase: "阶段",
    architecture: "技术架构",
    "project-type": "技术栈片段",
    pack: "能力包",
    "command-dependency": "命令依赖",
    "global-core": "全局基础能力",
    hold: "暂不收编",
  };
  return labels[type] ? t(labels[type]) : (type || t("目标"));
}

function actionLabel(action) {
  const labels = {
    add_to_profile_required: "加入 profile required",
    confirm_command_dependency: "写入 command frontmatter",
    hold: "暂不收编",
  };
  return labels[action] ? t(labels[action]) : (action || t("建议"));
}

function renderSyncOverview(data) {
  const sync = data.sync || {};
  const contract = sync.command_contracts || {};
  const compatibility = sync.compatibility || {};
  const coverage = contract.total ? Math.round((contract.declared || 0) * 100 / contract.total) : 0;
  return `
    <section class="asset-classification">
      <div class="asset-classification-head">
        <div>
          <h2>${escapeHtml(t("检测概览"))}</h2>
          <p class="muted">ECC ${escapeHtml(shortPath(sync.ecc_home))} · Profiles ${escapeHtml(shortPath(sync.profile_home))}</p>
        </div>
        <div class="pack-meta">
          <span class="badge">${escapeHtml(sync.version || "no VERSION")}</span>
          <span class="badge ${compatibility.status === "supported" ? "ok" : "warning"}">${escapeHtml(compatibility.status || "unknown compatibility")}</span>
          <span class="badge">${escapeHtml(sync.git_branch || "no branch")}</span>
          <span class="badge">${escapeHtml(sync.git_commit ? sync.git_commit.slice(0, 8) : "no commit")}</span>
        </div>
      </div>
      <div class="asset-breakdown">
        <article><strong>${escapeHtml(data.totals?.source ?? 0)}</strong><span>${escapeHtml(t("本地资产总量"))}</span><b>commands / skills / agents / rules</b></article>
        <article><strong>${escapeHtml(data.totals?.unassigned ?? 0)}</strong><span>${escapeHtml(t("新增未归类"))}</span><b>${escapeHtml(t("ECC 有，但 profile 未引用"))}</b></article>
        <article><strong>${escapeHtml(data.totals?.missing_references ?? 0)}</strong><span>${escapeHtml(t("缺失引用"))}</span><b>${escapeHtml(t("profile 引用但 ECC 不存在"))}</b></article>
        <article><strong>${escapeHtml(coverage)}%</strong><span>${escapeHtml(t("命令契约覆盖率"))}</span><b>${escapeHtml(contract.declared || 0)}/${escapeHtml(contract.total || 0)} ${escapeHtml(t("已声明"))}</b></article>
      </div>
    </section>
  `;
}

function renderSuggestions(suggestions) {
  if (!suggestions?.length) {
    return `<section class="asset-classification"><h2>${escapeHtml(t("归类建议"))}</h2><div class="empty">${escapeHtml(t("暂无建议。"))}</div></section>`;
  }
  return `
    <section class="asset-classification">
      <div class="asset-classification-head">
        <div>
          <h2>${escapeHtml(t("归类建议与应用区"))}</h2>
          <p class="muted">${escapeHtml(t("勾选后才会写入 profile JSON 或 command frontmatter；未勾选的建议只作为参考。"))}</p>
        </div>
        <div class="pack-meta"><span class="badge warning">${escapeHtml(uiSentence(`${suggestions.length} 条建议`))}</span></div>
      </div>
      <div class="asset-list">
      ${suggestions.map((item, index) => {
        const disabled = item.action === "hold" || item.target_type === "global-core";
        const levelSelector = item.action === "confirm_command_dependency"
            ? `<select data-suggestion-level="${index}">
                <option value="required" ${item.suggested_level === "required" ? "selected" : ""}>required</option>
                <option value="optional" ${item.suggested_level !== "required" ? "selected" : ""}>optional</option>
              </select>`
            : "";
          return `
            <label class="asset-row suggestion-row">
              <input type="checkbox" data-suggestion-select="${index}" ${disabled ? "disabled" : ""} />
              <code>${escapeHtml(item.kind)}/${escapeHtml(item.name)}</code>
              <span class="badge ${disabled ? "info" : "warning"}">${escapeHtml(targetTypeLabel(item.target_type))}</span>
              <span class="badge">${escapeHtml(item.target_id || "")}</span>
              <span class="muted">${escapeHtml(actionLabel(item.action))} · ${escapeHtml((Number(item.confidence || 0) * 100).toFixed(0))}%</span>
              ${levelSelector}
              <span class="muted">${escapeHtml(uiSentence(item.reason || ""))}</span>
            </label>
          `;
        }).join("")}
      </div>
    </section>
  `;
}

function renderCommandContracts(contracts) {
  if (!contracts?.length) return "";
  const stats = contracts.reduce((acc, item) => {
    acc[item.health] = (acc[item.health] || 0) + 1;
    return acc;
  }, {});
  return `
    <section class="asset-relations">
      <div class="asset-classification-head">
        <div>
          <h2>${escapeHtml(t("命令依赖契约"))}</h2>
          <p class="muted">${escapeHtml(t("frontmatter 的 requires / optional 是机器契约；Related 只作为候选线索。"))}</p>
        </div>
        <div class="pack-meta">
          <span class="badge ok">${escapeHtml(stats.ready || 0)} ready</span>
          <span class="badge warning">${escapeHtml(stats.degraded || 0)} degraded</span>
          <span class="badge error">${escapeHtml(stats.blocked || 0)} blocked</span>
          <span class="badge info">${escapeHtml(stats.unknown || 0)} unknown</span>
        </div>
      </div>
      <div class="command-relation-list">
        ${contracts.map((item) => `
          <details class="command-relation">
            <summary>
              <span>
                <strong>${escapeHtml(item.command)}</strong>
                <small>${escapeHtml(uiSentence(item.status))}</small>
              </span>
              <span class="pack-meta">
                <span class="badge ${commandHealthBadgeClass(item.health)}">${escapeHtml(uiStatusLabel(item.label || item.health))}</span>
                <span class="badge">${escapeHtml(item.declared?.source || "none")}</span>
                <span class="badge warning">${escapeHtml((item.candidates || []).length)} ${escapeHtml(t("候选"))}</span>
                ${(item.missing || []).length ? `<span class="badge error">${escapeHtml(item.missing.length)} ${escapeHtml(t("缺失"))}</span>` : ""}
              </span>
            </summary>
            ${(item.missing || []).length ? `
              <div class="relation-edge-list">
                ${item.missing.map((missing) => `
                  <div class="relation-edge">
                    <code>${escapeHtml(missing.kind)}/${escapeHtml(missing.name)}</code>
                    <span class="badge error">${escapeHtml(missing.level)}</span>
                    <span class="muted">${escapeHtml(uiSentence(missing.reason))}</span>
                  </div>
                `).join("")}
              </div>
            ` : `<div class="empty">${escapeHtml(t("契约引用的本地组件都存在。"))}</div>`}
            ${(item.candidates || []).length ? `
              <h3>${escapeHtml(t("候选未确认"))}</h3>
              <div class="relation-edge-list">
                ${item.candidates.map((candidate) => `
                  <div class="relation-edge">
                    <code>${escapeHtml(candidate.kind)}/${escapeHtml(candidate.name)}</code>
                    <span class="badge ${relationBadgeClass(candidate.relation_type)}">${relationTypeLabel(candidate.relation_type)}</span>
                    <span class="muted">${candidate.line_hint ? `L${escapeHtml(candidate.line_hint)}: ` : ""}${escapeHtml(candidate.evidence || "")}</span>
                  </div>
                `).join("")}
              </div>
            ` : ""}
          </details>
        `).join("")}
      </div>
    </section>
  `;
}

function renderProfileHealth(rows) {
  const problems = (rows || []).filter((item) => (item.missing || []).length || (item.stale || []).length);
  return `
    <section class="asset-classification">
      <div class="asset-classification-head">
        <div>
          <h2>${escapeHtml(t("Profile 健康"))}</h2>
          <p class="muted">${escapeHtml(t("阶段、技术架构、技术栈片段和能力包引用的本地资产是否还存在。"))}</p>
        </div>
        <div class="pack-meta">
          <span class="badge ok">${escapeHtml((rows || []).length - problems.length)} ok</span>
          <span class="badge ${problems.length ? "error" : "ok"}">${escapeHtml(problems.length)} ${escapeHtml(t("需要处理"))}</span>
        </div>
      </div>
      ${problems.length ? `
        <div class="asset-list">
          ${problems.map((profile) => `
            <div class="asset-row">
              <code>${escapeHtml(profile.profile_id)}</code>
              <span class="badge error">${escapeHtml(profile.group)}</span>
              <span class="muted">${escapeList((profile.missing || []).map((item) => item.component), "；")}</span>
            </div>
          `).join("")}
        </div>
      ` : `<div class="empty">${escapeHtml(t("没有发现缺失引用。"))}</div>`}
    </section>
  `;
}

function assetIssues(data) {
  const issues = [];
  const totals = data.totals || {};
  const suggestions = data.suggestions || [];
  const commandStats = (data.command_contracts || []).reduce((acc, item) => {
    acc[item.health] = (acc[item.health] || 0) + 1;
    return acc;
  }, {});
  if ((totals.missing_references || 0) > 0) {
    issues.push({
      id: "assets-missing-references",
      level: "error",
      title: "能力治理缺失引用",
      message: `${totals.missing_references} 个 profile 或 command 依赖引用找不到源文件。`,
      impact: "缺失引用可能导致计划失败或命令 blocked。",
      actions: [
        { kind: "manual_guide", label: "补齐或移除引用", description: "根据下方缺失列表补齐 ECC_HOME 源文件，或调整 profile/command 契约。", mode: "manual" },
      ],
    });
  }
  if (suggestions.length) {
    issues.push({
      id: "assets-suggestions",
      level: "warning",
      title: "存在可应用的治理建议",
      message: `${suggestions.length} 条建议可用于归类或补充命令依赖。`,
      impact: "不应用建议不会阻断使用，但命令契约和覆盖率可能不完整。",
      actions: [
        { kind: "apply_suggestions", label: "应用选中建议", description: "先勾选建议，再确认写入 profile 或 command frontmatter。", mode: "confirm" },
        { kind: "manual_guide", label: "跳过", description: "暂不应用建议，保留当前配置。", mode: "manual" },
      ],
    });
  }
  if ((commandStats.blocked || 0) > 0 || (commandStats.degraded || 0) > 0 || (commandStats.unknown || 0) > 0) {
    issues.push({
      id: "assets-command-contracts",
      level: (commandStats.blocked || 0) > 0 ? "error" : "warning",
      title: "命令契约需要处理",
      message: `${commandStats.blocked || 0} blocked，${commandStats.degraded || 0} degraded，${commandStats.unknown || 0} unknown。`,
      impact: "命令依赖契约不完整会影响计划判断和满配安装。",
      actions: [
        { kind: "manual_guide", label: "查看下方契约", description: "展开命令依赖契约，按缺失和候选项处理。", mode: "manual" },
      ],
    });
  }
  return issues;
}

async function refreshAssets() {
  const data = await api("/api/ecc/scan", {});
  state.assetScan = data;
  const groups = data.groups || {};
  const totals = data.totals || {};
  const pendingKinds = Object.values(groups).filter((group) => (group.unassigned || 0) > 0).length;
  const summaryCards = [
    ["ECC 内容总量", totals.source ?? 0, "commands / skills / agents / rules"],
    ["已加入可选项", totals.covered ?? 0, "当前阶段、架构、类型和能力包会使用"],
    ["待整理内容", `${pendingKinds} 类`, "下方按 commands / skills / agents / rules 展开"],
    ["找不到源文件", totals.missing_references ?? 0, "可选项引用了但 ECC_HOME 不存在"],
  ];
  const groupLabels = {
    commands: ["commands", "Claude 命令，比如 review-pr.md、python-review.md"],
    skills: ["skills", "技能目录，比如 nextjs-turbopack、github-ops"],
    agents: ["agents", "agent 文件，比如 rust-reviewer.md、architect.md"],
    rules: ["rules", "规则目录，比如 rust、java、swift"],
  };
  $("#assetsContent").innerHTML = `
    ${renderIssuesPanel("能力治理问题与选项", assetIssues(data), "能力治理没有 warning/error。")}
    ${renderSyncOverview(data)}
    ${renderSuggestions(data.suggestions || [])}
    ${renderCommandContracts(data.command_contracts || [])}
    ${renderProfileHealth(data.profile_health || [])}
    <div class="asset-summary">
      ${summaryCards.map(([label, value, note]) => `
        <article class="status-card">
          <h3>${escapeHtml(t(label))}</h3>
          <strong class="asset-number">${escapeHtml(uiSentence(value))}</strong>
          <p class="muted">${escapeHtml(t(note))}</p>
        </article>
      `).join("")}
    </div>
    <div class="asset-breakdown">
      ${Object.entries(groupLabels).map(([kind, [label, description]]) => {
        const group = groups[kind] || { total: 0, covered: 0, unassigned: 0, missing: [], items: [] };
        return `
          <article>
            <strong>${escapeHtml(label)}</strong>
            <span>${escapeHtml(description)}</span>
            <b>${escapeHtml(uiSentence(`${group.unassigned || 0} 个未加入可选项`))}</b>
          </article>
        `;
      }).join("")}
    </div>
    ${renderAssetClassification(data.classification)}
    ${renderCommandRelations(data.relations)}
    ${Object.entries(groupLabels).map(([kind, [label, description]]) => {
      const group = groups[kind] || { total: 0, covered: 0, unassigned: 0, missing: [], items: [] };
      const missing = group.missing || [];
      const unassigned = (group.items || []).filter((item) => item.status === "unassigned");
      const covered = (group.items || []).filter((item) => item.status === "covered");
      return `
        <div class="asset-group">
          <div class="asset-group-head">
            <div>
              <h2>${escapeHtml(label)}</h2>
              <p class="muted">${escapeHtml(description)}</p>
              <p class="muted">${escapeHtml(group.source_dir || "")}</p>
            </div>
            <div class="pack-meta">
              <span class="badge">${escapeHtml(uiSentence(`${group.total || 0} 总数`))}</span>
              <span class="badge ok">${escapeHtml(uiSentence(`${group.covered || 0} 已加入可选项`))}</span>
              <span class="badge warning">${escapeHtml(uiSentence(`${group.unassigned || 0} 未加入可选项`))}</span>
              ${missing.length ? `<span class="badge error">${escapeHtml(uiSentence(`${missing.length} 找不到源文件`))}</span>` : ""}
            </div>
          </div>
          ${missing.length ? `<h3>${escapeHtml(t("找不到源文件的引用"))}</h3>${renderAssetItems(missing, "没有找不到源文件的引用")}` : ""}
          <h3>${escapeHtml(t("未加入可选项"))}</h3>
          ${renderAssetItems(unassigned, "没有未加入可选项的内容")}
          <details>
            <summary>${escapeHtml(t("查看已加入可选项的内容"))}</summary>
            ${renderAssetItems(covered, "暂无已加入可选项的内容")}
          </details>
        </div>
      `;
    }).join("")}
  `;
}

async function applySelectedSuggestions() {
  const suggestions = state.assetScan?.suggestions || [];
  const selected = $$("[data-suggestion-select]:checked").map((checkbox) => {
    const index = Number(checkbox.dataset.suggestionSelect);
    const item = { ...suggestions[index] };
    const level = $(`[data-suggestion-level="${index}"]`)?.value;
    if (level) item.level = level;
    return item;
  });
  if (!selected.length) {
    toast("请先勾选要应用的建议");
    return;
  }
  if (!window.confirm(uiSentence(`确认应用 ${selected.length} 条治理建议？这会写入 profile JSON 或 command frontmatter。`))) {
    toast("已取消应用建议");
    return;
  }
  const result = await api("/api/ecc/apply-suggestions", { suggestions: selected });
  await loadCatalog();
  await refreshAssets();
  toast(`已应用 ${result.applied?.length || 0} 条建议，跳过 ${result.skipped?.length || 0} 条`);
}

async function runDoctor(fix) {
  const data = await api("/api/doctor", { project: $("#projectPath").value, fix });
  const checks = (data.checks || []).map((check) => `
    <div class="doctor-item">
      ${badge(check.level)}
      <strong>${escapeHtml(uiSentence(check.name))}</strong>
      <span>${escapeHtml(uiSentence(check.message))}${check.impact ? `<br><small class="muted">${escapeHtml(t("影响："))}${escapeHtml(uiSentence(check.impact))}</small>` : ""}</span>
      <span class="issue-actions">${renderIssueActions(check)}</span>
    </div>
  `).join("");
  const fixes = (data.fixes || []).length
    ? `<div class="preview-group"><h3>${escapeHtml(t("安全修复记录"))}</h3><ul class="preview-list">${data.fixes.map((item) => `<li><code>${escapeHtml(item.name)}</code><div class="muted">${escapeHtml(uiSentence(item.message))}</div></li>`).join("")}</ul></div>`
    : "";
  $("#doctorContent").innerHTML = `${renderIssuesPanel("Doctor 问题与选项", data.issues || [], "Doctor 没有 warning/error。")}${fixes}${checks}`;
  if (fix) {
    const count = (data.fixes || []).length;
    toast(count ? `安全修复已执行：${count} 项` : "Doctor 未发现需要自动修复的项目");
  }
}

function renderSettings() {
  const locked = {
    link_mode: "symlink",
    overwrite_policy: "skip",
    manage_settings_json: "false",
  };
  const editablePath = (key, label, value, note) => `
    <div class="setting-card editable-setting">
      <label class="field-label" for="setting-${key}">${label}</label>
      <div class="path-row">
        <input id="setting-${key}" type="text" value="${escapeAttr(value)}" spellcheck="false" />
      <button data-setting-choose="${key}">${escapeHtml(t("选择目录"))}</button>
      </div>
      <div class="muted setting-note">${note}</div>
    </div>
  `;
  const editableText = (key, label, value, note, placeholder = "") => `
    <div class="setting-card editable-setting">
      <label class="field-label" for="setting-${key}">${label}</label>
      <input id="setting-${key}" type="text" value="${escapeAttr(value || "")}" placeholder="${escapeAttr(placeholder)}" spellcheck="false" />
      <div class="muted setting-note">${note}</div>
    </div>
  `;
  const toggleSetting = (key, label, checked, note) => `
    <label class="setting-card toggle-setting" for="setting-${key}">
      <span class="toggle-setting-head">
        <span>
          <strong>${label}</strong>
          <small class="muted">${note}</small>
        </span>
        <input id="setting-${key}" type="checkbox" ${checked ? "checked" : ""} />
      </span>
    </label>
  `;
  const lockedCard = (key, value) => `
    <div class="setting-card">
      <strong>${escapeHtml(key)}</strong>
      <code>${escapeHtml(value)}</code>
    </div>
  `;

  $("#settingsContent").innerHTML = `
    ${editablePath("ecc_home", "ECC_HOME", state.config.ecc_home, "ECC 组件来源目录，需要包含 commands、skills、agents、rules 等子目录。")}
    ${editablePath("profile_home", "PROFILE_HOME", state.config.profile_home, "Profiles 和 ecc-use.config.json 的保存目录。")}
    ${editableText("generated_codex_file", "Codex 生成文件", state.config.generated_codex_file, "生成给 Codex 看的完整说明文件名。", "AGENTS.ecc.generated.md")}
    ${editableText("generated_antigravity_file", "Antigravity 生成文件", state.config.generated_antigravity_file, "生成给 Google Antigravity 看的完整说明文件名。", "ANTIGRAVITY.ecc.generated.md")}
    ${toggleSetting("enable_claude", "使用 Claude Code", state.config.enable_claude !== false, "选中后才生成 Claude Code 的 .claude/commands、skills、agents、rules 和 CLAUDE 说明文件。")}
    ${toggleSetting("enable_codex", "使用 Codex", state.config.enable_codex === true, "选中后才生成 Codex 的 AGENTS.md 托管区、.agents/skills、.codex/agents 和 .codex/rules；ECC commands 会适配为 skills。")}
    ${toggleSetting("enable_antigravity", "使用 Antigravity", state.config.enable_antigravity === true, "选中后才生成 Antigravity 的 AGENTS.md 托管区、.agents/agents.md、.agents/skills、.agents/rules 和 .agents/workflows。")}
    ${toggleSetting("manage_agents_md", "托管 AGENTS.md", state.config.manage_agents_md !== false, "Codex / Antigravity 需要这个入口才能稳定读取本次装配；只更新带 ecc-manager 标记的托管区，不覆盖用户已有内容。")}
    <div class="setting-card language-setting">
      <strong>${escapeHtml(t("界面语言"))}</strong>
      <div class="language-switcher" aria-label="Language">
        <button class="language-option" type="button" data-lang="en" aria-pressed="false">English</button>
        <button class="language-option" type="button" data-lang="zh-CN" aria-pressed="false">中文</button>
      </div>
      <div class="muted setting-note">${escapeHtml(t("首次打开会跟随浏览器语言，手动切换后会记住选择。"))}</div>
    </div>
    <div class="settings-actions">
      <button class="primary" id="saveSettingsBtn">${escapeHtml(t("保存设置"))}</button>
      <button id="resetSettingsBtn">${escapeHtml(t("恢复当前已保存值"))}</button>
    </div>
    ${lockedCard("generated_claude_file", state.config.generated_claude_file)}
    ${lockedCard("link_mode", locked.link_mode)}
    ${lockedCard("overwrite_policy", locked.overwrite_policy)}
    ${lockedCard("manage_settings_json", locked.manage_settings_json)}
  `;
}

function bindEvents() {
  $$(".nav-item").forEach((item) => item.addEventListener("click", () => setPage(item.dataset.page)));
  $("#chooseProjectBtn").addEventListener("click", async () => {
    await chooseProjectDirectory();
  });
  $("#useCwdBtn")?.addEventListener("click", async () => {
    await withToast(() => switchProject(state.cwd), "扫描当前目录失败");
  });
  $("#useTypedProjectBtn")?.addEventListener("click", async () => {
    await withToast(() => switchProject($("#projectPickerPath").value, true), "扫描项目失败");
  });
  $("#projectPickerPath")?.addEventListener("keydown", async (event) => {
    if (event.key === "Enter") {
      await withToast(() => switchProject($("#projectPickerPath").value, true), "扫描项目失败");
    }
  });
  $("#scanProjectBtn").addEventListener("click", () => scanProject({ notify: true }));
  $("#openClaudeBtn").addEventListener("click", async () => {
    await openProjectPath("CLAUDE.md", "CLAUDE.md", (scan) => scan.has_claude_md);
  });
  $("#openClaudeDirBtn").addEventListener("click", async () => {
    await openProjectPath(t(".claude 目录"), ".claude", (scan) => scan.has_claude_dir);
  });
  $("#openAgentsBtn").addEventListener("click", async () => {
    await openProjectPath("AGENTS.md", "AGENTS.md", (scan) => scan.has_agents_md);
  });
  $("#openCodexDirBtn").addEventListener("click", async () => {
    await openProjectPath(t(".codex 目录"), ".codex", (scan) => scan.has_codex_dir);
  });
  $("#initProfilesBtn").addEventListener("click", async () => {
    await withToast(async () => {
      const result = await api("/api/profiles/init", {});
      toast(`Profiles 已初始化：${result.created.length} 个文件`);
      await loadCatalog();
      await scanProject();
    }, "初始化 Profiles 失败");
  });
  $("#previewInitBtn").addEventListener("click", () => {
    state.lastActionPage = "init";
    withToast(() => makePlan("init", selectedInitProfiles()), "生成初始化预览失败");
  });
  $("#applyInitBtn").addEventListener("click", async () => {
    await withToast(async () => {
      state.lastActionPage = "init";
      const plan = await makePlan("init", selectedInitProfiles());
      if (plan.can_apply) await executeCurrentPlan();
    }, "初始化失败");
  });
  $("#previewStageBtn").addEventListener("click", () => {
    state.lastActionPage = "phases";
    withToast(() => makePlan("phase", actionableSelectedStagePhaseIds()), "生成阶段追加预览失败");
  });
  $("#applyStageBtn").addEventListener("click", async () => {
    await withToast(async () => {
      state.lastActionPage = "phases";
      const plan = await makePlan("phase", actionableSelectedStagePhaseIds());
      if (plan.can_apply) await executeCurrentPlan();
    }, "追加阶段失败");
  });
  $("#executePlanBtn").addEventListener("click", () => withToast(executeCurrentPlan, "执行失败"));
  $("#backToSelectionBtn").addEventListener("click", () => setPage(state.lastActionPage));
  $("#refreshStatusBtn").addEventListener("click", () => withToast(refreshStatus, "刷新状态失败"));
  $("#refreshAssetsBtn").addEventListener("click", () => withToast(refreshAssets, "刷新资产盘点失败"));
  $("#applySuggestionsBtn").addEventListener("click", () => withToast(applySelectedSuggestions, "应用建议失败"));
  $("#regenClaudeBtn").addEventListener("click", async () => {
    await withToast(async () => {
      await runDoctorFixWithConfirm();
      setPage("doctor");
    }, "重新生成说明文件失败");
  });
  $("#runDoctorBtn").addEventListener("click", () => withToast(() => runDoctor(false), "Doctor 检查失败"));
  $("#fixDoctorBtn").addEventListener("click", () => withToast(runDoctorFixWithConfirm, "Doctor 修复失败"));
  $("#taskToStatusBtn").addEventListener("click", () => setPage("status"));
  $("#taskToDoctorBtn").addEventListener("click", () => setPage("doctor"));

  document.addEventListener("click", async (event) => {
    const languageOption = event.target.closest(".language-option");
    if (languageOption) {
      setLang(languageOption.dataset.lang);
      return;
    }

    const issueAction = event.target.closest("[data-issue-action]");
    if (issueAction) {
      await withToast(async () => {
        await handleIssueAction(JSON.parse(issueAction.dataset.action || "{}"));
      }, "处理操作失败");
      return;
    }

    const choice = event.target.closest(".choice");
    if (choice) {
      const id = choice.dataset.profile;
      const type = choice.dataset.type;
      if (type === "phase") state.selectedPhase = id;
      if (type === "architecture") state.selectedArchitecture = id;
      if (type === "stage-phase") {
        if (phaseStatus(id)) {
          renderDetail(profileById(id));
          return;
        }
        toggleSet(state.selectedStagePhases, id);
      }
      if (type === "project-type") toggleSet(state.selectedProjectTypes, id);
      if (type === "init-pack") toggleSet(state.selectedPacks, id);
      renderCatalog();
      renderDetail(profileById(id));
      return;
    }
    const recentProject = event.target.closest("[data-recent-project]");
    if (recentProject) {
      await withToast(() => switchProject(recentProject.dataset.recentProject, true), "切换项目失败");
      return;
    }
    const packRow = event.target.closest(".pack-row");
    if (packRow && !event.target.closest("button")) {
      renderDetail(profileById(packRow.dataset.profile));
      return;
    }
    const previewPack = event.target.dataset.packPreview;
    if (previewPack) {
      await withToast(async () => {
        state.lastActionPage = "packs";
        renderDetail(profileById(previewPack));
        await makePlan("add", [previewPack]);
      }, "生成能力包预览失败");
      return;
    }
    const addPack = event.target.dataset.packAdd;
    if (addPack) {
      await withToast(async () => {
        state.lastActionPage = "packs";
        renderDetail(profileById(addPack));
        const plan = await makePlan("add", [addPack]);
        if (plan.can_apply) await executeCurrentPlan();
      }, "添加能力包失败");
      return;
    }
    const removeProfile = event.target.dataset.removeProfile;
    if (removeProfile) {
      await withToast(async () => {
        if (!window.confirm(uiSentence(`确认移除 ${removeProfile}？\n\n只会删除仍然指向 ECC 源文件的 symlink；真实文件和冲突项会保留。`))) {
          return;
        }
        const result = await api("/api/remove", { project: $("#projectPath").value, profile_id: removeProfile });
        toast(result.ok ? `已移除 ${removeProfile}` : result.error);
        await refreshStatus();
      }, `移除 ${removeProfile} 失败`);
      return;
    }
    const pageJump = event.target.dataset.pageJump;
    if (pageJump) {
      setPage(pageJump);
      return;
    }
    const settingKey = event.target.dataset.settingChoose;
    if (settingKey) {
      await chooseConfigDirectory(settingKey);
      return;
    }
    if (event.target.id === "saveSettingsBtn") {
      await withToast(saveSettings, "保存设置失败");
      return;
    }
    if (event.target.id === "resetSettingsBtn") {
      renderSettings();
    }
  });
}

function toggleSet(set, id) {
  if (set.has(id)) set.delete(id);
  else set.add(id);
}

async function executeCurrentPlan() {
  if (!state.currentPlan) return;
  if (!state.currentPlan.can_apply) {
    toast("存在缺失源文件，不能执行");
    return;
  }
  if (!(await confirmInstallPlan(state.currentPlan))) {
    toast("已取消执行");
    return;
  }
  const result = await api("/api/apply", { plan: state.currentPlan });
  state.lastTaskRun = result.task_run || null;
  renderTaskResult(state.lastTaskRun);
  const label = state.lastTaskRun?.label || (result.ok ? "执行完成" : result.error || "执行失败");
  toast(label);
  await scanProject();
  setPage("task");
}

async function loadCatalog() {
  const data = await api("/api/catalog");
  state.config = data.config;
  state.catalog = data.profiles;
  renderCatalog();
  renderSettings();
  renderDetail(null);
  localizeTree();
}

async function init() {
  state.lang = initialLanguage();
  bindEvents();
  updateLanguageSwitcher();
  let localizeScheduled = false;
  const observer = new MutationObserver(() => {
    if (currentLang() === DEFAULT_LANGUAGE || localizeScheduled) return;
    localizeScheduled = true;
    window.requestAnimationFrame(() => {
      localizeScheduled = false;
      localizeTree();
    });
  });
  observer.observe(document.body, { childList: true, subtree: true });
  localizeTree();
  const boot = await api("/api/bootstrap");
  state.cwd = boot.cwd;
  state.homeDir = boot.home || "";
  state.config = boot.config;
  state.csrfToken = boot.csrf_token || "";
  const project = savedProjectPath();
  $("#projectPath").value = project;
  await loadCatalog();
  if (project) {
    await scanProject();
  } else {
    renderNoProjectSelected();
    await chooseProjectDirectory({ notifySuccess: false });
  }
  localizeTree();
}

init().catch((error) => {
  console.error(error);
  toast(error.message);
});
