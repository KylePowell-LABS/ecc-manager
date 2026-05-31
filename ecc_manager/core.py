"""Core ECC Manager logic shared by CLI and web UI."""

from __future__ import annotations

import json
import os
import re
import subprocess
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .default_profiles import ARCHITECTURES, COMMAND_DEPENDENCIES, DEFAULT_CONFIG, PACKS, PHASES, PROJECT_TYPES


KIND_DIRS = {
    "commands": ("commands", ".claude/commands"),
    "skills": ("skills", ".claude/skills"),
    "agents": ("agents", ".claude/agents"),
    "rules": ("rules", ".claude/rules/ecc"),
}

CODEX_SKILL_TARGET_ROOT = ".agents/skills"
CODEX_AGENT_TARGET_ROOT = ".codex/agents"
CODEX_RULE_TARGET_ROOT = ".codex/rules"
CODEX_MANAGED_BLOCK_START = "<!-- ecc-manager:codex:start -->"
CODEX_MANAGED_BLOCK_END = "<!-- ecc-manager:codex:end -->"
CODEX_AGENT_MARKER = "# Managed by ecc-manager for Codex."
CODEX_GENERATED_FILE_DEFAULT = "AGENTS.ecc.generated.md"
ANTIGRAVITY_RULE_TARGET_ROOT = ".agents/rules"
ANTIGRAVITY_WORKFLOW_TARGET_ROOT = ".agents/workflows"
ANTIGRAVITY_AGENTS_TARGET = ".agents/agents.md"
ANTIGRAVITY_LEGACY_WORKFLOW_TARGET_ROOT = ".agent/workflows"
ANTIGRAVITY_MANAGED_BLOCK_START = "<!-- ecc-manager:antigravity:start -->"
ANTIGRAVITY_MANAGED_BLOCK_END = "<!-- ecc-manager:antigravity:end -->"
ANTIGRAVITY_MARKER = "# Managed by ecc-manager for Antigravity."
ANTIGRAVITY_GENERATED_FILE_DEFAULT = "ANTIGRAVITY.ecc.generated.md"
ANTIGRAVITY_FILE_CHAR_LIMIT = 12000

LOCAL_DEPENDENCY_KINDS = tuple(KIND_DIRS)
REQUIRED_DEPENDENCY_KINDS = (*LOCAL_DEPENDENCY_KINDS, "runtime")
OPTIONAL_DEPENDENCY_KINDS = (*REQUIRED_DEPENDENCY_KINDS, "hooks", "mcp", "external_install")

COMMAND_HEALTH_LABELS = {
    "ready": "可完整运行",
    "needs_confirmation": "需要确认",
    "degraded": "可运行但能力降级",
    "blocked": "缺少必需组件",
    "unknown": "未声明依赖契约",
}

TASK_STATUS_LABELS = {
    "completed": "任务完成",
    "completed_with_warnings": "任务完成但需要跟进",
    "failed": "任务未完成",
}

ISSUE_LEVEL_LABELS = {
    "info": "提示",
    "warning": "需要跟进",
    "error": "需要处理",
}

GLOBAL_PLAN_SOURCE_NAME = "plan.md"
GLOBAL_PLAN_COMMAND_NAME = "ecc-plan.md"
GLOBAL_PLAN_ENTRY_NAME = "ecc-plan"
LEGACY_GLOBAL_PLAN_COMMAND_NAME = "plan.md"

RUNTIME_DEFINITIONS = {
    "ccg-workflow": {
        "description_zh": "multi-* 命令依赖的本地运行时。ECC 仓库没有内置这些文件时，需要用户确认后执行外部初始化。",
        "global_targets": [
            "~/.claude/bin/codeagent-wrapper",
            "~/.claude/.ccg/prompts",
        ],
        "source_candidates": [
            "runtime/ccg-workflow",
            "runtimes/ccg-workflow",
            ".claude/bin/codeagent-wrapper",
            ".claude/.ccg",
        ],
        "external_install": ["npx ccg-workflow"],
    }
}

ASSET_CATEGORY_DEFINITIONS = [
    {
        "id": "language-cpp",
        "name_zh": "C++ 工程栈",
        "description_zh": "C++ 构建、测试、审查和编码规则。",
        "terms": ["cpp", "c++", "cmake", "googletest", "gtest"],
    },
    {
        "id": "language-go",
        "name_zh": "Go 工程栈",
        "description_zh": "Go 构建、测试、审查和服务开发模式。",
        "terms": ["go", "golang"],
    },
    {
        "id": "language-kotlin-android",
        "name_zh": "Kotlin / Android",
        "description_zh": "Kotlin、Android、KMP、Compose、Gradle 和 HarmonyOS 相关内容。",
        "terms": ["kotlin", "android", "compose", "ktor", "exposed", "gradle", "harmonyos", "arkts"],
    },
    {
        "id": "language-flutter-dart",
        "name_zh": "Flutter / Dart",
        "description_zh": "Flutter、Dart 构建、测试、审查和 UI 模式。",
        "terms": ["flutter", "dart"],
    },
    {
        "id": "language-rust",
        "name_zh": "Rust 工程栈",
        "description_zh": "Rust 构建、测试、审查和安全模式。",
        "terms": ["rust", "cargo"],
    },
    {
        "id": "language-java-jvm",
        "name_zh": "Java / JVM",
        "description_zh": "Java、Spring Boot、Quarkus、JPA、Hibernate 和 JVM 服务模式。",
        "terms": ["java", "springboot", "spring", "quarkus", "jpa", "hibernate", "tinystruct"],
    },
    {
        "id": "language-dotnet",
        "name_zh": ".NET / C# / F#",
        "description_zh": "C#、F#、.NET 测试和工程模式。",
        "terms": ["csharp", "fsharp", "dotnet"],
    },
    {
        "id": "language-swift-ios",
        "name_zh": "Swift / iOS",
        "description_zh": "Swift、SwiftUI、iOS、FoundationModels 和 Apple 平台模式。",
        "terms": ["swift", "swiftui", "ios", "foundation", "liquid"],
    },
    {
        "id": "language-php-perl-ruby",
        "name_zh": "PHP / Perl / Ruby",
        "description_zh": "Laravel、Perl、PHP、Ruby 相关工程模式和规则。",
        "terms": ["laravel", "php", "perl", "ruby"],
    },
    {
        "id": "frontend-ui",
        "name_zh": "前端 / UI / 体验",
        "description_zh": "前端框架、UI、动效、浏览器验证和可视化体验。",
        "terms": ["frontend", "ui", "design", "motion", "angular", "vite", "nuxt", "vue", "slides", "browser", "click-path", "nextjs"],
    },
    {
        "id": "backend-api-data",
        "name_zh": "后端 / API / 数据",
        "description_zh": "后端服务、API、数据库、缓存、ORM 和连接器。",
        "terms": ["api", "backend", "database", "postgres", "mysql", "redis", "clickhouse", "jpa", "hibernate", "celery", "mcp-server", "connector", "content-hash", "regex", "structured-text"],
    },
    {
        "id": "ai-agent-orchestration",
        "name_zh": "AI Agent / 编排",
        "description_zh": "Agent 架构、评测、自主循环、多 agent 协同和模型路由。",
        "terms": ["agent", "agentic", "ai-first", "autonomous", "loop", "harness", "eval", "dmux", "devfleet", "santa", "gan", "model-route", "team-builder", "ralphinho", "planner", "council", "openclaw"],
    },
    {
        "id": "planning-prp",
        "name_zh": "规划 / PRP / 产品",
        "description_zh": "需求、规划、PRP、RFC、蓝图、产品判断和架构决策。",
        "terms": ["plan", "prd", "prp", "blueprint", "product", "rfc", "architecture-decision", "feature-dev", "architect"],
    },
    {
        "id": "quality-review-testing",
        "name_zh": "质量 / 审查 / 测试",
        "description_zh": "代码审查、构建修复、测试、TDD、验证和质量门禁。",
        "terms": ["review", "test", "testing", "tdd", "verification", "quality", "build", "fix", "harness-audit", "checkpoint", "gateguard", "plankton", "repo-scan", "refactor", "simplifier"],
    },
    {
        "id": "devops-runtime-ops",
        "name_zh": "DevOps / 运行时 / 成本",
        "description_zh": "部署、运行时、Docker、PM2、可观测、成本和环境管理。",
        "terms": ["pm2", "docker", "deploy", "deployment", "canary", "dashboard", "uncloud", "flox", "cost", "billing", "package", "setup-pm", "auto-update", "runtime", "workspace-surface"],
    },
    {
        "id": "github-project-ops",
        "name_zh": "GitHub / 项目协作",
        "description_zh": "GitHub、Git、PR、Jira、消息、通知和跨平台协作。",
        "terms": ["github", "git", "jira", "pr", "project", "project-flow", "notification", "email", "messages", "google-workspace", "crosspost", "x-api", "social", "chief-of-staff"],
    },
    {
        "id": "knowledge-memory-sessions",
        "name_zh": "记忆 / 学习 / 会话",
        "description_zh": "连续学习、instinct、会话保存恢复、知识库和上下文管理。",
        "terms": ["learn", "continuous-learning", "instinct", "session", "ck", "knowledge", "codemap", "token-budget", "conversation", "save-session", "resume-session", "projects", "promote", "prune", "aside"],
    },
    {
        "id": "security-safety",
        "name_zh": "安全 / 护栏 / 合规",
        "description_zh": "安全审查、护栏、合规、隐私、破坏性操作防护和交易风险。",
        "terms": ["security", "safety", "guard", "bounty", "compliance", "hipaa", "phi", "prompt", "x402", "trading", "defi", "keccak"],
    },
    {
        "id": "network-homelab",
        "name_zh": "网络 / Homelab",
        "description_zh": "网络诊断、Cisco、Netmiko、BGP、WireGuard、Pi-hole、VLAN 和接口健康。",
        "terms": ["network", "homelab", "cisco", "netmiko", "bgp", "wireguard", "pihole", "vlan", "interface"],
    },
    {
        "id": "industry-business",
        "name_zh": "行业业务场景",
        "description_zh": "医疗、财务、物流、贸易、能源、库存、投资、销售和业务运营。",
        "terms": ["healthcare", "finance", "billing", "logistics", "customs", "energy", "inventory", "investor", "lead", "carrier", "customer", "production", "quality-nonconformance", "returns", "visa", "trade", "procurement"],
    },
    {
        "id": "media-docs-science",
        "name_zh": "媒体 / 文档 / 科研",
        "description_zh": "视频、媒体生成、文档处理、科学数据库、文献和学术评估。",
        "terms": ["video", "media", "manim", "remotion", "videodb", "blender", "document", "nutrient", "scientific", "pubmed", "uspto", "literature", "scholar", "fal-ai", "slides", "exa", "search"],
    },
    {
        "id": "ecc-governance",
        "name_zh": "ECC 自身治理",
        "description_zh": "ECC 安装、配置、skill 生成、盘点、规则提炼、hookify 和能力治理。",
        "terms": ["ecc", "skill", "rules", "hookify", "configure-ecc", "agent-sort", "skill-create", "skill-health", "skill-scout", "skill-stocktake", "rules-distill", "update-codemaps", "hermes"],
    },
    {
        "id": "opensource-release",
        "name_zh": "开源 / 发布整理",
        "description_zh": "开源清理、fork、打包、发布和仓库对外整理。",
        "terms": ["opensource", "open-source", "fork", "packager", "sanitizer", "release"],
    },
    {
        "id": "web3-crypto",
        "name_zh": "Web3 / 加密",
        "description_zh": "DeFi、EVM、Keccak、x402、钱包和交易 agent 安全。",
        "terms": ["defi", "evm", "keccak", "x402", "trading", "wallet", "solidity"],
    },
]

CONFIG_FILENAME = "ecc-use.config.json"
APP_CONFIG_PATH = Path.home() / ".ecc-manager" / "config.json"
SUPPORTED_ECC_VERSIONS = {"2.0.0-rc.1"}
ENV_CONFIG_KEYS = {
    "ECC_HOME": "ecc_home",
    "PROFILE_HOME": "profile_home",
    "ECC_MANAGER_GENERATED_CLAUDE_FILE": "generated_claude_file",
    "ECC_MANAGER_GENERATED_CODEX_FILE": "generated_codex_file",
    "ECC_MANAGER_GENERATED_ANTIGRAVITY_FILE": "generated_antigravity_file",
}


@dataclass(frozen=True)
class Paths:
    ecc_home: Path
    profile_home: Path
    generated_claude_file: str
    generated_codex_file: str
    generated_antigravity_file: str


def expand_path(value: str | Path) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(str(value)))).resolve()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _normalize_config(config: dict[str, Any]) -> dict[str, Any]:
    config["ecc_home"] = str(expand_path(config["ecc_home"]))
    config["profile_home"] = str(expand_path(config["profile_home"]))
    config["enable_claude"] = _as_bool(config.get("enable_claude", DEFAULT_CONFIG.get("enable_claude", True)))
    config["enable_codex"] = _as_bool(config.get("enable_codex", DEFAULT_CONFIG.get("enable_codex", False)))
    config["enable_antigravity"] = _as_bool(config.get("enable_antigravity", DEFAULT_CONFIG.get("enable_antigravity", False)))
    config["manage_agents_md"] = _as_bool(config.get("manage_agents_md", True))
    if config["enable_codex"] or config["enable_antigravity"]:
        config["manage_agents_md"] = True
    return config


def _meaningful_config_items(config: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in config.items()
        if value is not None and value != ""
    }


def _env_config() -> dict[str, str]:
    return {
        config_key: value
        for env_key, config_key in ENV_CONFIG_KEYS.items()
        if (value := os.environ.get(env_key, "").strip())
    }


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "no", "off"}
    return bool(value)


def load_config(profile_home: str | Path | None = None) -> dict[str, Any]:
    app_config = read_json(APP_CONFIG_PATH, {}) or {}
    config = dict(DEFAULT_CONFIG)
    env_config = _env_config()
    config.update(_meaningful_config_items(app_config))
    config.update(env_config)
    if profile_home is not None:
        config["profile_home"] = str(profile_home)

    profile_dir = expand_path(config["profile_home"])
    config_path = profile_dir / CONFIG_FILENAME
    profile_config = read_json(config_path, {}) or {}
    config.update(profile_config)
    config.update(_meaningful_config_items(app_config))
    config.update(env_config)
    if profile_home is not None:
        config["profile_home"] = str(profile_home)
    return _normalize_config(config)


def save_config(updates: dict[str, Any]) -> dict[str, Any]:
    config = load_config()
    for key in ["ecc_home", "profile_home", "generated_claude_file", "generated_codex_file", "generated_antigravity_file"]:
        if key in updates:
            value = str(updates[key]).strip()
            if not value:
                raise ValueError(f"{key} 不能为空")
            config[key] = value
    for key in ["enable_claude", "enable_codex", "enable_antigravity", "manage_agents_md"]:
        if key in updates:
            config[key] = _as_bool(updates[key])

    config = _normalize_config(config)
    profile_dir = expand_path(config["profile_home"])
    write_json(profile_dir / CONFIG_FILENAME, config)
    write_json(APP_CONFIG_PATH, {
        "ecc_home": config["ecc_home"],
        "profile_home": config["profile_home"],
    })
    return config


def paths_from_config(config: dict[str, Any]) -> Paths:
    return Paths(
        ecc_home=expand_path(config["ecc_home"]),
        profile_home=expand_path(config["profile_home"]),
        generated_claude_file=config.get("generated_claude_file", "CLAUDE.ecc.generated.md"),
        generated_codex_file=config.get("generated_codex_file", CODEX_GENERATED_FILE_DEFAULT),
        generated_antigravity_file=config.get("generated_antigravity_file", ANTIGRAVITY_GENERATED_FILE_DEFAULT),
    )


def bootstrap_profiles(profile_home: str | Path | None = None, force: bool = False) -> dict[str, Any]:
    config = load_config()
    if profile_home is not None:
        config["profile_home"] = str(profile_home)
    config = _normalize_config(config)
    root = expand_path(config["profile_home"])
    created: list[str] = []

    config_path = root / CONFIG_FILENAME
    if force or not config_path.exists():
        write_json(config_path, config)
        created.append(str(config_path))

    groups = [
        ("phases", PHASES),
        ("architectures", ARCHITECTURES),
        ("project-types", PROJECT_TYPES),
        ("packs", PACKS),
    ]
    for dirname, profiles in groups:
        for profile_id, profile in profiles.items():
            target = root / dirname / f"{profile_id}.json"
            if force or not target.exists():
                write_json(target, profile)
                created.append(str(target))

    dep_path = root / "dependencies" / "commands.json"
    if force or not dep_path.exists():
        write_json(dep_path, COMMAND_DEPENDENCIES)
        created.append(str(dep_path))

    return {"ok": True, "profile_home": str(root), "created": created}


def default_profile_catalog() -> dict[str, dict[str, Any]]:
    return {
        "phases": deepcopy(PHASES),
        "architectures": deepcopy(ARCHITECTURES),
        "project-types": deepcopy(PROJECT_TYPES),
        "packs": deepcopy(PACKS),
    }


def _ensure_phase_plan_command(profile: dict[str, Any]) -> dict[str, Any]:
    if profile.get("type") != "phase":
        return profile
    required = profile.setdefault("required", {})
    commands = required.setdefault("commands", [])
    if isinstance(commands, list) and GLOBAL_PLAN_SOURCE_NAME not in commands:
        commands.insert(0, GLOBAL_PLAN_SOURCE_NAME)
    return profile


def load_profiles(profile_home: str | Path = DEFAULT_CONFIG["profile_home"]) -> dict[str, dict[str, Any]]:
    root = expand_path(profile_home)
    out = default_profile_catalog()
    for dirname in out:
        group_dir = root / dirname
        if not group_dir.exists():
            continue
        for path in sorted(group_dir.glob("*.json")):
            data = read_json(path, {})
            if isinstance(data, dict) and data.get("id"):
                target_dirname = "architectures" if dirname == "project-types" and data.get("preset_kind") == "architecture" else dirname
                if target_dirname == "architectures":
                    data = {**data, "type": "architecture"}
                if target_dirname == "phases":
                    data = _ensure_phase_plan_command(data)
                out.setdefault(target_dirname, {})
                out[target_dirname][data["id"]] = data
    for profile in out.get("phases", {}).values():
        _ensure_phase_plan_command(profile)
    return out


def load_command_dependencies(profile_home: str | Path = DEFAULT_CONFIG["profile_home"]) -> dict[str, Any]:
    root = expand_path(profile_home)
    data = read_json(root / "dependencies" / "commands.json", {})
    if isinstance(data, dict) and isinstance(data.get("commands"), dict):
        return data
    return COMMAND_DEPENDENCIES


def _command_registry_path(paths: Paths) -> Path:
    return paths.ecc_home / "docs" / "COMMAND-REGISTRY.json"


def _command_name_from_registry_entry(entry: dict[str, Any]) -> str:
    raw_path = str(entry.get("path") or "").strip()
    if raw_path:
        return Path(raw_path).name
    command = str(entry.get("command") or "").strip()
    if not command:
        return ""
    return command if command.endswith(".md") else f"{command}.md"


def _agent_filename(value: str) -> str:
    value = value.strip()
    return value if value.endswith(".md") else f"{value}.md"


def load_command_registry_dependencies(paths: Paths) -> dict[str, dict[str, Any]]:
    data = read_json(_command_registry_path(paths), {}) or {}
    commands = data.get("commands", []) if isinstance(data, dict) else []
    if not isinstance(commands, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for entry in commands:
        if not isinstance(entry, dict):
            continue
        command_name = _command_name_from_registry_entry(entry)
        if not command_name:
            continue
        skills = _as_list(entry.get("skills"))
        agents = [_agent_filename(item) for item in [*_as_list(entry.get("primaryAgents")), *_as_list(entry.get("allAgents"))]]
        agents = list(dict.fromkeys(item for item in agents if item != ".md"))
        out[command_name] = normalize_command_dependency({
            "mode": "registry",
            "required": {
                "commands": [],
                "skills": skills,
                "agents": agents,
                "rules": [],
                "runtime": [],
            },
            "optional": {},
        })
    return out


def _empty_dependency_lists(kinds: tuple[str, ...]) -> dict[str, list[str]]:
    return {kind: [] for kind in kinds}


def _empty_owner_map(kinds: tuple[str, ...]) -> dict[str, dict[str, list[str]]]:
    return {kind: {} for kind in kinds}


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def normalize_dependency_section(section: Any, kinds: tuple[str, ...]) -> dict[str, list[str]]:
    normalized = _empty_dependency_lists(kinds)
    if not isinstance(section, dict):
        return normalized
    for kind in kinds:
        normalized[kind] = _as_list(section.get(kind))
    return normalized


def normalize_command_dependency(dep: Any) -> dict[str, Any]:
    dep = dep if isinstance(dep, dict) else {}
    required_section = dep.get("requires", dep.get("required", {}))
    normalized = {
        "mode": dep.get("mode", "default"),
        "required": normalize_dependency_section(required_section, REQUIRED_DEPENDENCY_KINDS),
        "optional": normalize_dependency_section(dep.get("optional", {}), OPTIONAL_DEPENDENCY_KINDS),
    }
    return normalized


def normalize_command_dependencies(command_dependencies: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(command_dependencies, dict):
        command_dependencies = COMMAND_DEPENDENCIES
    commands = command_dependencies.get("commands", {})
    if not isinstance(commands, dict):
        return {}
    return {
        command_name: normalize_command_dependency(dep)
        for command_name, dep in commands.items()
        if isinstance(command_name, str)
    }


def _clean_yaml_scalar(value: str) -> str:
    value = value.strip()
    if "#" in value:
        value = value.split("#", 1)[0].strip()
    return value.strip().strip('"').strip("'")


def _parse_yaml_list(value: str) -> list[str]:
    value = value.strip()
    if not value or value in {"[]", "{}"}:
        return []
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_clean_yaml_scalar(item) for item in inner.split(",") if _clean_yaml_scalar(item)]
    cleaned = _clean_yaml_scalar(value)
    return [cleaned] if cleaned else []


def _split_top_level_csv(value: str) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    quote: str | None = None
    for index, char in enumerate(value):
        if quote:
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
            continue
        if char in "[{(":
            depth += 1
            continue
        if char in "]})":
            depth = max(0, depth - 1)
            continue
        if char == "," and depth == 0:
            parts.append(value[start:index].strip())
            start = index + 1
    tail = value[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def _parse_yaml_inline_map(value: str, kinds: tuple[str, ...]) -> dict[str, list[str]] | None:
    value = value.strip()
    if not (value.startswith("{") and value.endswith("}")):
        return None
    inner = value[1:-1].strip()
    parsed = _empty_dependency_lists(kinds)
    if not inner:
        return parsed
    for item in _split_top_level_csv(inner):
        key, separator, raw_values = item.partition(":")
        if not separator:
            continue
        kind = key.strip().strip('"').strip("'")
        if kind in parsed:
            parsed[kind] = _parse_yaml_list(raw_values)
    return parsed


def split_frontmatter(raw: str) -> tuple[bool, str, str]:
    lines = raw.splitlines()
    if not lines or lines[0].strip() != "---":
        return False, "", raw
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            frontmatter = "\n".join(lines[1:index])
            body = "\n".join(lines[index + 1:])
            if raw.endswith("\n"):
                body += "\n"
            return True, frontmatter, body
    return False, "", raw


def parse_command_frontmatter_dependency(raw: str) -> tuple[bool, dict[str, Any]]:
    has_frontmatter, frontmatter, _body = split_frontmatter(raw)
    if not has_frontmatter:
        return False, normalize_command_dependency({})

    sections: dict[str, dict[str, list[str]]] = {
        "required": _empty_dependency_lists(REQUIRED_DEPENDENCY_KINDS),
        "optional": _empty_dependency_lists(OPTIONAL_DEPENDENCY_KINDS),
    }
    found_contract = False
    active_section: str | None = None
    active_kind: str | None = None

    for line in frontmatter.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        top_level = not line.startswith((" ", "\t"))
        if top_level:
            key, separator, value = line.partition(":")
            if not separator:
                active_section = None
                active_kind = None
                continue
            key = key.strip()
            if key in {"requires", "required"}:
                found_contract = True
                active_section = "required"
                active_kind = None
                inline = _parse_yaml_inline_map(value, REQUIRED_DEPENDENCY_KINDS)
                if inline is not None:
                    sections["required"] = inline
                continue
            if key == "optional":
                found_contract = True
                active_section = "optional"
                active_kind = None
                inline = _parse_yaml_inline_map(value, OPTIONAL_DEPENDENCY_KINDS)
                if inline is not None:
                    sections["optional"] = inline
                continue
            active_section = None
            active_kind = None
            continue

        if active_section is None:
            continue

        stripped = line.strip()
        child_match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", stripped)
        if child_match:
            kind = child_match.group(1)
            value = child_match.group(2)
            allowed = REQUIRED_DEPENDENCY_KINDS if active_section == "required" else OPTIONAL_DEPENDENCY_KINDS
            if kind in allowed:
                active_kind = kind
                sections[active_section][kind] = _parse_yaml_list(value)
            else:
                active_kind = None
            continue

        if active_kind and stripped.startswith("- "):
            item = _clean_yaml_scalar(stripped[2:])
            if item and item not in sections[active_section][active_kind]:
                sections[active_section][active_kind].append(item)

    if not found_contract:
        return False, normalize_command_dependency({})
    return True, {"mode": "frontmatter", "required": sections["required"], "optional": sections["optional"]}


def _command_source_path(paths: Paths, command_name: str) -> Path:
    return paths.ecc_home / "commands" / command_name


def command_frontmatter_contract(paths: Paths, command_name: str) -> tuple[bool, dict[str, Any]]:
    path = _command_source_path(paths, command_name)
    if not path.exists() or not path.is_file():
        return False, normalize_command_dependency({})
    try:
        return parse_command_frontmatter_dependency(path.read_text(encoding="utf-8", errors="ignore"))
    except OSError:
        return False, normalize_command_dependency({})


def load_command_contracts(paths: Paths, profile_home: str | Path) -> dict[str, dict[str, Any]]:
    legacy = normalize_command_dependencies(load_command_dependencies(profile_home))
    registry = load_command_registry_dependencies(paths)
    command_names = set(_source_names(paths, "commands")) | set(legacy) | set(registry)
    contracts: dict[str, dict[str, Any]] = {}
    for command_name in sorted(command_names):
        declared, dependency = command_frontmatter_contract(paths, command_name)
        if declared:
            source = "frontmatter"
        elif command_name in legacy:
            source = "legacy"
            dependency = legacy[command_name]
        elif command_name in registry:
            source = "registry"
            dependency = registry[command_name]
        else:
            source = "none"
        contracts[command_name] = {
            "command": command_name,
            "declared": source != "none",
            "source": source,
            "dependency": normalize_command_dependency(dependency),
        }
    return contracts


def profile_label(group: str, profile: dict[str, Any]) -> str:
    prefix = {
        "phases": "阶段",
        "architectures": "技术架构",
        "project-types": "技术栈片段",
        "packs": "能力包",
    }.get(group, group)
    name = profile.get("name_zh") or profile.get("id") or "unknown"
    return f"{prefix}: {name}"


def _asset_text(paths: Paths, kind: str, name: str) -> str:
    source_dir, _target_dir = KIND_DIRS[kind]
    path = paths.ecc_home / source_dir / name
    candidates: list[Path] = []
    if path.is_file():
        candidates.append(path)
    elif path.is_dir():
        candidates.extend([
            path / "SKILL.md",
            path / "README.md",
        ])
        candidates.extend(sorted(path.glob("*.md")))

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            try:
                raw = candidate.read_text(encoding="utf-8", errors="ignore")
                return _asset_summary_text(raw)
            except OSError:
                return ""
    return ""


def _asset_raw_text(paths: Paths, kind: str, name: str) -> str:
    source_dir, _target_dir = KIND_DIRS[kind]
    path = paths.ecc_home / source_dir / name
    if path.is_file():
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return ""
    if path.is_dir():
        for candidate in [path / "SKILL.md", path / "README.md", *sorted(path.glob("*.md"))]:
            if candidate.exists() and candidate.is_file():
                try:
                    return candidate.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    return ""
    return ""


def _asset_summary_text(raw: str) -> str:
    lines = raw.splitlines()
    selected: list[str] = []
    body_start = 0
    if lines and lines[0].strip() == "---":
        for index, line in enumerate(lines[1:80], start=1):
            stripped = line.strip()
            if stripped == "---":
                body_start = index + 1
                break
            if stripped.startswith(("name:", "description:", "tools:", "model:")):
                selected.append(stripped)

    body_count = 0
    for line in lines[body_start:]:
        stripped = line.strip()
        if not stripped:
            continue
        if "Prompt Defense Baseline" in stripped:
            break
        if stripped.startswith("#") or body_count < 24:
            selected.append(stripped)
            body_count += 1
        if body_count >= 24:
            break
    return "\n".join(selected)[:4000]


def _search_tokens(value: str) -> set[str]:
    normalized = value.lower()
    for char in ["/", "\\", ".", "_", ":", "(", ")", "[", "]", "{", "}", ","]:
        normalized = normalized.replace(char, "-")
    return {part for part in normalized.split("-") if part}


def _term_matches(term: str, haystack: str, tokens: set[str]) -> bool:
    term = term.lower()
    if "-" in term or "+" in term or " " in term:
        return term in haystack
    if term in tokens:
        return True
    return len(term) >= 6 and term in haystack


def _asset_node_id(kind: str, name: str) -> str:
    return f"{kind}/{name}"


def _profile_node_id(group: str, profile_id: str) -> str:
    return f"profiles/{group}/{profile_id}"


def _category_node_id(category_id: str) -> str:
    return f"categories/{category_id}"


def _edge_type_for_kind(kind: str) -> str:
    return {
        "agents": "command_invokes_agent",
        "skills": "command_uses_skill",
        "rules": "command_uses_rule",
    }.get(kind, f"command_uses_{kind[:-1]}")


def _frontmatter_value(raw: str, key: str) -> str:
    lines = raw.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    prefix = f"{key}:"
    for line in lines[1:80]:
        stripped = line.strip()
        if stripped == "---":
            break
        if stripped.startswith(prefix):
            return stripped.removeprefix(prefix).strip().strip('"').strip("'")
    return ""


def _alias_pattern(alias: str) -> re.Pattern[str]:
    if "/" in alias or "." in alias:
        return re.compile(re.escape(alias), re.IGNORECASE)
    return re.compile(rf"(?<![\w-]){re.escape(alias)}(?![\w-])", re.IGNORECASE)


def _relation_strength(line: str, context: str, kind: str) -> tuple[str, float]:
    lower_line = line.lower()
    lower_context = context.lower()
    explicit_markers = {
        "agents": ["agent:", "agents:", "subagent_type", "agents/"],
        "skills": ["skill:", "skills:", "skills/"],
        "rules": ["rule:", "rules:", "rules/"],
    }.get(kind, [])
    strong_markers = {
        "agents": ["invokes the", "invoke the", "specialized review agents", "review agents", "agent"],
        "skills": ["uses the", "use the", "related", "skill"],
        "rules": ["rule"],
    }.get(kind, [])
    if any(marker in lower_line for marker in explicit_markers):
        return "explicit", 0.95
    if kind == "agents" and any(marker in lower_context for marker in ["specialized review agents", "run specialized review agents", "agent section"]):
        return "explicit", 0.95
    if kind == "skills" and "skill section" in lower_context:
        return "explicit", 0.95
    if kind == "rules" and "rule section" in lower_context:
        return "explicit", 0.95
    if any(marker in lower_context for marker in strong_markers):
        return "strong", 0.8
    return "mention", 0.45


def _source_names(paths: Paths, kind: str) -> list[str]:
    source_dir, _target_dir = KIND_DIRS[kind]
    root = paths.ecc_home / source_dir
    if not root.exists():
        return []
    return sorted(path.name for path in root.iterdir() if root.exists() and not path.name.startswith("."))


def _asset_status_lookup(groups: dict[str, dict[str, Any]]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for kind, group in groups.items():
        for item in group.get("items", []):
            statuses[_asset_node_id(kind, item["name"])] = item.get("status", "")
        for item in group.get("missing", []):
            statuses[_asset_node_id(kind, item["name"])] = item.get("status", "")
    return statuses


def _asset_category_lookup(groups: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    categories: dict[str, list[dict[str, str]]] = {}
    for kind, group in groups.items():
        for item in [*group.get("items", []), *group.get("missing", [])]:
            categories[_asset_node_id(kind, item["name"])] = item.get("categories", [])
    return categories


def _relation_index(paths: Paths) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {kind: [] for kind in ["agents", "skills", "rules"]}
    for name in _source_names(paths, "agents"):
        raw = _asset_raw_text(paths, "agents", name)
        stem = Path(name).stem
        aliases = {name, stem, f"agents/{name}", f"agent/{stem}"}
        frontmatter_name = _frontmatter_value(raw, "name")
        if frontmatter_name:
            aliases.add(frontmatter_name)
        index["agents"].append({
            "kind": "agents",
            "name": name,
            "id": _asset_node_id("agents", name),
            "aliases": sorted(aliases, key=len, reverse=True),
            "patterns": [(alias, _alias_pattern(alias)) for alias in sorted(aliases, key=len, reverse=True)],
        })
    for name in _source_names(paths, "skills"):
        raw = _asset_raw_text(paths, "skills", name)
        aliases = {name, f"skills/{name}", f"skills/{name}/", f"skill/{name}"}
        frontmatter_name = _frontmatter_value(raw, "name")
        if frontmatter_name:
            aliases.add(frontmatter_name)
        index["skills"].append({
            "kind": "skills",
            "name": name,
            "id": _asset_node_id("skills", name),
            "aliases": sorted(aliases, key=len, reverse=True),
            "patterns": [(alias, _alias_pattern(alias)) for alias in sorted(aliases, key=len, reverse=True)],
        })
    for name in _source_names(paths, "rules"):
        aliases = {f"rules/{name}", f"rules/ecc/{name}", f"rule/{name}"}
        index["rules"].append({
            "kind": "rules",
            "name": name,
            "id": _asset_node_id("rules", name),
            "aliases": sorted(aliases, key=len, reverse=True),
            "patterns": [(alias, _alias_pattern(alias)) for alias in sorted(aliases, key=len, reverse=True)],
        })
    return index


def _add_node(nodes: dict[str, dict[str, Any]], node: dict[str, Any]) -> None:
    existing = nodes.get(node["id"], {})
    merged = {**existing, **node}
    if existing.get("categories") or node.get("categories"):
        merged["categories"] = existing.get("categories") or node.get("categories") or []
    nodes[node["id"]] = merged


def _add_edge(edges: dict[tuple[str, str, str], dict[str, Any]], edge: dict[str, Any]) -> None:
    key = (edge["source"], edge["target"], edge["type"])
    existing = edges.get(key)
    if not existing or edge.get("confidence", 0) > existing.get("confidence", 0):
        edges[key] = edge


def _edge_categories(edge: dict[str, Any], nodes: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    target = nodes.get(edge["target"], {})
    return target.get("categories", []) if edge["type"].startswith("command_") else []


def _merge_command_relation_categories(nodes: dict[str, dict[str, Any]], edges: dict[tuple[str, str, str], dict[str, Any]]) -> None:
    by_command: dict[str, list[dict[str, str]]] = {}
    for edge in edges.values():
        if not edge["source"].startswith("commands/"):
            continue
        for category in _edge_categories(edge, nodes):
            bucket = by_command.setdefault(edge["source"], [])
            if category not in bucket:
                bucket.append(category)
    for command_id, categories in by_command.items():
        current = nodes.get(command_id, {}).get("categories", [])
        merged = list(current)
        for category in categories:
            if category not in merged:
                merged.append({
                    **category,
                    "reason": f"关联组件：{category.get('name_zh', category.get('id', ''))}",
                })
        if command_id in nodes:
            nodes[command_id]["categories"] = merged


def _scan_command_relations(
    paths: Paths,
    command_name: str,
    index: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    raw = _asset_raw_text(paths, "commands", command_name)
    if not raw:
        return []
    lines = raw.splitlines()
    found: dict[tuple[str, str], dict[str, Any]] = {}
    in_code_fence = False
    agent_context_until = 0
    skill_context_until = 0
    rule_context_until = 0
    for i, line in enumerate(lines, start=1):
        if line.strip().startswith("```"):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        lower_line = line.lower()
        if any(marker in lower_line for marker in ["agent:", "agents:", "review agents", "specialized review agents"]):
            agent_context_until = i + 12
        if any(marker in lower_line for marker in ["skill:", "skills:", "related skills"]):
            skill_context_until = i + 12
        if any(marker in lower_line for marker in ["rule:", "rules:", "related rules"]):
            rule_context_until = i + 12
        context_lines = lines[max(0, i - 4): min(len(lines), i + 2)]
        context = "\n".join(context_lines)
        if i <= agent_context_until:
            context += "\nagent section"
        if i <= skill_context_until:
            context += "\nskill section"
        if i <= rule_context_until:
            context += "\nrule section"
        for kind in ["agents", "skills", "rules"]:
            for target in index[kind]:
                for _alias, pattern in target["patterns"]:
                    if not pattern.search(line):
                        continue
                    relation_type, confidence = _relation_strength(line, context, kind)
                    key = (kind, target["name"])
                    edge = {
                        "source": _asset_node_id("commands", command_name),
                        "target": target["id"],
                        "type": _edge_type_for_kind(kind),
                        "relation_type": relation_type,
                        "confidence": confidence,
                        "evidence": line.strip()[:220],
                        "line_hint": i,
                    }
                    previous = found.get(key)
                    if not previous or confidence > previous["confidence"]:
                        found[key] = edge
                    break
    return list(found.values())


def classify_asset(kind: str, name: str, paths: Paths | None = None) -> list[dict[str, str]]:
    text = _asset_text(paths, kind, name) if paths else ""
    haystack = f"{kind} {name} {text}".lower()
    tokens = _search_tokens(f"{kind}-{name}") | _search_tokens(text[:2000])
    categories: list[dict[str, str]] = []
    for definition in ASSET_CATEGORY_DEFINITIONS:
        matched_terms = [
            term
            for term in definition["terms"]
            if _term_matches(term, haystack, tokens)
        ]
        if matched_terms:
            categories.append({
                "id": definition["id"],
                "name_zh": definition["name_zh"],
                "description_zh": definition["description_zh"],
                "reason": "匹配 " + "、".join(matched_terms[:3]),
            })
    return categories


def build_asset_classification(groups: dict[str, dict[str, Any]], relations: dict[str, Any] | None = None) -> dict[str, Any]:
    categories = {
        definition["id"]: {
            "id": definition["id"],
            "name_zh": definition["name_zh"],
            "description_zh": definition["description_zh"],
            "counts": {kind: 0 for kind in KIND_DIRS},
            "items": [],
        }
        for definition in ASSET_CATEGORY_DEFINITIONS
    }
    relation_categories = {
        node["id"]: node.get("categories", [])
        for node in (relations or {}).get("nodes", [])
        if node.get("categories")
    }
    uncategorized: list[dict[str, str]] = []
    for kind, group in groups.items():
        for item in group.get("items", []):
            if item.get("status") != "unassigned":
                continue
            summary = {
                "kind": kind,
                "name": item["name"],
                "status": item["status"],
            }
            item_categories = relation_categories.get(_asset_node_id(kind, item["name"]), item.get("categories", []))
            if not item_categories:
                uncategorized.append(summary)
                continue
            for category in item_categories:
                bucket = categories[category["id"]]
                bucket["items"].append({
                    **summary,
                    "reason": category["reason"],
                })
                bucket["counts"][kind] += 1

    out = [category for category in categories.values() if category["items"]]
    out.sort(key=lambda category: (-len(category["items"]), category["name_zh"]))
    return {
        "categories": out,
        "uncategorized": uncategorized,
    }


def build_asset_relations(
    paths: Paths,
    profiles: dict[str, dict[str, Any]],
    groups: dict[str, dict[str, Any]],
    command_contracts: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[tuple[str, str, str], dict[str, Any]] = {}
    statuses = _asset_status_lookup(groups)
    category_lookup = _asset_category_lookup(groups)

    for kind, group in groups.items():
        for item in [*group.get("items", []), *group.get("missing", [])]:
            node_id = _asset_node_id(kind, item["name"])
            _add_node(nodes, {
                "id": node_id,
                "kind": kind,
                "name": item["name"],
                "label": item["name"],
                "status": item.get("status"),
                "categories": item.get("categories", []),
            })

    for definition in ASSET_CATEGORY_DEFINITIONS:
        category_id = _category_node_id(definition["id"])
        _add_node(nodes, {
            "id": category_id,
            "kind": "categories",
            "name": definition["id"],
            "label": definition["name_zh"],
            "description_zh": definition["description_zh"],
        })

    relation_index = _relation_index(paths)
    command_relations: list[dict[str, Any]] = []
    for command_name in _source_names(paths, "commands"):
        command_id = _asset_node_id("commands", command_name)
        command_edges = _scan_command_relations(paths, command_name, relation_index)
        command_relations.extend(command_edges)
        for edge in command_edges:
            target = nodes.get(edge["target"])
            if not target:
                continue
            _add_edge(edges, edge | {
                "source_status": statuses.get(edge["source"]),
                "target_status": statuses.get(edge["target"]),
                "suggested_dependency": edge["relation_type"] in {"explicit", "strong"},
            })

    for group, items in profiles.items():
        for profile_id, profile in items.items():
            source = _profile_node_id(group, profile_id)
            _add_node(nodes, {
                "id": source,
                "kind": "profiles",
                "profile_group": group,
                "name": profile_id,
                "label": profile_label(group, profile),
            })
            required = merge_required([profile_id], profiles, command_contracts)["required"]
            for kind in KIND_DIRS:
                for name in required.get(kind, {}):
                    target = _asset_node_id(kind, name)
                    _add_node(nodes, {
                        "id": target,
                        "kind": kind,
                        "name": name,
                        "label": name,
                        "status": statuses.get(target, "missing_reference"),
                        "categories": category_lookup.get(target, []),
                    })
                    _add_edge(edges, {
                        "source": source,
                        "target": target,
                        "type": "profile_requires_asset",
                        "relation_type": "profile",
                        "confidence": 1.0,
                        "evidence": f"{profile_label(group, profile)} required {kind}/{name}",
                        "line_hint": None,
                        "source_status": "profile",
                        "target_status": statuses.get(target, "missing_reference"),
                        "suggested_dependency": False,
                    })

    _merge_command_relation_categories(nodes, edges)

    for node in list(nodes.values()):
        if node["kind"] not in KIND_DIRS:
            continue
        for category in node.get("categories", []):
            category_target = _category_node_id(category["id"])
            _add_edge(edges, {
                "source": node["id"],
                "target": category_target,
                "type": "asset_category_match",
                "relation_type": "mention",
                "confidence": 0.35,
                "evidence": category.get("reason", ""),
                "line_hint": None,
                "source_status": node.get("status"),
                "target_status": "category",
                "suggested_dependency": False,
            })

    command_summaries = []
    relation_types = ["command_invokes_agent", "command_uses_skill", "command_uses_rule"]
    for command_name in _source_names(paths, "commands"):
        command_id = _asset_node_id("commands", command_name)
        command_edges = [
            edge for edge in edges.values()
            if edge["source"] == command_id and edge["type"] in relation_types
        ]
        command_edges.sort(key=lambda edge: (-edge["confidence"], edge["target"]))
        command_summaries.append({
            "id": command_id,
            "name": command_name,
            "status": statuses.get(command_id, ""),
            "relations": command_edges,
            "relation_count": len(command_edges),
            "categories": nodes.get(command_id, {}).get("categories", []),
            "message": "" if command_edges else "未发现明确关联",
        })

    return {
        "nodes": sorted(nodes.values(), key=lambda node: node["id"]),
        "edges": sorted(edges.values(), key=lambda edge: (edge["source"], edge["type"], edge["target"])),
        "commands": command_summaries,
        "stats": {
            "commands": len(command_summaries),
            "commands_with_relations": sum(1 for item in command_summaries if item["relation_count"]),
            "suggested_edges": sum(1 for edge in edges.values() if edge.get("suggested_dependency")),
            "profile_edges": sum(1 for edge in edges.values() if edge["type"] == "profile_requires_asset"),
        },
    }


def ecc_version_metadata(paths: Paths) -> dict[str, Any]:
    version_path = paths.ecc_home / "VERSION"
    try:
        version = version_path.read_text(encoding="utf-8").strip() if version_path.exists() else ""
    except OSError:
        version = ""

    git_commit = ""
    git_branch = ""
    if paths.ecc_home.exists():
        commit_result = subprocess.run(
            ["git", "-C", str(paths.ecc_home), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if commit_result.returncode == 0:
            git_commit = commit_result.stdout.strip()
        branch_result = subprocess.run(
            ["git", "-C", str(paths.ecc_home), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if branch_result.returncode == 0:
            git_branch = branch_result.stdout.strip()

    return {
        "version": version,
        "git_commit": git_commit,
        "git_branch": git_branch,
        "fingerprint": git_commit or version or "unknown",
    }


def ecc_manifest_metadata(paths: Paths) -> dict[str, Any]:
    version = ecc_version_metadata(paths).get("version", "")
    manifest_specs = {
        "install_profiles": paths.ecc_home / "manifests" / "install-profiles.json",
        "install_modules": paths.ecc_home / "manifests" / "install-modules.json",
        "install_components": paths.ecc_home / "manifests" / "install-components.json",
        "project_stack_mappings": paths.ecc_home / "config" / "project-stack-mappings.json",
        "command_registry": _command_registry_path(paths),
    }
    manifests: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for name, path in manifest_specs.items():
        data = read_json(path, None)
        if data is None:
            manifests[name] = {"exists": False, "path": str(path)}
            missing.append(name)
            continue
        count = 0
        if name == "install_profiles" and isinstance(data, dict):
            count = len(data.get("profiles", {})) if isinstance(data.get("profiles"), dict) else 0
        elif name == "install_modules" and isinstance(data, dict):
            count = len(data.get("modules", [])) if isinstance(data.get("modules"), list) else 0
        elif name == "install_components" and isinstance(data, dict):
            count = len(data.get("components", [])) if isinstance(data.get("components"), list) else 0
        elif name == "project_stack_mappings" and isinstance(data, dict):
            count = len(data.get("stacks", [])) if isinstance(data.get("stacks"), list) else 0
        elif name == "command_registry" and isinstance(data, dict):
            count = len(data.get("commands", [])) if isinstance(data.get("commands"), list) else 0
        manifests[name] = {
            "exists": True,
            "path": str(path),
            "schema_version": data.get("schemaVersion", data.get("version")) if isinstance(data, dict) else None,
            "count": count,
        }

    if not paths.ecc_home.exists():
        status = "missing_ecc_home"
    elif version and version not in SUPPORTED_ECC_VERSIONS:
        status = "unsupported_version"
    elif missing:
        status = "missing_manifests"
    elif not version:
        status = "unknown_version"
    else:
        status = "supported"

    return {
        "status": status,
        "version": version,
        "supported_versions": sorted(SUPPORTED_ECC_VERSIONS),
        "manifests": manifests,
        "missing": missing,
        "message": {
            "supported": "ECC version and manifest set are supported.",
            "unsupported_version": "ECC version differs from this Manager's tested compatibility range; scan works, but profile coverage should be reviewed.",
            "missing_manifests": "ECC manifests are incomplete; falling back to source-folder scanning.",
            "unknown_version": "ECC VERSION file is missing; falling back to source-folder scanning.",
            "missing_ecc_home": "ECC_HOME does not exist.",
        }.get(status, status),
    }


def _profile_source_exists(paths: Paths, kind: str, name: str) -> bool:
    source_dir, _target_dir = KIND_DIRS[kind]
    return (paths.ecc_home / source_dir / name).exists()


def _declared_dependency_level(dep: dict[str, Any], kind: str, name: str) -> str:
    if name in dep.get("required", {}).get(kind, []):
        return "required"
    if name in dep.get("optional", {}).get(kind, []):
        return "optional"
    return ""


def _relation_dependency_kind(edge: dict[str, Any]) -> str:
    target = edge.get("target", "")
    kind, _separator, _name = target.partition("/")
    return kind


def _relation_dependency_name(edge: dict[str, Any]) -> str:
    _kind, _separator, name = edge.get("target", "").partition("/")
    return name


def _command_relation_candidates(
    command_name: str,
    relations: dict[str, Any],
    contract: dict[str, Any],
) -> list[dict[str, Any]]:
    dep = _contract_dependency(contract)
    relation_items = next(
        (item.get("relations", []) for item in relations.get("commands", []) if item.get("name") == command_name),
        [],
    )
    candidates: list[dict[str, Any]] = []
    for edge in relation_items:
        if not edge.get("suggested_dependency"):
            continue
        kind = _relation_dependency_kind(edge)
        name = _relation_dependency_name(edge)
        if kind not in {"skills", "agents", "rules"} or not name:
            continue
        if _declared_dependency_level(dep, kind, name):
            continue
        candidates.append({
            "kind": kind,
            "name": name,
            "relation_type": edge.get("relation_type"),
            "confidence": edge.get("confidence", 0),
            "evidence": edge.get("evidence", ""),
            "line_hint": edge.get("line_hint"),
            "suggested_level": "required" if edge.get("relation_type") == "explicit" else "optional",
        })
    return candidates


def build_command_contract_report(
    paths: Paths,
    command_contracts: dict[str, dict[str, Any]],
    relations: dict[str, Any],
) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for command_name in _source_names(paths, "commands"):
        contract = command_contracts.get(command_name, {
            "command": command_name,
            "declared": False,
            "source": "none",
            "dependency": normalize_command_dependency({}),
        })
        dep = _contract_dependency(contract)
        missing: list[dict[str, Any]] = []
        for level, kinds in [("required", REQUIRED_DEPENDENCY_KINDS), ("optional", OPTIONAL_DEPENDENCY_KINDS)]:
            for kind in kinds:
                for name in dep.get(level, {}).get(kind, []):
                    if kind in KIND_DIRS and not _profile_source_exists(paths, kind, name):
                        missing.append({"level": level, "kind": kind, "name": name, "reason": "source_missing"})
                    elif kind == "runtime":
                        runtime_status = _runtime_definition_status(paths.ecc_home, name)
                        if level == "required" and not runtime_status["source_exists"] and not runtime_status["target_exists"]:
                            missing.append({"level": level, "kind": kind, "name": name, "reason": "needs_confirmation"})
        candidates = _command_relation_candidates(command_name, relations, contract)
        if not contract.get("declared"):
            health = "unknown"
            status = "missing_contract"
        elif any(item["level"] == "required" for item in missing):
            health = "blocked"
            status = "contract_references_missing_required"
        elif missing:
            health = "degraded"
            status = "contract_references_missing_optional"
        else:
            health = "ready"
            status = "declared"
        reports.append({
            "command": command_name,
            "status": status,
            "declared": {
                "source": contract.get("source", "none"),
                "has_contract": bool(contract.get("declared")),
                "requires": dep.get("required", {}),
                "optional": dep.get("optional", {}),
            },
            "candidates": candidates,
            "missing": missing,
            "health": health,
            "label": COMMAND_HEALTH_LABELS.get(health, health),
        })
    return reports


def _suggestion_targets_for_asset(item: dict[str, Any]) -> list[dict[str, Any]]:
    name = item.get("name", "")
    kind = item.get("kind", "")
    category_ids = {category.get("id") for category in item.get("categories", [])}
    lower = f"{kind} {name}".lower()
    suggestions: list[dict[str, Any]] = []

    global_core_names = {"common", "planner.md", "code-explorer.md", "coding-standards", "codebase-onboarding"}
    if name in global_core_names:
        suggestions.append({
            "target_type": "global-core",
            "target_id": "common-foundation",
            "reason": "看起来是所有项目都可能需要的基础能力",
            "confidence": 0.82,
        })

    if "quality-review-testing" in category_ids:
        target_id = "test-coverage-pack" if "test" in lower else "code-review-pack"
        suggestions.append({
            "target_type": "pack",
            "target_id": target_id,
            "reason": "匹配质量、审查或测试能力，可进入横向能力包",
            "confidence": 0.72,
        })
        suggestions.append({
            "target_type": "phase",
            "target_id": "ph-qa",
            "reason": "质量检查通常属于后期 QA 阶段",
            "confidence": 0.62,
        })
    if "security-safety" in category_ids:
        suggestions.append({
            "target_type": "pack",
            "target_id": "security-audit-pack",
            "reason": "匹配安全审查能力，可进入安全能力包",
            "confidence": 0.74,
        })
        suggestions.append({
            "target_type": "phase",
            "target_id": "ph-launch",
            "reason": "安全检查常用于上线前治理",
            "confidence": 0.64,
        })
    if "planning-prp" in category_ids:
        suggestions.append({
            "target_type": "phase",
            "target_id": "ph-init",
            "reason": "规划、PRP 和产品判断通常属于项目初期",
            "confidence": 0.7,
        })
    if "frontend-ui" in category_ids:
        suggestions.append({
            "target_type": "project-type",
            "target_id": "web-react-frontend",
            "reason": "匹配前端、UI 或浏览器体验能力",
            "confidence": 0.68,
        })
    if "backend-api-data" in category_ids:
        target_id = "api-python-fastapi" if any(term in lower for term in ["python", "fastapi"]) else "api-node-backend"
        suggestions.append({
            "target_type": "project-type",
            "target_id": target_id,
            "reason": "匹配后端、API 或数据能力",
            "confidence": 0.66,
        })
    if "ai-agent-orchestration" in category_ids:
        suggestions.append({
            "target_type": "architecture",
            "target_id": "arch-ai-agent-fastapi-web",
            "reason": "匹配 AI Agent、编排或评测能力",
            "confidence": 0.7,
        })
    if "devops-runtime-ops" in category_ids:
        suggestions.append({
            "target_type": "project-type",
            "target_id": "infra-docker-devops",
            "reason": "匹配 DevOps、部署或运行时能力",
            "confidence": 0.64,
        })
    if not suggestions:
        suggestions.append({
            "target_type": "hold",
            "target_id": "manual-review",
            "reason": "用途还不够稳定，建议暂不收编，先人工确认",
            "confidence": 0.35,
        })
    return suggestions


def build_asset_suggestions(
    groups: dict[str, dict[str, Any]],
    relations: dict[str, Any],
    command_contracts: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    suggestions: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str, str]] = set()

    def add(item: dict[str, Any]) -> None:
        key = (
            item.get("action", ""),
            item.get("kind", ""),
            item.get("name", ""),
            item.get("target_type", ""),
            item.get("target_id", ""),
        )
        if key in seen:
            return
        seen.add(key)
        suggestions.append(item)

    for kind, group in groups.items():
        for item in group.get("items", []):
            if item.get("status") != "unassigned":
                continue
            enriched = {"kind": kind, **item}
            for target in _suggestion_targets_for_asset(enriched):
                action = "hold" if target["target_type"] == "hold" else "add_to_profile_required"
                add({
                    "kind": kind,
                    "name": item["name"],
                    "target_type": target["target_type"],
                    "target_id": target["target_id"],
                    "action": action,
                    "reason": target["reason"],
                    "confidence": target["confidence"],
                })

    for command in relations.get("commands", []):
        contract = command_contracts.get(command.get("name", ""), {})
        for candidate in _command_relation_candidates(command.get("name", ""), relations, contract):
            add({
                "kind": candidate["kind"],
                "name": candidate["name"],
                "target_type": "command-dependency",
                "target_id": command.get("name", ""),
                "action": "confirm_command_dependency",
                "reason": f"命令正文提到该组件：{candidate.get('evidence', '')}",
                "confidence": candidate.get("confidence", 0),
                "dependency_kind": candidate["kind"],
                "dependency_name": candidate["name"],
                "suggested_level": candidate.get("suggested_level", "optional"),
                "relation_type": candidate.get("relation_type"),
            })

    suggestions.sort(key=lambda item: (-float(item.get("confidence", 0)), item.get("target_type", ""), item.get("name", "")))
    return suggestions


def build_profile_health(
    paths: Paths,
    profiles: dict[str, dict[str, Any]],
    command_contracts: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group, items in profiles.items():
        for profile_id, profile in sorted(items.items()):
            missing: list[dict[str, Any]] = []
            required = merge_required([profile_id], profiles, command_contracts)["required"]
            for kind in KIND_DIRS:
                for name in required.get(kind, {}):
                    if not _profile_source_exists(paths, kind, name):
                        missing.append({"kind": kind, "name": name, "component": f"{kind}/{name}"})
            rows.append({
                "profile_id": profile_id,
                "profile_name": profile.get("name_zh") or profile_id,
                "group": group,
                "missing": missing,
                "stale": [],
                "suggestions": [
                    {
                        "action": "remove_or_replace_missing_reference",
                        "component": item["component"],
                        "reason": "profile 引用了 ECC_HOME 中不存在的资产",
                    }
                    for item in missing
                ],
                "status": "missing_references" if missing else "ok",
            })
    return rows


def asset_inventory(config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_config()
    paths = paths_from_config(config)
    profiles = load_profiles(paths.profile_home)
    command_contracts = load_command_contracts(paths, paths.profile_home)
    usage: dict[str, dict[str, list[dict[str, str]]]] = {kind: {} for kind in KIND_DIRS}
    missing_references: list[dict[str, str]] = []

    for group, items in profiles.items():
        for profile_id, profile in items.items():
            owner = {
                "group": group,
                "profile_id": profile_id,
                "profile_name": profile.get("name_zh") or profile_id,
                "label": profile_label(group, profile),
            }
            required = merge_required([profile_id], profiles, command_contracts)["required"]
            for kind in KIND_DIRS:
                for name in required.get(kind, {}):
                    usage[kind].setdefault(name, [])
                    if owner not in usage[kind][name]:
                        usage[kind][name].append(owner)

    groups: dict[str, dict[str, Any]] = {}
    totals = {"source": 0, "covered": 0, "unassigned": 0, "missing_references": 0}
    for kind, (source_dir, _target_dir) in KIND_DIRS.items():
        root = paths.ecc_home / source_dir
        source_names = sorted(
            path.name
            for path in root.iterdir()
            if root.exists() and not path.name.startswith(".")
        ) if root.exists() else []
        source_set = set(source_names)
        used_names = set(usage[kind])
        covered = sorted(source_set & used_names)
        unassigned = sorted(source_set - used_names)
        missing = sorted(used_names - source_set)
        for name in missing:
            for owner in usage[kind][name]:
                missing_references.append({
                    "kind": kind,
                    "name": name,
                    "owner": owner["label"],
                    "profile_id": owner["profile_id"],
                })
        groups[kind] = {
            "source_dir": str(root),
            "total": len(source_names),
            "covered": len(covered),
            "unassigned": len(unassigned),
            "missing_references": len(missing),
            "items": [
                {"name": name, "status": "covered", "owners": usage[kind].get(name, []), "categories": classify_asset(kind, name, paths)}
                for name in covered
            ] + [
                {"name": name, "status": "unassigned", "owners": [], "categories": classify_asset(kind, name, paths)}
                for name in unassigned
            ],
            "missing": [
                {"name": name, "status": "missing_reference", "owners": usage[kind].get(name, []), "categories": classify_asset(kind, name)}
                for name in missing
            ],
        }
        totals["source"] += len(source_names)
        totals["covered"] += len(covered)
        totals["unassigned"] += len(unassigned)
        totals["missing_references"] += len(missing)

    relations = build_asset_relations(paths, profiles, groups, command_contracts)
    command_contract_report = build_command_contract_report(paths, command_contracts, relations)
    suggestions = build_asset_suggestions(groups, relations, command_contracts)
    sync = {
        "ecc_home": str(paths.ecc_home),
        "profile_home": str(paths.profile_home),
        **ecc_version_metadata(paths),
        "compatibility": ecc_manifest_metadata(paths),
        "totals": totals,
        "command_contracts": {
            "total": len(command_contract_report),
            "declared": sum(1 for item in command_contract_report if item["declared"]["has_contract"]),
            "unknown": sum(1 for item in command_contract_report if item["health"] == "unknown"),
            "candidates": sum(len(item.get("candidates", [])) for item in command_contract_report),
        },
    }
    return {
        "config": config,
        "ecc_home": str(paths.ecc_home),
        "profile_home": str(paths.profile_home),
        "sync": sync,
        "suggestions": suggestions,
        "command_contracts": command_contract_report,
        "profile_health": build_profile_health(paths, profiles, command_contracts),
        "totals": totals,
        "groups": groups,
        "classification": build_asset_classification(groups, relations),
        "relations": relations,
        "missing_references": missing_references,
    }


def ecc_scan(config: dict[str, Any] | None = None) -> dict[str, Any]:
    return asset_inventory(config)


def _dependency_section_has_items(section: dict[str, list[str]]) -> bool:
    return any(section.get(kind) for kind in section)


def _format_dependency_section(title: str, section: dict[str, list[str]], kinds: tuple[str, ...]) -> list[str]:
    lines = [f"{title}:"]
    for kind in kinds:
        values = section.get(kind, [])
        if values:
            lines.append(f"  {kind}:")
            lines.extend(f"    - {value}" for value in values)
        else:
            lines.append(f"  {kind}: []")
    return lines


def _frontmatter_without_contract(frontmatter: str) -> str:
    lines = frontmatter.splitlines()
    kept: list[str] = []
    skipping = False
    for line in lines:
        top_level = bool(line.strip()) and not line.startswith((" ", "\t"))
        if top_level:
            key = line.partition(":")[0].strip()
            skipping = key in {"requires", "required", "optional"}
        if not skipping:
            kept.append(line)
    while kept and not kept[-1].strip():
        kept.pop()
    return "\n".join(kept)


def _render_frontmatter_with_contract(raw: str, dependency: dict[str, Any]) -> str:
    has_frontmatter, frontmatter, body = split_frontmatter(raw)
    base = _frontmatter_without_contract(frontmatter) if has_frontmatter else ""
    dep = normalize_command_dependency(dependency)
    sections = [
        *_format_dependency_section("requires", dep["required"], REQUIRED_DEPENDENCY_KINDS),
        *_format_dependency_section("optional", dep["optional"], OPTIONAL_DEPENDENCY_KINDS),
    ]
    frontmatter_lines = [line for line in [base, "\n".join(sections)] if line.strip()]
    new_frontmatter = "\n".join(frontmatter_lines)
    body_text = body if has_frontmatter else raw
    if body_text and not body_text.startswith("\n"):
        return f"---\n{new_frontmatter}\n---\n{body_text}"
    return f"---\n{new_frontmatter}\n---\n{body_text}"


def write_command_contract_dependency(
    paths: Paths,
    command_name: str,
    level: str,
    kind: str,
    name: str,
) -> dict[str, Any]:
    if level not in {"required", "optional", "requires"}:
        return {"ok": False, "error": f"unsupported dependency level: {level}"}
    normalized_level = "required" if level == "requires" else level
    allowed = REQUIRED_DEPENDENCY_KINDS if normalized_level == "required" else OPTIONAL_DEPENDENCY_KINDS
    if kind not in allowed:
        return {"ok": False, "error": f"unsupported dependency kind for {normalized_level}: {kind}"}
    path = _command_source_path(paths, command_name)
    if not path.exists() or not path.is_file():
        return {"ok": False, "error": f"command source missing: {path}"}
    raw = path.read_text(encoding="utf-8", errors="ignore")
    declared, dependency = parse_command_frontmatter_dependency(raw)
    if not declared:
        dependency = normalize_command_dependency({})
    if name not in dependency[normalized_level][kind]:
        dependency[normalized_level][kind].append(name)
    if normalized_level == "required" and kind in dependency["optional"] and name in dependency["optional"][kind]:
        dependency["optional"][kind].remove(name)
    if normalized_level == "optional" and kind in dependency["required"] and name in dependency["required"][kind]:
        dependency["required"][kind].remove(name)
    path.write_text(_render_frontmatter_with_contract(raw, dependency), encoding="utf-8")
    return {
        "ok": True,
        "command": command_name,
        "level": normalized_level,
        "kind": kind,
        "name": name,
        "path": str(path),
    }


def _profile_group_from_target_type(target_type: str) -> str | None:
    return {
        "phase": "phases",
        "architecture": "architectures",
        "project-type": "project-types",
        "pack": "packs",
    }.get(target_type)


def apply_ecc_suggestions(
    suggestions: list[dict[str, Any]],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or load_config()
    paths = paths_from_config(config)
    profiles = load_profiles(paths.profile_home)
    applied: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for suggestion in suggestions:
        action = suggestion.get("action")
        if action == "add_to_profile_required":
            group = _profile_group_from_target_type(suggestion.get("target_type", ""))
            profile_id = suggestion.get("target_id")
            kind = suggestion.get("kind")
            name = suggestion.get("name")
            if not group or not profile_id or kind not in KIND_DIRS or not name:
                skipped.append(suggestion | {"reason": "suggestion 不完整"})
                continue
            profile = deepcopy(profiles.get(group, {}).get(profile_id))
            if not profile:
                skipped.append(suggestion | {"reason": "目标 profile 不存在"})
                continue
            required = profile.setdefault("required", {})
            required.setdefault(kind, [])
            if name not in required[kind]:
                required[kind].append(name)
            write_json(paths.profile_home / group / f"{profile_id}.json", profile)
            applied.append(suggestion | {"path": str(paths.profile_home / group / f"{profile_id}.json")})
            continue

        if action == "confirm_command_dependency":
            command_name = suggestion.get("target_id") or suggestion.get("command")
            level = suggestion.get("level") or suggestion.get("selected_level") or suggestion.get("suggested_level") or "optional"
            kind = suggestion.get("dependency_kind") or suggestion.get("kind")
            name = suggestion.get("dependency_name") or suggestion.get("name")
            result = write_command_contract_dependency(paths, command_name, level, kind, name)
            if result.get("ok"):
                applied.append(suggestion | result)
            else:
                skipped.append(suggestion | {"reason": result.get("error", "写入失败")})
            continue

        skipped.append(suggestion | {"reason": "未应用或暂不支持的建议类型"})

    return {"ok": True, "applied": applied, "skipped": skipped}


def profile_group(profile_id: str, profiles: dict[str, dict[str, Any]]) -> str | None:
    for group, items in profiles.items():
        if profile_id in items:
            return group
    return None


def get_profile(profile_id: str, profiles: dict[str, dict[str, Any]]) -> dict[str, Any]:
    group = profile_group(profile_id, profiles)
    if not group:
        raise ValueError(f"Unknown profile id: {profile_id}")
    return profiles[group][profile_id]


def normalize_project(path: str | Path | None) -> Path:
    return expand_path(path or Path.cwd())


def lock_path(project: Path) -> Path:
    return project / ".ecc-manager" / "ecc-lock" / "profile.json"


def legacy_lock_path(project: Path) -> Path:
    return project / ".claude" / "ecc-lock" / "profile.json"


def read_lock(project: Path) -> dict[str, Any]:
    return read_json(lock_path(project), {}) or read_json(legacy_lock_path(project), {}) or {}


def lock_target_path(project: Path, target_value: str | None) -> Path:
    target = Path(target_value or "")
    return target if target.is_absolute() else project / target


def default_lock(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "ecc_home": config["ecc_home"],
        "profile_home": config["profile_home"],
        "link_mode": "symlink",
        "overwrite_policy": "skip",
        "generated_claude_file": config.get("generated_claude_file", "CLAUDE.ecc.generated.md"),
        "generated_codex_file": config.get("generated_codex_file", CODEX_GENERATED_FILE_DEFAULT),
        "generated_antigravity_file": config.get("generated_antigravity_file", ANTIGRAVITY_GENERATED_FILE_DEFAULT),
        "enable_claude": _as_bool(config.get("enable_claude", True)),
        "enable_codex": _as_bool(config.get("enable_codex", True)),
        "enable_antigravity": _as_bool(config.get("enable_antigravity", True)),
        "manage_agents_md": _as_bool(config.get("manage_agents_md", True)),
        "initial_phase": None,
        "added_phases": [],
        "architecture": None,
        "project_types": [],
        "packs": [],
        "components": {},
        "codex_components": {},
        "antigravity_components": {},
        "skipped_existing": [],
        "task_history": [],
        "last_task_run": None,
    }


def classify_ids(ids: list[str], profiles: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    groups = {"phases": [], "architectures": [], "project-types": [], "packs": []}
    for profile_id in ids:
        group = profile_group(profile_id, profiles)
        if not group:
            raise ValueError(f"Unknown profile id: {profile_id}")
        groups[group].append(profile_id)
    return groups


def validate_profile_selection(profile_ids: list[str], profiles: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    groups = classify_ids(profile_ids, profiles)
    architecture_ids = list(dict.fromkeys(groups["architectures"]))
    if len(architecture_ids) > 1:
        raise ValueError(f"Only one architecture can be selected: {', '.join(architecture_ids)}")
    return groups


def profile_include_ids(profile: dict[str, Any]) -> list[str]:
    includes = profile.get("includes", {})
    if isinstance(includes, list):
        return [item for item in includes if isinstance(item, str)]
    if not isinstance(includes, dict):
        return []
    out: list[str] = []
    for value in includes.values():
        for item in _as_list(value):
            if item not in out:
                out.append(item)
    return out


def merge_required(
    profile_ids: list[str],
    profiles: dict[str, dict[str, Any]],
    command_contracts: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, list[str]]]:
    required = _empty_owner_map(REQUIRED_DEPENDENCY_KINDS)
    optional = _empty_owner_map(OPTIONAL_DEPENDENCY_KINDS)

    def add(target: dict[str, list[str]], name: str, owner: str) -> None:
        target.setdefault(name, [])
        if owner not in target[name]:
            target[name].append(owner)

    def merge_profile(profile_id: str, owner: str, stack: list[str]) -> None:
        if profile_id in stack:
            raise ValueError(f"Profile include cycle: {' -> '.join([*stack, profile_id])}")
        profile = get_profile(profile_id, profiles)
        for include_id in profile_include_ids(profile):
            if not profile_group(include_id, profiles):
                raise ValueError(f"Unknown included profile id: {include_id}")
            merge_profile(include_id, owner, [*stack, profile_id])
        for kind in REQUIRED_DEPENDENCY_KINDS:
            for item in profile.get("required", {}).get(kind, []):
                add(required[kind], item, owner)
        for kind in OPTIONAL_DEPENDENCY_KINDS:
            for item in profile.get("optional", {}).get(kind, []):
                add(optional[kind], item, owner)

    for profile_id in profile_ids:
        merge_profile(profile_id, profile_id, [])

    if command_contracts:
        seed_commands = list(required["commands"].items())
        for command_name, owners in seed_commands:
            closure = command_dependency_closure(command_name, command_contracts)
            for owner in owners:
                dependency_owner = f"{owner} via {command_name}"
                for kind in REQUIRED_DEPENDENCY_KINDS:
                    for item in closure["required"].get(kind, []):
                        if kind == "commands" and item == command_name:
                            continue
                        add(required[kind], item, dependency_owner)
                for kind in OPTIONAL_DEPENDENCY_KINDS:
                    for item in closure["optional"].get(kind, []):
                        add(optional[kind], item, dependency_owner)
    for kind in REQUIRED_DEPENDENCY_KINDS:
        for item in list(optional.get(kind, {})):
            if item in required.get(kind, {}):
                optional[kind].pop(item, None)
    return {"required": required, "optional": optional}


def promote_optional_dependencies(merged: dict[str, dict[str, dict[str, list[str]]]]) -> dict[str, dict[str, dict[str, list[str]]]]:
    promoted = deepcopy(merged)
    for kind in REQUIRED_DEPENDENCY_KINDS:
        for name, owners in list(promoted["optional"].get(kind, {}).items()):
            target_owners = promoted["required"].setdefault(kind, {}).setdefault(name, [])
            for owner in owners:
                optional_owner = f"{owner} optional"
                if optional_owner not in target_owners:
                    target_owners.append(optional_owner)
            promoted["optional"].get(kind, {}).pop(name, None)
    return promoted


def runtime_plan(ecc_home: Path, runtime_required: dict[str, list[str]]) -> dict[str, list[dict[str, Any]]]:
    create: list[dict[str, Any]] = []
    existing_ok: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    external_required: list[dict[str, Any]] = []

    for name, owners in runtime_required.items():
        definition = RUNTIME_DEFINITIONS.get(name, {})
        source_candidates = [ecc_home / item for item in definition.get("source_candidates", [])]
        existing_sources = [source for source in source_candidates if source.exists()]
        targets = [expand_path(item) for item in definition.get("global_targets", [])]
        target_statuses = [
            {"path": str(target), "exists": target.exists() or target.is_symlink()}
            for target in targets
        ]
        base = {
            "kind": "runtime",
            "component": f"runtime/{name}",
            "name": name,
            "required_by": owners,
            "description_zh": definition.get("description_zh", ""),
            "targets": target_statuses,
            "external_install": definition.get("external_install", []),
        }
        if existing_sources:
            source = existing_sources[0]
            target = targets[0] if targets else Path.home() / ".claude" / "runtime" / name
            status = symlink_status(target, source)
            item = base | {"source": str(source), "target": str(target), "status": status}
            if status == "missing":
                create.append(item | {"status": "create_symlink"})
            elif status == "linked":
                existing_ok.append(item | {"status": "already_linked"})
            else:
                skipped.append(item)
        else:
            external_required.append(base | {"status": "external_confirmation_required"})
            if not targets or not all(item["exists"] for item in target_statuses):
                missing.append(base | {"status": "missing_runtime_files"})
    return {
        "create": create,
        "existing_ok": existing_ok,
        "skipped": skipped,
        "missing": missing,
        "external_required": external_required,
    }


def _add_dependency_name(target: dict[str, list[str]], kind: str, name: str) -> None:
    if name not in target[kind]:
        target[kind].append(name)


def _contract_dependency(contract: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(contract, dict):
        return normalize_command_dependency({})
    if "dependency" in contract:
        return normalize_command_dependency(contract.get("dependency"))
    return normalize_command_dependency(contract)


def command_dependency_closure(command_name: str, command_contracts: dict[str, dict[str, Any]]) -> dict[str, dict[str, list[str]]]:
    required = _empty_dependency_lists(REQUIRED_DEPENDENCY_KINDS)
    optional = _empty_dependency_lists(OPTIONAL_DEPENDENCY_KINDS)
    queue = [command_name]
    seen: set[str] = set()
    while queue:
        current = queue.pop(0)
        if current in seen:
            continue
        seen.add(current)
        _add_dependency_name(required, "commands", current)
        dep = _contract_dependency(command_contracts.get(current))
        for kind in REQUIRED_DEPENDENCY_KINDS:
            for item in dep.get("required", {}).get(kind, []):
                _add_dependency_name(required, kind, item)
                if kind == "commands" and item not in seen:
                    queue.append(item)
        for kind in OPTIONAL_DEPENDENCY_KINDS:
            for item in dep.get("optional", {}).get(kind, []):
                _add_dependency_name(optional, kind, item)
    return {"required": required, "optional": optional}


def _local_dependency_record(
    paths: Paths,
    project: Path,
    kind: str,
    name: str,
    merged_required: dict[str, dict[str, list[str]]],
) -> dict[str, Any]:
    source, target, component = component_paths(paths.ecc_home, project, kind, name)
    source_exists = source.exists()
    is_required = name in merged_required.get(kind, {})
    target_status = symlink_status(target, source) if source_exists else "missing_source"
    enabled = is_required or target_status == "linked"
    status = target_status
    if not source_exists:
        status = "missing_source"
    elif not enabled:
        status = "not_enabled"
    elif is_required and target_status == "missing":
        status = "will_enable"
    return {
        "kind": kind,
        "name": name,
        "component": component,
        "source": str(source),
        "target": str(target),
        "status": status,
        "enabled": enabled,
        "source_exists": source_exists,
        "required": is_required,
    }


def _runtime_definition_status(ecc_home: Path, name: str) -> dict[str, Any]:
    definition = RUNTIME_DEFINITIONS.get(name, {})
    sources = [ecc_home / item for item in definition.get("source_candidates", [])]
    targets = [expand_path(item) for item in definition.get("global_targets", [])]
    return {
        "kind": "runtime",
        "name": name,
        "description_zh": definition.get("description_zh", ""),
        "source_exists": any(source.exists() for source in sources),
        "target_exists": bool(targets) and all(target.exists() or target.is_symlink() for target in targets),
        "targets": [{"path": str(target), "exists": target.exists() or target.is_symlink()} for target in targets],
        "external_install": definition.get("external_install", []),
    }


def _runtime_required_record(
    paths: Paths,
    name: str,
    runtime: dict[str, list[dict[str, Any]]],
    merged_required: dict[str, dict[str, list[str]]],
) -> dict[str, Any]:
    external_names = {item.get("name") for item in runtime.get("external_required", [])}
    missing_names = {item.get("name") for item in runtime.get("missing", [])}
    base = _runtime_definition_status(paths.ecc_home, name)
    enabled = name in merged_required.get("runtime", {}) and name not in external_names and name not in missing_names
    enabled = enabled or base["target_exists"]
    needs_confirmation = not enabled
    return base | {
        "status": "needs_confirmation" if needs_confirmation else "enabled",
        "enabled": enabled,
        "required": True,
        "needs_confirmation": needs_confirmation,
    }


def _runtime_optional_record(
    paths: Paths,
    name: str,
    merged_required: dict[str, dict[str, list[str]]],
) -> dict[str, Any]:
    base = _runtime_definition_status(paths.ecc_home, name)
    enabled = name in merged_required.get("runtime", {}) or base["target_exists"]
    return base | {
        "status": "enabled" if enabled else "not_enabled",
        "enabled": enabled,
        "required": False,
        "needs_confirmation": False,
    }


def _optional_integration_record(kind: str, name: str) -> dict[str, Any]:
    return {
        "kind": kind,
        "name": name,
        "component": f"{kind}/{name}",
        "status": "pending_confirmation",
        "enabled": False,
        "required": False,
    }


def build_command_health(
    paths: Paths,
    project: Path,
    merged: dict[str, dict[str, dict[str, list[str]]]],
    command_contracts: dict[str, dict[str, Any]],
    runtime: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    required = merged["required"]
    command_rows: list[dict[str, Any]] = []
    stats = {status: 0 for status in COMMAND_HEALTH_LABELS}

    for command_name, owners in sorted(required.get("commands", {}).items()):
        contract = command_contracts.get(command_name, {
            "command": command_name,
            "declared": False,
            "source": "none",
            "dependency": normalize_command_dependency({}),
        })
        if not contract.get("declared"):
            status = "unknown"
            stats[status] += 1
            command_rows.append({
                "name": command_name,
                "status": status,
                "label": COMMAND_HEALTH_LABELS[status],
                "summary": "没有机器可读 requires / optional 依赖契约",
                "required_by": owners,
                "contract_source": "none",
                "declared": False,
                "required": [],
                "required_missing": [],
                "runtime_pending": [],
                "optional_pending": [],
            })
            continue

        closure = command_dependency_closure(command_name, command_contracts)
        required_records: list[dict[str, Any]] = []
        required_missing: list[dict[str, Any]] = []
        runtime_pending: list[dict[str, Any]] = []
        optional_pending: list[dict[str, Any]] = []

        for kind in LOCAL_DEPENDENCY_KINDS:
            for name in closure["required"][kind]:
                record = _local_dependency_record(paths, project, kind, name, required)
                required_records.append(record)
                if not record["source_exists"] or not record["enabled"]:
                    required_missing.append(record)

        for name in closure["required"]["runtime"]:
            record = _runtime_required_record(paths, name, runtime, required)
            required_records.append(record)
            if record["needs_confirmation"]:
                runtime_pending.append(record)

        for kind in LOCAL_DEPENDENCY_KINDS:
            for name in closure["optional"][kind]:
                record = _local_dependency_record(paths, project, kind, name, required)
                if not record["enabled"]:
                    optional_pending.append(record)

        for name in closure["optional"]["runtime"]:
            record = _runtime_optional_record(paths, name, required)
            if not record["enabled"]:
                optional_pending.append(record)

        for kind in ["hooks", "mcp", "external_install"]:
            for name in closure["optional"][kind]:
                optional_pending.append(_optional_integration_record(kind, name))

        if required_missing:
            status = "blocked"
            summary = f"缺少 {len(required_missing)} 个必需组件"
        elif runtime_pending:
            status = "needs_confirmation"
            summary = f"需要确认 {len(runtime_pending)} 个 runtime / external install"
        elif optional_pending:
            status = "degraded"
            summary = f"{len(optional_pending)} 个 optional 依赖未启用"
        else:
            status = "ready"
            summary = "必需依赖完整"
        stats[status] += 1
        command_rows.append({
            "name": command_name,
            "status": status,
            "label": COMMAND_HEALTH_LABELS[status],
            "summary": summary,
            "required_by": owners,
            "contract_source": contract.get("source", "unknown"),
            "declared": True,
            "required": required_records,
            "required_missing": required_missing,
            "runtime_pending": runtime_pending,
            "optional_pending": optional_pending,
        })

    return {"commands": command_rows, "stats": stats}


def component_paths(ecc_home: Path, project: Path, kind: str, name: str) -> tuple[Path, Path, str]:
    source_root, target_root = KIND_DIRS[kind]
    source = ecc_home / source_root / name
    target = project / target_root / name
    component = f"{kind}/{name}"
    return source, target, component


def _codex_safe_name(value: str, prefix: str = "ecc") -> str:
    stem = Path(value).stem
    safe = re.sub(r"[^A-Za-z0-9_-]+", "-", stem).strip("-_").lower()
    return f"{prefix}-{safe or 'asset'}"


def _codex_agent_name(agent_name: str) -> str:
    return _codex_safe_name(agent_name).replace("-", "_")


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _read_text(path: Path, limit: int | None = None) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return text[:limit] if limit else text


def _truncate_markdown(text: str, limit: int, source: Path) -> str:
    if len(text) <= limit:
        return text
    notice = f"\n\n[Truncated by ecc-manager to keep this Antigravity file under {limit} characters. Source: {source}]\n"
    return text[: max(0, limit - len(notice))].rstrip() + notice


def _first_summary_line(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip().lstrip("#").strip()
        if stripped and not stripped.startswith("---") and ":" not in stripped[:24]:
            return stripped[:180]
    return fallback


def _managed_file_status(path: Path, desired: str, marker: str) -> str:
    if not path.exists() and not path.is_symlink():
        return "generate_file"
    if path.is_dir() or path.is_symlink():
        return "existing_real"
    current = path.read_text(encoding="utf-8", errors="ignore")
    if marker not in current:
        return "existing_real"
    return "already_generated" if current == desired else "update_generated"


def render_codex_agent_toml(source: Path, agent_file: str) -> str:
    raw = _read_text(source, limit=24000)
    agent_name = _codex_agent_name(agent_file)
    description = _first_summary_line(raw, f"ECC adapted agent from {agent_file}.")
    instructions = "\n".join([
        f"You are the Codex adaptation of the ECC agent `{agent_file}`.",
        "Follow the source instructions below while respecting the active Codex sandbox, approvals, and project AGENTS.md instructions.",
        "",
        "## ECC source agent instructions",
        raw.strip(),
        "",
    ])
    return "\n".join([
        CODEX_AGENT_MARKER,
        f"# Source: {source}",
        f"name = {_toml_string(agent_name)}",
        f"description = {_toml_string(description)}",
        f"developer_instructions = {_toml_string(instructions)}",
        "",
    ])


def render_codex_skill_adapter(source: Path, skill_name: str) -> str:
    readme = source / "README.md"
    source_text = _read_text(readme if readme.exists() else source, limit=12000) if source.is_file() or readme.exists() else ""
    description = _first_summary_line(source_text, f"Use ECC skill material from {skill_name}.")
    body = source_text.strip() or f"Use the ECC skill source at `{source}` as supporting context for this workflow."
    return "\n".join([
        "---",
        f"name: {_codex_safe_name(skill_name)}",
        f"description: {description}",
        "origin: ECC",
        "---",
        "",
        CODEX_AGENT_MARKER,
        f"Source: {source}",
        "",
        "Use this adapter when the task matches the ECC skill source below.",
        "",
        body,
        "",
    ])


def render_codex_command_skill(source: Path, command_name: str) -> str:
    raw = _read_text(source, limit=24000)
    skill_name = GLOBAL_PLAN_ENTRY_NAME if command_name == GLOBAL_PLAN_COMMAND_NAME else _codex_safe_name(command_name)
    invocation = _command_invocation(command_name)
    description = _first_summary_line(raw, f"Run the ECC workflow {invocation}.")
    return "\n".join([
        "---",
        f"name: {skill_name}",
        f"description: {description}",
        "origin: ECC",
        "---",
        "",
        CODEX_AGENT_MARKER,
        f"Source: {source}",
        "",
        f"Use this skill when the user asks for `{invocation}` or wants the ECC planning workflow.",
        "Follow the source ECC command workflow below. Adapt Claude Code specific wording to Codex while preserving the task intent, checks, and expected output.",
        "",
        raw.strip(),
        "",
    ])


def render_codex_command(source: Path, command_name: str) -> str:
    raw = _read_text(source, limit=24000)
    invocation = _command_invocation(command_name)
    return "\n".join([
        CODEX_AGENT_MARKER,
        f"# Source: {source}",
        "",
        f"# {invocation}",
        "",
        "This file is the Codex-readable adapter for the ECC slash-style command below.",
        "When the user asks for this command, follow the source workflow while adapting Claude Code specific wording to Codex.",
        "",
        "## ECC source command",
        "",
        raw.strip(),
        "",
    ])


def render_codex_rule(source: Path, rule_name: str) -> str:
    readme = source / "README.md"
    raw = _read_text(readme if readme.exists() else source, limit=24000) if source.is_file() or readme.exists() else ""
    body = raw.strip() or f"Apply the ECC rule source at `{source}` when this project's selected profile requires `{rule_name}`."
    return "\n".join([
        CODEX_AGENT_MARKER,
        f"# Source: {source}",
        "",
        f"# ECC rule: {rule_name}",
        "",
        "Apply this project rule when working in Codex on tasks covered by the active ECC profiles.",
        "",
        "## ECC source rule",
        "",
        body,
        "",
    ])


def _codex_generated_record(kind: str, name: str, source: Path, target: Path, desired: str, owners: list[str]) -> dict[str, Any]:
    status = _managed_file_status(target, desired, CODEX_AGENT_MARKER)
    return {
        "kind": kind,
        "component": f"codex/{kind}/{name}",
        "name": name,
        "source": str(source),
        "target": str(target),
        "status": status,
        "required_by": owners,
        "content": desired,
    }


def codex_bridge_plan(
    paths: Paths,
    project: Path,
    merged: dict[str, dict[str, dict[str, list[str]]]],
    config: dict[str, Any],
) -> dict[str, Any]:
    enabled = _as_bool(config.get("enable_codex", True))
    generated_file = config.get("generated_codex_file", paths.generated_codex_file)
    manage_agents_md = enabled or _as_bool(config.get("manage_agents_md", True))
    result: dict[str, Any] = {
        "enabled": enabled,
        "write": [],
        "existing_ok": [],
        "skipped": [],
        "missing": [],
        "generated": [],
        "manage_agents_md": manage_agents_md,
    }
    if not enabled:
        return result

    required = merged["required"]
    for command_name, owners in required.get("commands", {}).items():
        source = paths.ecc_home / "commands" / command_name
        adapter_dir = project / CODEX_SKILL_TARGET_ROOT / _codex_safe_name(command_name)
        adapter_file = adapter_dir / "SKILL.md"
        if not source.exists():
            result["missing"].append({
                "kind": "codex_command",
                "component": f"codex/commands/{command_name}",
                "name": command_name,
                "source": str(source),
                "target": str(adapter_dir),
                "status": "missing_source",
                "required_by": owners,
            })
            continue
        item = _codex_generated_record("commands", command_name, source, adapter_file, render_codex_command_skill(source, command_name), owners)
        item["command_name"] = Path(command_name).stem
        item["codex_name"] = _codex_safe_name(command_name)
        item["target"] = str(adapter_dir)
        item["generated_file"] = str(adapter_file)
        if item["status"] in {"generate_file", "update_generated"}:
            result["write"].append(item)
        elif item["status"] == "already_generated":
            result["existing_ok"].append(item)
        else:
            result["skipped"].append(item)

    for skill_name, owners in required.get("skills", {}).items():
        source = paths.ecc_home / "skills" / skill_name
        if not source.exists():
            result["missing"].append({
                "kind": "codex_skill",
                "component": f"codex/skills/{skill_name}",
                "name": skill_name,
                "source": str(source),
                "target": str(project / CODEX_SKILL_TARGET_ROOT / skill_name),
                "status": "missing_source",
                "required_by": owners,
            })
            continue
        if source.is_dir() and (source / "SKILL.md").exists():
            target = project / CODEX_SKILL_TARGET_ROOT / skill_name
            item = {
                "kind": "codex_skill",
                "component": f"codex/skills/{skill_name}",
                "name": skill_name,
                "codex_name": skill_name,
                "source": str(source),
                "target": str(target),
                "required_by": owners,
            }
            status = symlink_status(target, source)
            if status == "missing":
                result["write"].append(item | {"status": "create_symlink"})
            elif status == "linked":
                result["existing_ok"].append(item | {"status": "already_linked"})
            else:
                result["skipped"].append(item | {"status": status})
        else:
            adapter_dir = project / CODEX_SKILL_TARGET_ROOT / _codex_safe_name(skill_name)
            adapter_file = adapter_dir / "SKILL.md"
            desired = render_codex_skill_adapter(source, skill_name)
            item = _codex_generated_record("skills", skill_name, source, adapter_file, desired, owners)
            item["codex_name"] = _codex_safe_name(skill_name)
            item["target"] = str(adapter_dir)
            item["generated_file"] = str(adapter_file)
            if item["status"] in {"generate_file", "update_generated"}:
                result["write"].append(item)
            elif item["status"] == "already_generated":
                result["existing_ok"].append(item)
            else:
                result["skipped"].append(item)

    for agent_file, owners in required.get("agents", {}).items():
        source = paths.ecc_home / "agents" / agent_file
        target = project / CODEX_AGENT_TARGET_ROOT / f"{_codex_safe_name(agent_file)}.toml"
        if not source.exists():
            result["missing"].append({
                "kind": "codex_agent",
                "component": f"codex/agents/{agent_file}",
                "name": agent_file,
                "source": str(source),
                "target": str(target),
                "status": "missing_source",
                "required_by": owners,
            })
            continue
        item = _codex_generated_record("agents", agent_file, source, target, render_codex_agent_toml(source, agent_file), owners)
        item["agent_name"] = _codex_agent_name(agent_file)
        if item["status"] in {"generate_file", "update_generated"}:
            result["write"].append(item)
        elif item["status"] == "already_generated":
            result["existing_ok"].append(item)
        else:
            result["skipped"].append(item)

    for rule_name, owners in required.get("rules", {}).items():
        source = paths.ecc_home / "rules" / rule_name
        target = project / CODEX_RULE_TARGET_ROOT / f"{_codex_safe_name(rule_name)}.md"
        if not source.exists():
            result["missing"].append({
                "kind": "codex_rule",
                "component": f"codex/rules/{rule_name}",
                "name": rule_name,
                "source": str(source),
                "target": str(target),
                "status": "missing_source",
                "required_by": owners,
            })
            continue
        item = _codex_generated_record("rules", rule_name, source, target, render_codex_rule(source, rule_name), owners)
        item["kind"] = "codex_rule"
        if item["status"] in {"generate_file", "update_generated"}:
            result["write"].append(item)
        elif item["status"] == "already_generated":
            result["existing_ok"].append(item)
        else:
            result["skipped"].append(item)

    result["generated"] = [
        {"path": str(project / generated_file), "status": "generate"},
    ]
    if result["manage_agents_md"]:
        result["generated"].append({"path": str(project / "AGENTS.md"), "status": "upsert_managed_block"})
    return result


def render_antigravity_skill_adapter(source: Path, skill_name: str) -> str:
    readme = source / "README.md"
    source_text = _read_text(readme if readme.exists() else source, limit=12000) if source.is_file() or readme.exists() else ""
    description = _first_summary_line(source_text, f"Use ECC skill material from {skill_name}.")
    body = source_text.strip() or f"Use the ECC skill source at `{source}` as supporting context for this workflow."
    return "\n".join([
        "---",
        f"name: {_codex_safe_name(skill_name)}",
        f"description: {description}",
        "---",
        "",
        ANTIGRAVITY_MARKER,
        f"Source: {source}",
        "",
        "Use this adapter when an Antigravity task matches the ECC skill source below.",
        "",
        body,
        "",
    ])


def render_antigravity_workflow(source: Path, command_name: str, workflow_name: str | None = None) -> str:
    raw = _read_text(source)
    invocation = "/" + Path(workflow_name or command_name).stem
    description = _first_summary_line(raw, f"Run the ECC workflow {invocation}.")
    head = "\n".join([
        "---",
        f"description: {_yaml_scalar(description)}",
        "---",
        "",
        ANTIGRAVITY_MARKER,
        f"Source: {source}",
        "",
        f"# ECC Workflow: {invocation}",
        "",
        "Follow the source ECC command workflow below. Adapt Claude Code specific wording to Antigravity while preserving the task intent, checks, and expected output.",
        "",
    ])
    return _truncate_markdown("\n".join([head, raw.strip(), ""]), ANTIGRAVITY_FILE_CHAR_LIMIT, source)


def _yaml_scalar(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_antigravity_rule(source: Path, rule_name: str) -> str:
    readme = source / "README.md"
    raw = _read_text(readme if readme.exists() else source) if source.is_file() or readme.exists() else ""
    body = raw.strip() or f"Apply the ECC rule source at `{source}` when this project's selected profile requires `{rule_name}`."
    description = _first_summary_line(body, f"Apply the ECC {rule_name} project rule.")
    head = "\n".join([
        "---",
        f"description: {_yaml_scalar(description)}",
        "alwaysApply: true",
        "---",
        "",
        ANTIGRAVITY_MARKER,
        f"Source: {source}",
        "",
        f"# ECC Rule: {rule_name}",
        "",
        "Apply this rule when working in this project because the active ECC profile requires it.",
        "",
    ])
    return _truncate_markdown("\n".join([head, body, ""]), ANTIGRAVITY_FILE_CHAR_LIMIT, source)


def render_antigravity_agents_md(agent_sources: list[tuple[str, Path]]) -> str:
    lines = [
        ANTIGRAVITY_MARKER,
        "# ECC Antigravity Agents",
        "",
        "This file centralizes ECC agent personas for Google Antigravity.",
        "Workflows may shift context to these handles when orchestrating project work.",
        "",
    ]
    for agent_file, source in agent_sources:
        raw = _read_text(source, limit=8000).strip()
        handle = "@" + _codex_safe_name(agent_file, prefix="").replace("-", "_").strip("_")
        title = Path(agent_file).stem.replace("-", " ").replace("_", " ").title()
        lines.extend([
            f"## {title} ({handle})",
            "",
            f"**Source**: `{source}`",
            "",
            raw or f"Use the ECC source agent `{agent_file}` for this role.",
            "",
        ])
    return _truncate_markdown("\n".join(lines), ANTIGRAVITY_FILE_CHAR_LIMIT, agent_sources[0][1])


def _antigravity_generated_record(kind: str, name: str, source: Path, target: Path, desired: str, owners: list[str]) -> dict[str, Any]:
    status = _managed_file_status(target, desired, ANTIGRAVITY_MARKER)
    return {
        "kind": f"antigravity_{kind[:-1] if kind.endswith('s') else kind}",
        "component": f"antigravity/{kind}/{name}",
        "name": name,
        "source": str(source),
        "target": str(target),
        "status": status,
        "required_by": owners,
        "content": desired,
    }


def antigravity_bridge_plan(
    paths: Paths,
    project: Path,
    merged: dict[str, dict[str, dict[str, list[str]]]],
    config: dict[str, Any],
) -> dict[str, Any]:
    enabled = _as_bool(config.get("enable_antigravity", True))
    generated_file = config.get("generated_antigravity_file", paths.generated_antigravity_file)
    manage_agents_md = enabled or _as_bool(config.get("manage_agents_md", True))
    result: dict[str, Any] = {
        "enabled": enabled,
        "write": [],
        "existing_ok": [],
        "skipped": [],
        "missing": [],
        "generated": [],
        "manage_agents_md": manage_agents_md,
        "uses_shared_codex_skill_targets": enabled and _as_bool(config.get("enable_codex", True)),
    }
    if not enabled:
        return result

    required = merged["required"]
    agent_sources: list[tuple[str, Path]] = []
    agent_owners: list[str] = []
    for agent_file, owners in required.get("agents", {}).items():
        source = paths.ecc_home / "agents" / agent_file
        if not source.exists():
            result["missing"].append({
                "kind": "antigravity_agent",
                "component": f"antigravity/agents/{agent_file}",
                "name": agent_file,
                "source": str(source),
                "target": str(project / ANTIGRAVITY_AGENTS_TARGET),
                "status": "missing_source",
                "required_by": owners,
            })
            continue
        agent_sources.append((agent_file, source))
        for owner in owners:
            if owner not in agent_owners:
                agent_owners.append(owner)
    if agent_sources:
        target = project / ANTIGRAVITY_AGENTS_TARGET
        desired = render_antigravity_agents_md(agent_sources)
        status = _managed_file_status(target, desired, ANTIGRAVITY_MARKER)
        item = {
            "kind": "antigravity_agent",
            "component": "antigravity/agents/agents.md",
            "name": "agents.md",
            "source": str(paths.ecc_home / "agents"),
            "target": str(target),
            "status": status,
            "required_by": agent_owners,
            "content": desired,
            "agent_names": [agent_file for agent_file, _source in agent_sources],
        }
        if status in {"generate_file", "update_generated"}:
            result["write"].append(item)
        elif status == "already_generated":
            result["existing_ok"].append(item)
        else:
            result["skipped"].append(item)

    if not result["uses_shared_codex_skill_targets"]:
        for skill_name, owners in required.get("skills", {}).items():
            source = paths.ecc_home / "skills" / skill_name
            if not source.exists():
                result["missing"].append({
                    "kind": "antigravity_skill",
                    "component": f"antigravity/skills/{skill_name}",
                    "name": skill_name,
                    "source": str(source),
                    "target": str(project / CODEX_SKILL_TARGET_ROOT / skill_name),
                    "status": "missing_source",
                    "required_by": owners,
                })
                continue
            if source.is_dir() and (source / "SKILL.md").exists():
                target = project / CODEX_SKILL_TARGET_ROOT / skill_name
                item = {
                    "kind": "antigravity_skill",
                    "component": f"antigravity/skills/{skill_name}",
                    "name": skill_name,
                    "source": str(source),
                    "target": str(target),
                    "required_by": owners,
                }
                status = symlink_status(target, source)
                if status == "missing":
                    result["write"].append(item | {"status": "create_symlink"})
                elif status == "linked":
                    result["existing_ok"].append(item | {"status": "already_linked"})
                else:
                    result["skipped"].append(item | {"status": status})
            else:
                adapter_dir = project / CODEX_SKILL_TARGET_ROOT / _codex_safe_name(skill_name)
                adapter_file = adapter_dir / "SKILL.md"
                item = _antigravity_generated_record("skills", skill_name, source, adapter_file, render_antigravity_skill_adapter(source, skill_name), owners)
                item["target"] = str(adapter_dir)
                item["generated_file"] = str(adapter_file)
                if item["status"] in {"generate_file", "update_generated"}:
                    result["write"].append(item)
                elif item["status"] == "already_generated":
                    result["existing_ok"].append(item)
                else:
                    result["skipped"].append(item)

    for rule_name, owners in required.get("rules", {}).items():
        source = paths.ecc_home / "rules" / rule_name
        target = project / ANTIGRAVITY_RULE_TARGET_ROOT / f"{_codex_safe_name(rule_name)}.md"
        if not source.exists():
            result["missing"].append({
                "kind": "antigravity_rule",
                "component": f"antigravity/rules/{rule_name}",
                "name": rule_name,
                "source": str(source),
                "target": str(target),
                "status": "missing_source",
                "required_by": owners,
            })
            continue
        item = _antigravity_generated_record("rules", rule_name, source, target, render_antigravity_rule(source, rule_name), owners)
        if item["status"] in {"generate_file", "update_generated"}:
            result["write"].append(item)
        elif item["status"] == "already_generated":
            result["existing_ok"].append(item)
        else:
            result["skipped"].append(item)

    for command_name, owners in required.get("commands", {}).items():
        source = paths.ecc_home / "commands" / command_name
        workflow_name = f"{_codex_safe_name(command_name)}.md"
        target = project / ANTIGRAVITY_WORKFLOW_TARGET_ROOT / workflow_name
        if not source.exists():
            result["missing"].append({
                "kind": "antigravity_workflow",
                "component": f"antigravity/workflows/{command_name}",
                "name": command_name,
                "source": str(source),
                "target": str(target),
                "status": "missing_source",
                "required_by": owners,
            })
            continue
        item = _antigravity_generated_record("workflows", command_name, source, target, render_antigravity_workflow(source, command_name, workflow_name), owners)
        item["workflow_name"] = Path(workflow_name).stem
        if item["status"] in {"generate_file", "update_generated"}:
            result["write"].append(item)
        elif item["status"] == "already_generated":
            result["existing_ok"].append(item)
        else:
            result["skipped"].append(item)

    result["generated"] = [
        {"path": str(project / generated_file), "status": "generate"},
    ]
    if result["manage_agents_md"]:
        result["generated"].append({"path": str(project / "AGENTS.md"), "status": "upsert_managed_block"})
    return result


def symlink_status(target: Path, source: Path) -> str:
    if not target.exists() and not target.is_symlink():
        return "missing"
    if target.is_symlink():
        try:
            resolved = target.resolve(strict=True)
        except FileNotFoundError:
            return "broken"
        return "linked" if resolved == source.resolve() else "foreign_symlink"
    return "existing_real"


def _path_is_within(path: Path, root: Path) -> bool:
    try:
        path_value = os.path.normpath(os.path.abspath(os.path.expanduser(os.path.expandvars(str(path)))))
        root_value = os.path.normpath(os.path.abspath(os.path.expanduser(os.path.expandvars(str(root)))))
        return os.path.commonpath([path_value, root_value]) == root_value
    except ValueError:
        return False


def _require_plan_path_scope(path: Path, root: Path, label: str) -> None:
    if not path.is_absolute():
        raise ValueError(f"{label} must be absolute: {path}")
    if not _path_is_within(path, root):
        raise ValueError(f"{label} is outside allowed root: {path}")


def validate_plan_paths_for_apply(plan: dict[str, Any], config: dict[str, Any], project: Path) -> None:
    paths = paths_from_config(config)
    for bucket in ["create", "existing_ok", "skipped", "missing"]:
        for item in plan.get(bucket, []):
            source = Path(item.get("source", ""))
            target = Path(item.get("target", ""))
            _require_plan_path_scope(source, paths.ecc_home, f"{bucket} source")
            _require_plan_path_scope(target, project, f"{bucket} target")

    runtime_root = Path.home() / ".claude"
    runtime = plan.get("runtime", {}) if isinstance(plan.get("runtime", {}), dict) else {}
    for bucket in ["create", "existing_ok", "skipped", "missing"]:
        for item in runtime.get(bucket, []):
            source_value = item.get("source")
            target_value = item.get("target")
            if source_value:
                _require_plan_path_scope(Path(source_value), paths.ecc_home, f"runtime {bucket} source")
            if target_value:
                _require_plan_path_scope(Path(target_value), runtime_root, f"runtime {bucket} target")

    codex = plan.get("codex", {}) if isinstance(plan.get("codex", {}), dict) else {}
    for bucket in ["write", "existing_ok", "skipped", "missing"]:
        for item in codex.get(bucket, []):
            source_value = item.get("source")
            target_value = item.get("target")
            generated_value = item.get("generated_file")
            if source_value:
                _require_plan_path_scope(Path(source_value), paths.ecc_home, f"codex {bucket} source")
            if target_value:
                _require_plan_path_scope(Path(target_value), project, f"codex {bucket} target")
            if generated_value:
                _require_plan_path_scope(Path(generated_value), project, f"codex {bucket} generated file")
    for item in codex.get("generated", []):
        if item.get("path"):
            _require_plan_path_scope(Path(item["path"]), project, "codex generated path")

    antigravity = plan.get("antigravity", {}) if isinstance(plan.get("antigravity", {}), dict) else {}
    for bucket in ["write", "existing_ok", "skipped", "missing"]:
        for item in antigravity.get(bucket, []):
            source_value = item.get("source")
            target_value = item.get("target")
            generated_value = item.get("generated_file")
            if source_value:
                _require_plan_path_scope(Path(source_value), paths.ecc_home, f"antigravity {bucket} source")
            if target_value:
                _require_plan_path_scope(Path(target_value), project, f"antigravity {bucket} target")
            if generated_value:
                _require_plan_path_scope(Path(generated_value), project, f"antigravity {bucket} generated file")
    for item in antigravity.get("generated", []):
        if item.get("path"):
            _require_plan_path_scope(Path(item["path"]), project, "antigravity generated path")


def _profile_display_name(profile_id: str, profiles: dict[str, dict[str, Any]]) -> str:
    try:
        profile = get_profile(profile_id, profiles)
    except ValueError:
        return profile_id
    return profile.get("name_zh") or profile_id


def _task_goal(action: str, profile_ids: list[str], profiles: dict[str, dict[str, Any]]) -> str:
    names = "、".join(_profile_display_name(profile_id, profiles) for profile_id in profile_ids) or "未选择 profile"
    action_label = {
        "init": "初始化项目能力",
        "add": "添加项目能力",
        "phase": "追加阶段能力",
    }.get(action, "执行项目能力变更")
    return f"{action_label}：{names}"


def _command_invocation(command_name: str) -> str:
    return "/" + Path(command_name).stem


def _plan_next_commands(plan: dict[str, Any]) -> list[str]:
    commands = [_command_invocation(name) for name in plan.get("required", {}).get("commands", {})]
    return sorted(dict.fromkeys(commands))


def _command_health_criterion(command_health: dict[str, Any]) -> dict[str, str]:
    stats = command_health.get("stats", {}) if isinstance(command_health, dict) else {}
    total = sum(int(stats.get(status, 0) or 0) for status in COMMAND_HEALTH_LABELS)
    if not total:
        return {"id": "command_health", "status": "pass", "label": "命令可运行性", "message": "本次任务没有新增 command。"}
    if stats.get("blocked"):
        return {
            "id": "command_health",
            "status": "fail",
            "label": "命令可运行性",
            "message": f"{stats.get('blocked')} 个 command 缺少必需组件。",
        }
    warning_count = sum(int(stats.get(status, 0) or 0) for status in ["needs_confirmation", "degraded", "unknown"])
    if warning_count:
        details = []
        if stats.get("needs_confirmation"):
            details.append(f"{stats.get('needs_confirmation')} 个需要 runtime 确认")
        if stats.get("degraded"):
            details.append(f"{stats.get('degraded')} 个 optional 未启用")
        if stats.get("unknown"):
            details.append(f"{stats.get('unknown')} 个缺少依赖契约")
        return {
            "id": "command_health",
            "status": "warning",
            "label": "命令可运行性",
            "message": "；".join(details),
        }
    return {"id": "command_health", "status": "pass", "label": "命令可运行性", "message": "本次 command 的必需依赖完整。"}


def build_task_outline(
    plan: dict[str, Any],
    profiles: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    missing = plan.get("missing", [])
    skipped = plan.get("skipped", [])
    generated_name = Path(plan.get("generated", [{}])[0].get("path", "CLAUDE.ecc.generated.md")).name
    criteria = [
        {
            "id": "sources_available",
            "status": "fail" if missing else "pass",
            "label": "源组件存在",
            "message": f"{len(missing)} 个源组件缺失。" if missing else "所有 required 源组件都存在。",
        },
        {
            "id": "required_symlinks",
            "status": "fail" if skipped else "pending",
            "label": "required symlink 可创建",
            "message": f"{len(skipped)} 个目标已有冲突，执行时会跳过。" if skipped else "执行后检查所有 required symlink。",
        },
        {"id": "lock_written", "status": "pending", "label": "lock 写入", "message": "执行后写入 .ecc-manager/ecc-lock/profile.json。"},
        {"id": "generated_written", "status": "pending", "label": "说明文件生成", "message": f"执行后生成 {generated_name}。"},
        _command_health_criterion(plan.get("command_health", {})),
        _criterion("pending", "codex_bridge", "Codex 兼容层", "执行后生成 AGENTS.md 托管区、Codex skills 和 Codex agents。"),
        _criterion("pending", "antigravity_bridge", "Antigravity 兼容层", "执行后生成 Antigravity agents、workflows、rules 和项目说明。"),
    ]
    return {
        "goal": _task_goal(plan.get("action", ""), plan.get("profiles", []), profiles),
        "profiles": plan.get("profiles", []),
        "success_criteria": criteria,
        "next_commands": _plan_next_commands(plan),
    }


def build_plan(
    action: str,
    profile_ids: list[str],
    project_path: str | Path | None = None,
    config: dict[str, Any] | None = None,
    include_optional: bool = False,
) -> dict[str, Any]:
    config = config or load_config()
    paths = paths_from_config(config)
    project = normalize_project(project_path)
    profiles = load_profiles(paths.profile_home)
    if not any(profiles.values()):
        profiles = {"phases": PHASES, "architectures": ARCHITECTURES, "project-types": PROJECT_TYPES, "packs": PACKS}

    command_contracts = load_command_contracts(paths, paths.profile_home)
    validate_profile_selection(profile_ids, profiles)
    merged = merge_required(profile_ids, profiles, command_contracts)
    if include_optional:
        merged = promote_optional_dependencies(merged)
    runtime = runtime_plan(paths.ecc_home, merged["required"]["runtime"])
    command_health = build_command_health(paths, project, merged, command_contracts, runtime)
    codex = codex_bridge_plan(paths, project, merged, config)
    antigravity = antigravity_bridge_plan(paths, project, merged, config)
    claude_enabled = _as_bool(config.get("enable_claude", True))
    create: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    existing_ok: list[dict[str, Any]] = []

    if claude_enabled:
        for kind in KIND_DIRS:
            for name, owners in merged["required"][kind].items():
                source, target, component = component_paths(paths.ecc_home, project, kind, name)
                item = {
                    "kind": kind[:-1] if kind.endswith("s") else kind,
                    "component": component,
                    "name": name,
                    "source": str(source),
                    "target": str(target),
                    "required_by": owners,
                }
                if not source.exists():
                    missing.append(item | {"status": "missing_source"})
                    continue
                status = symlink_status(target, source)
                if status == "missing":
                    create.append(item | {"status": "create_symlink"})
                elif status == "linked":
                    existing_ok.append(item | {"status": "already_linked"})
                else:
                    skipped.append(item | {"status": status})

    generated = [
        *([{"path": str(project / paths.generated_claude_file), "status": "generate"}] if claude_enabled else []),
        {"path": str(lock_path(project)), "status": "write_lock"},
        *codex.get("generated", []),
        *antigravity.get("generated", []),
    ]
    generated = list({item["path"]: item for item in generated}.values())
    untouched = [str(project / ".claude" / "settings.json")]
    if not claude_enabled:
        untouched.extend([str(project / "CLAUDE.md"), str(project / paths.generated_claude_file)])
    else:
        untouched.append(str(project / "CLAUDE.md"))
    if not codex.get("manage_agents_md", True):
        untouched.append(str(project / "AGENTS.md"))
    plan = {
        "action": action,
        "project": str(project),
        "profiles": profile_ids,
        "include_optional": include_optional,
        "required": merged["required"],
        "optional": merged["optional"],
        "create": create,
        "skipped": skipped,
        "missing": missing,
        "existing_ok": existing_ok,
        "runtime": runtime,
        "codex": codex,
        "antigravity": antigravity,
        "enable_claude": claude_enabled,
        "command_health": command_health,
        "generated": generated,
        "untouched": untouched,
        "can_apply": (
            not missing
            and not skipped
            and not codex.get("missing")
            and not codex.get("skipped")
            and not antigravity.get("missing")
            and not antigravity.get("skipped")
        ),
        "requires_confirmation": bool(
            runtime["external_required"]
            or any(merged["optional"].values())
            or command_health["stats"].get("needs_confirmation")
        ),
    }
    plan["issues"] = plan_issues(plan)
    plan["task"] = build_task_outline(plan, profiles)
    return plan


def _criterion(status: str, criterion_id: str, label: str, message: str) -> dict[str, str]:
    return {"id": criterion_id, "status": status, "label": label, "message": message}


def issue_action(kind: str, label: str, description: str, mode: str, **extra: Any) -> dict[str, Any]:
    return {"kind": kind, "label": label, "description": description, "mode": mode, **extra}


def issue_record(
    issue_id: str,
    level: str,
    title: str,
    message: str,
    impact: str,
    actions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    fallback = issue_action("manual_guide", "查看指引", "按说明手动处理后重新扫描。", "manual")
    return {
        "id": issue_id,
        "level": level,
        "level_label": ISSUE_LEVEL_LABELS.get(level, level),
        "title": title,
        "message": message,
        "impact": impact,
        "actions": actions or [fallback],
    }


def _command_issue_actions(status: str) -> list[dict[str, Any]]:
    if status == "degraded":
        return [
            issue_action("preview_full_config", "满配预览", "把可管理的 optional 依赖纳入预览，确认后再写入。", "preview"),
            issue_action("navigate", "看预览", "回到预览页查看 Optional 未启用详情。", "navigation", page="preview"),
        ]
    if status == "needs_confirmation":
        return [
            issue_action("navigate", "查看 Doctor", "打开 Doctor 查看 runtime / external install 的确认项。", "navigation", page="doctor"),
            issue_action("manual_guide", "手动确认", "外部安装、runtime 初始化需要人工确认后再执行。", "manual"),
        ]
    if status == "blocked":
        return [
            issue_action("navigate", "看预览详情", "查看缺失的 required 组件和来源。", "navigation", page="preview"),
            issue_action("navigate", "能力治理", "到能力治理页检查缺失引用或补齐来源。", "navigation", page="assets"),
        ]
    if status == "unknown":
        return [
            issue_action("navigate", "能力治理", "为 command 补充 requires / optional 契约。", "navigation", page="assets"),
            issue_action("manual_guide", "补充契约", "在 command frontmatter 或依赖注册表中声明依赖。", "manual"),
        ]
    return []


def _command_health_issues(command_health: dict[str, Any], prefix: str = "command") -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for command in command_health.get("commands", []) if isinstance(command_health, dict) else []:
        status = command.get("status")
        if status in {"ready"}:
            continue
        level = "error" if status == "blocked" else ("warning" if status in {"needs_confirmation", "degraded"} else "info")
        issues.append(issue_record(
            f"{prefix}-{command.get('name', 'unknown')}-{status}",
            level,
            f"命令可运行性：{command.get('name')}",
            command.get("summary") or COMMAND_HEALTH_LABELS.get(status, status),
            {
                "blocked": "命令缺少必需组件，执行前需要补齐。",
                "needs_confirmation": "命令可用性依赖 runtime 或外部初始化确认。",
                "degraded": "命令可以运行，但 optional 增强能力未启用。",
                "unknown": "系统无法判断该命令依赖是否完整。",
            }.get(status, "需要查看命令依赖状态。"),
            _command_issue_actions(status),
        ))
    return issues


def _component_list_issue(
    issue_id: str,
    level: str,
    title: str,
    items: list[dict[str, Any]],
    impact: str,
    actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not items:
        return []
    preview = "；".join((item.get("component") or item.get("name") or item.get("source") or item.get("target") or "item") for item in items[:3])
    suffix = f"；另有 {len(items) - 3} 个" if len(items) > 3 else ""
    return [issue_record(issue_id, level, title, f"{preview}{suffix}", impact, actions)]


def plan_issues(plan: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    issues.extend(_component_list_issue(
        "plan-missing-sources",
        "error",
        "缺失源文件",
        plan.get("missing", []),
        "缺少 required 源组件时，本次计划不能安全执行。",
        [
            issue_action("navigate", "能力治理", "检查 profile 引用和 ECC_HOME 源文件。", "navigation", page="assets"),
            issue_action("manual_guide", "补齐源文件", "把缺失组件补到 ECC_HOME 后重新生成计划。", "manual"),
        ],
    ))
    issues.extend(_component_list_issue(
        "plan-target-conflicts",
        "error",
        "目标冲突",
        plan.get("skipped", []),
        "目标位置已有用户文件或外部 symlink，ECC Manager 不会覆盖。",
        [
            issue_action("navigate", "查看 Doctor", "用 Doctor 检查是否可安全修复。", "navigation", page="doctor"),
            issue_action("doctor_fix", "安全修复", "只修复托管且可恢复的项目，确认后执行。", "confirm"),
        ],
    ))
    runtime = plan.get("runtime", {}) if isinstance(plan.get("runtime"), dict) else {}
    issues.extend(_component_list_issue(
        "runtime-confirmation",
        "warning",
        "Runtime 需要确认",
        runtime.get("external_required", []),
        "这些 runtime 可能需要外部初始化；不会自动安装。",
        [
            issue_action("navigate", "查看 Doctor", "查看 runtime 当前状态。", "navigation", page="doctor"),
            issue_action("manual_guide", "手动初始化", "按 runtime 提示完成外部初始化后重新扫描。", "manual"),
        ],
    ))
    issues.extend(_component_list_issue(
        "runtime-missing",
        "warning",
        "Runtime 本地文件缺失",
        runtime.get("missing", []),
        "runtime 文件不存在时，相关命令只能降级或等待外部初始化。",
        [
            issue_action("navigate", "查看 Doctor", "查看缺失 runtime 的具体目标。", "navigation", page="doctor"),
            issue_action("manual_guide", "补齐 runtime", "安装或生成 runtime 文件后重新生成计划。", "manual"),
        ],
    ))
    for section_name, section in [("codex", plan.get("codex", {})), ("antigravity", plan.get("antigravity", {}))]:
        if not isinstance(section, dict):
            continue
        label = "Codex" if section_name == "codex" else "Antigravity"
        issues.extend(_component_list_issue(
            f"{section_name}-missing",
            "error",
            f"{label} 缺失源文件",
            section.get("missing", []),
            f"{label} 兼容层缺少源组件，相关适配不会生成。",
            [
                issue_action("navigate", "能力治理", "检查缺失源组件。", "navigation", page="assets"),
                issue_action("manual_guide", "补齐源文件", "补齐 ECC_HOME 里的源文件后重新生成计划。", "manual"),
            ],
        ))
        issues.extend(_component_list_issue(
            f"{section_name}-conflicts",
            "error",
            f"{label} 目标冲突",
            section.get("skipped", []),
            f"{label} 目标已有非托管内容，系统不会覆盖。",
            [
                issue_action("navigate", "查看 Doctor", "检查目标冲突和托管状态。", "navigation", page="doctor"),
                issue_action("manual_guide", "手动处理", "移动或确认已有文件后重新执行。", "manual"),
            ],
        ))
    optional_count = sum(len(items or {}) for items in (plan.get("optional") or {}).values())
    if optional_count:
        issues.append(issue_record(
            "optional-not-enabled",
            "warning",
            "Optional 依赖未启用",
            f"{optional_count} 个 optional 依赖仍未启用。",
            "命令可以运行，但增强能力不是满配；hooks/MCP/external install 仍需人工确认。",
            [
                issue_action("preview_full_config", "满配预览", "把可管理 optional 纳入预览，确认后执行。", "preview"),
                issue_action("manual_guide", "只保留降级", "如果当前能力够用，可以忽略这个 warning。", "manual"),
            ],
        ))
    issues.extend(_command_health_issues(plan.get("command_health", {}), "plan-command"))
    return issues


def _verification_summary(criteria: list[dict[str, str]]) -> dict[str, int]:
    return {
        "pass": sum(1 for item in criteria if item["status"] == "pass"),
        "warning": sum(1 for item in criteria if item["status"] == "warning"),
        "fail": sum(1 for item in criteria if item["status"] == "fail"),
    }


def _task_status_from_summary(summary: dict[str, int]) -> str:
    if summary.get("fail"):
        return "failed"
    if summary.get("warning"):
        return "completed_with_warnings"
    return "completed"


def _check_required_symlinks(plan: dict[str, Any]) -> dict[str, str]:
    failed: list[str] = []
    checked = 0
    for item in [*plan.get("create", []), *plan.get("existing_ok", [])]:
        checked += 1
        source = Path(item.get("source", ""))
        target = Path(item.get("target", ""))
        if not source.exists():
            failed.append(f"{item.get('component')}: source_missing")
            continue
        status = symlink_status(target, source)
        if status != "linked":
            failed.append(f"{item.get('component')}: {status}")
    for item in plan.get("skipped", []):
        failed.append(f"{item.get('component')}: {item.get('status')}")
    if failed:
        preview = "；".join(failed[:3])
        suffix = f"；另有 {len(failed) - 3} 个" if len(failed) > 3 else ""
        return _criterion("fail", "required_symlinks", "required symlink", f"{preview}{suffix}")
    return _criterion("pass", "required_symlinks", "required symlink", f"已验证 {checked} 个 required symlink。")


def _codex_item_ok(item: dict[str, Any]) -> bool:
    if item.get("kind") == "codex_skill" and item.get("status") == "create_symlink":
        return symlink_status(Path(item.get("target", "")), Path(item.get("source", ""))) == "linked"
    target = Path(item.get("generated_file") or item.get("target", ""))
    return target.exists() and CODEX_AGENT_MARKER in target.read_text(encoding="utf-8", errors="ignore")


def _check_codex_bridge(plan: dict[str, Any]) -> dict[str, str]:
    codex = plan.get("codex", {}) if isinstance(plan.get("codex", {}), dict) else {}
    if not codex.get("enabled", False):
        return _criterion("pass", "codex_bridge", "Codex 兼容层", "Codex 支持未启用。")
    failed: list[str] = []
    checked = 0
    for item in [*codex.get("write", []), *codex.get("existing_ok", [])]:
        checked += 1
        if item.get("status") in {"already_linked", "already_generated"}:
            continue
        if not _codex_item_ok(item):
            failed.append(f"{item.get('component')}: {item.get('status')}")
    for item in codex.get("skipped", []):
        failed.append(f"{item.get('component')}: {item.get('status')}")
    for item in codex.get("missing", []):
        failed.append(f"{item.get('component')}: missing_source")
    for item in codex.get("generated", []):
        path = Path(item.get("path", ""))
        if path.name == "AGENTS.md":
            if not path.exists() or CODEX_MANAGED_BLOCK_START not in path.read_text(encoding="utf-8", errors="ignore"):
                failed.append("AGENTS.md: managed_block_missing")
        elif not path.exists():
            failed.append(f"{path.name}: missing")
    if failed:
        preview = "；".join(failed[:3])
        suffix = f"；另有 {len(failed) - 3} 个" if len(failed) > 3 else ""
        return _criterion("fail", "codex_bridge", "Codex 兼容层", f"{preview}{suffix}")
    return _criterion("pass", "codex_bridge", "Codex 兼容层", f"已验证 {checked} 个 Codex command/skill/agent/rule 组件。")


def _antigravity_item_ok(item: dict[str, Any]) -> bool:
    if item.get("kind") == "antigravity_skill" and item.get("status") == "create_symlink":
        return symlink_status(Path(item.get("target", "")), Path(item.get("source", ""))) == "linked"
    target = Path(item.get("generated_file") or item.get("target", ""))
    return target.exists() and ANTIGRAVITY_MARKER in target.read_text(encoding="utf-8", errors="ignore")


def _check_antigravity_bridge(plan: dict[str, Any]) -> dict[str, str]:
    antigravity = plan.get("antigravity", {}) if isinstance(plan.get("antigravity", {}), dict) else {}
    if not antigravity.get("enabled", False):
        return _criterion("pass", "antigravity_bridge", "Antigravity 兼容层", "Antigravity 支持未启用。")
    failed: list[str] = []
    checked = 0
    for item in [*antigravity.get("write", []), *antigravity.get("existing_ok", [])]:
        checked += 1
        if item.get("status") in {"already_linked", "already_generated"}:
            continue
        if not _antigravity_item_ok(item):
            failed.append(f"{item.get('component')}: {item.get('status')}")
    for item in antigravity.get("skipped", []):
        failed.append(f"{item.get('component')}: {item.get('status')}")
    for item in antigravity.get("missing", []):
        failed.append(f"{item.get('component')}: missing_source")
    for item in antigravity.get("generated", []):
        path = Path(item.get("path", ""))
        if path.name == "AGENTS.md":
            if not path.exists() or ANTIGRAVITY_MANAGED_BLOCK_START not in path.read_text(encoding="utf-8", errors="ignore"):
                failed.append("AGENTS.md: antigravity_managed_block_missing")
        elif not path.exists():
            failed.append(f"{path.name}: missing")
    if failed:
        preview = "；".join(failed[:3])
        suffix = f"；另有 {len(failed) - 3} 个" if len(failed) > 3 else ""
        return _criterion("fail", "antigravity_bridge", "Antigravity 兼容层", f"{preview}{suffix}")
    return _criterion("pass", "antigravity_bridge", "Antigravity 兼容层", f"已验证 {checked} 个 Antigravity agent/workflow/rule/skill 组件。")


def _doctor_criterion(doctor_result: dict[str, Any]) -> dict[str, str]:
    checks = doctor_result.get("checks", [])
    errors = _task_relevant_doctor_errors(doctor_result)
    warnings = [item for item in checks if item.get("level") == "warning"]
    if errors:
        return _criterion("fail", "doctor_checks", "Doctor 自动验证", f"{len(errors)} 个 error，需要先处理。")
    if warnings:
        return _criterion("warning", "doctor_checks", "Doctor 自动验证", f"{len(warnings)} 个 warning，需要跟进。")
    return _criterion("pass", "doctor_checks", "Doctor 自动验证", "Doctor 未发现阻断项。")


def doctor_check_actions(check: dict[str, Any]) -> list[dict[str, Any]]:
    level = check.get("level")
    name = str(check.get("name", ""))
    message = str(check.get("message", ""))
    if level not in {"warning", "error"}:
        return []
    if any(token in message for token in ["missing", "缺失", "broken", "managed file missing"]) or any(token in name for token in ["托管区", "generated", "AGENTS.md", "CLAUDE", "command"]):
        return [
            issue_action("doctor_fix", "安全修复", "重新生成托管说明或修复可恢复 symlink，确认后执行。", "confirm"),
            issue_action("manual_guide", "手动处理", "检查该路径或托管区后重新运行 Doctor。", "manual"),
        ]
    if name.startswith("ECC") or name in {"profiles", "profile JSON", "ECC compatibility"}:
        return [
            issue_action("navigate", "打开设置", "检查 ECC_HOME 和 PROFILE_HOME 配置。", "navigation", page="settings"),
            issue_action("manual_guide", "查看路径", "确认路径存在且版本兼容。", "manual"),
        ]
    if name.startswith("command "):
        status_text = "blocked" if "缺少必需" in message else "degraded" if "降级" in message else "unknown"
        return _command_issue_actions(status_text) or [issue_action("navigate", "能力治理", "检查 command 依赖契约。", "navigation", page="assets")]
    if "未记录" in name or "旧版" in name:
        return [
            issue_action("navigate", "查看状态", "查看当前项目记录和遗留产物。", "navigation", page="status"),
            issue_action("manual_guide", "人工确认", "确认不是用户自有文件后再清理。", "manual"),
        ]
    return [issue_action("manual_guide", "查看指引", "按提示处理后重新运行 Doctor。", "manual")]


def enrich_doctor_checks(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for index, check in enumerate(checks):
        actions = doctor_check_actions(check)
        impact = "该检查不阻断当前流程。" if check.get("level") == "info" else "如果不处理，相关能力可能不可用或继续显示 warning。"
        enriched.append({
            **check,
            "id": check.get("id") or f"doctor-{index}-{_codex_safe_name(check.get('name', 'check'))}",
            "impact": impact,
            "actions": actions,
        })
    return enriched


def doctor_issues(doctor_result: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for check in doctor_result.get("checks", []):
        if check.get("level") not in {"warning", "error"}:
            continue
        issues.append(issue_record(
            check.get("id") or f"doctor-{_codex_safe_name(check.get('name', 'check'))}",
            "error" if check.get("level") == "error" else "warning",
            check.get("name", "Doctor check"),
            check.get("message", ""),
            check.get("impact") or "如果不处理，相关能力可能不可用或继续显示 warning。",
            check.get("actions") or doctor_check_actions(check),
        ))
    return issues


def _task_relevant_doctor_errors(doctor_result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item for item in doctor_result.get("checks", [])
        if item.get("level") == "error" and not str(item.get("name", "")).startswith("source missing in ")
    ]


def _claude_reference_missing(doctor_result: dict[str, Any]) -> bool:
    for item in doctor_result.get("checks", []):
        if item.get("name") in {"CLAUDE.md", "CLAUDE.md 引用"} and item.get("level") in {"info", "warning"}:
            return True
    return False


def _task_next_actions(plan: dict[str, Any], criteria: list[dict[str, str]], doctor_result: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    by_id = {item["id"]: item for item in criteria}
    command_stats = plan.get("command_health", {}).get("stats", {})
    if by_id.get("sources_available", {}).get("status") == "fail":
        actions.append({"kind": "fix_sources", "message": "补齐缺失的 ECC_HOME 源组件后重新生成计划。", "title": "补齐源组件", "impact": "源组件缺失会阻止计划安全执行。", "actions": [issue_action("navigate", "能力治理", "检查缺失引用。", "navigation", page="assets")]})
    if by_id.get("required_symlinks", {}).get("status") == "fail":
        actions.append({"kind": "run_doctor_fix", "message": "运行 Doctor 安全修复，或手动处理目标文件冲突。", "title": "处理目标冲突", "impact": "目标冲突时不会覆盖用户文件。", "actions": [issue_action("doctor_fix", "安全修复", "确认后修复可恢复项。", "confirm"), issue_action("navigate", "查看 Doctor", "查看冲突详情。", "navigation", page="doctor")]})
    if by_id.get("codex_bridge", {}).get("status") == "fail":
        actions.append({"kind": "fix_codex_bridge", "message": "处理 AGENTS.md、.agents/skills 或 .codex/agents 的目标冲突后重新执行。", "title": "修复 Codex 兼容层", "impact": "Codex 可能无法读取完整 ECC 能力。", "actions": [issue_action("navigate", "查看 Doctor", "检查 Codex 目标。", "navigation", page="doctor")]})
    if by_id.get("antigravity_bridge", {}).get("status") == "fail":
        actions.append({"kind": "fix_antigravity_bridge", "message": "处理 Antigravity workflows、rules 或 AGENTS.md 的目标冲突后重新执行。", "title": "修复 Antigravity 兼容层", "impact": "Antigravity 可能无法读取完整 ECC 能力。", "actions": [issue_action("navigate", "查看 Doctor", "检查 Antigravity 目标。", "navigation", page="doctor")]})
    if command_stats.get("blocked"):
        actions.append({"kind": "fix_command_dependencies", "message": "先修复 blocked command 的必需依赖。", "title": "修复命令必需依赖", "impact": "blocked command 可能无法运行。", "actions": _command_issue_actions("blocked")})
    if command_stats.get("needs_confirmation"):
        actions.append({"kind": "confirm_runtime", "message": "确认 runtime / external install 后，这些 command 才算完整可运行。", "title": "确认 runtime", "impact": "未确认 runtime 会让命令能力不完整。", "actions": _command_issue_actions("needs_confirmation")})
    if command_stats.get("unknown"):
        actions.append({"kind": "declare_command_contracts", "message": "为 unknown command 补充 frontmatter requires / optional 契约。", "title": "补充命令契约", "impact": "系统无法自动判断该命令是否满配。", "actions": _command_issue_actions("unknown")})
    if command_stats.get("degraded"):
        actions.append({"kind": "review_optional_dependencies", "message": "按需启用 optional 依赖，消除 degraded 状态。", "title": "启用 optional 依赖", "impact": "命令可运行，但增强能力不是满配。", "actions": _command_issue_actions("degraded")})
    doctor_warnings = sum(1 for item in doctor_result.get("checks", []) if item.get("level") == "warning")
    if doctor_warnings:
        actions.append({"kind": "review_doctor_warnings", "message": f"查看 Doctor 的 {doctor_warnings} 个 warning，能自动修复的可运行安全修复。", "title": "查看 Doctor warning", "impact": "Doctor warning 可能影响工具读取生成说明或兼容层。", "actions": [issue_action("navigate", "查看 Doctor", "打开 Doctor 检查详情。", "navigation", page="doctor"), issue_action("doctor_fix", "安全修复", "确认后重新生成托管文件。", "confirm")]})
    if _claude_reference_missing(doctor_result):
        generated_name = Path(plan.get("generated", [{}])[0].get("path", "CLAUDE.ecc.generated.md")).name
        actions.append({"kind": "wire_claude_md", "message": f"在项目 CLAUDE.md 中加入 @{generated_name}，让 Claude Code 自动读取生成说明。", "title": "连接 CLAUDE.md", "impact": "未引用生成说明时，Claude Code 可能不会自动读取 ECC 配置。", "actions": [issue_action("manual_guide", "手动加入引用", f"在 CLAUDE.md 中加入 @{generated_name}。", "manual")]})
    next_commands = _plan_next_commands(plan)
    if next_commands and not any(item["status"] == "fail" for item in criteria):
        actions.append({"kind": "run_command", "message": "下一步可在 Claude Code 中运行：" + "、".join(next_commands[:5]), "title": "运行下一步命令", "impact": "环境已装配，可以进入下一步工作。", "actions": [issue_action("manual_guide", "复制命令使用", "在对应 AI 工具中运行建议命令。", "manual")]})
    if not actions:
        actions.append({"kind": "done", "message": "任务已经完成，当前没有必须跟进的动作。", "title": "已完成", "impact": "没有需要处理的问题。", "actions": []})
    return actions


def build_task_run(
    plan: dict[str, Any],
    apply_result: dict[str, Any],
    doctor_result: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    criteria = [
        _criterion(
            "fail" if plan.get("missing") else "pass",
            "sources_available",
            "源组件存在",
            f"{len(plan.get('missing', []))} 个源组件缺失。" if plan.get("missing") else "所有 required 源组件都存在。",
        ),
        _check_required_symlinks(plan),
        _criterion(
            "pass" if Path(apply_result.get("lock", "")).exists() else "fail",
            "lock_written",
            "lock 写入",
            apply_result.get("lock", "lock 未写入"),
        ),
        _criterion(
            "pass" if not plan.get("enable_claude", True) or Path(apply_result.get("generated", "")).exists() else "fail",
            "generated_written",
            "Claude 说明文件",
            apply_result.get("generated") or "Claude Code 目标未启用",
        ),
        _command_health_criterion(plan.get("command_health", {})),
        _check_codex_bridge(plan),
        _check_antigravity_bridge(plan),
        _doctor_criterion(doctor_result),
    ]
    summary = _verification_summary(criteria)
    status = _task_status_from_summary(summary)
    task = plan.get("task") or {}
    doctor_result["checks"] = enrich_doctor_checks(doctor_result.get("checks", []))
    issues = [*plan.get("issues", []), *doctor_issues(doctor_result)]
    return {
        "id": f"task-{created_at}",
        "created_at": created_at,
        "goal": task.get("goal") or "执行项目能力变更",
        "status": status,
        "label": TASK_STATUS_LABELS[status],
        "project": plan.get("project"),
        "profiles": plan.get("profiles", []),
        "next_commands": task.get("next_commands") or _plan_next_commands(plan),
        "next_actions": _task_next_actions(plan, criteria, doctor_result),
        "issues": issues,
        "verification": {
            "criteria": criteria,
            "summary": summary,
            "doctor": {
                "errors": len(_task_relevant_doctor_errors(doctor_result)),
                "warnings": sum(1 for item in doctor_result.get("checks", []) if item.get("level") == "warning"),
                "checks": len(doctor_result.get("checks", [])),
            },
        },
        "apply": {
            "applied": len(apply_result.get("applied", [])),
            "runtime_applied": len(apply_result.get("runtime_applied", [])),
            "codex_applied": len(apply_result.get("codex_applied", [])),
            "antigravity_applied": len(apply_result.get("antigravity_applied", [])),
            "lock": apply_result.get("lock"),
            "generated": apply_result.get("generated"),
        },
        "config": {
            "ecc_home": config.get("ecc_home"),
            "profile_home": config.get("profile_home"),
        },
    }


def task_run_summary(task_run: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": task_run.get("id"),
        "created_at": task_run.get("created_at"),
        "goal": task_run.get("goal"),
        "status": task_run.get("status"),
        "label": task_run.get("label"),
        "project": task_run.get("project"),
        "profiles": task_run.get("profiles", []),
        "next_commands": task_run.get("next_commands", []),
        "next_actions": task_run.get("next_actions", []),
        "issues": task_run.get("issues", []),
        "verification": task_run.get("verification", {}),
    }


def record_task_run(project: Path, task_run: dict[str, Any]) -> dict[str, Any]:
    lock = read_lock(project)
    if not lock:
        return {}
    summary = task_run_summary(task_run)
    history = lock.setdefault("task_history", [])
    history.append(summary)
    del history[:-20]
    lock["last_task_run"] = summary
    write_json(lock_path(project), lock)
    if lock.get("enable_claude", True):
        render_generated_claude(project, lock)
    if lock.get("enable_codex", True):
        render_generated_codex(project, lock)
    if lock.get("enable_antigravity", True):
        render_generated_antigravity(project, lock)
    if lock.get("manage_agents_md", True) and (lock.get("enable_codex", True) or lock.get("enable_antigravity", True)):
        update_agents_md(project, lock)
    return summary


def status_issues(data: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    scan = data.get("scan", {}) if isinstance(data.get("scan"), dict) else {}
    if scan.get("ecc_status") != "ok":
        issues.append(issue_record(
            "status-ecc-home",
            "error",
            "ECC_HOME 不可用",
            scan.get("ecc_home", "ECC_HOME 缺失"),
            "无法从 ECC_HOME 读取 commands / skills / agents / rules。",
            [issue_action("navigate", "打开设置", "检查 ECC_HOME 配置。", "navigation", page="settings")],
        ))
    if scan.get("profiles_status") != "ok":
        issues.append(issue_record(
            "status-profile-home",
            "warning",
            "Profile 配置不可用",
            scan.get("profile_home", "PROFILE_HOME 缺失"),
            "无法读取阶段、架构和能力包配置。",
            [issue_action("navigate", "打开设置", "检查 PROFILE_HOME 配置。", "navigation", page="settings")],
        ))
    if not data.get("initial_phase") and not data.get("components"):
        issues.append(issue_record(
            "status-not-initialized",
            "warning",
            "项目尚未初始化",
            "当前项目没有记录初始阶段或已安装组件。",
            "未初始化时，AI 工具不会获得 ECC 项目能力。",
            [issue_action("navigate", "去初始化", "选择阶段和架构后生成初始化预览。", "navigation", page="init")],
        ))
    skipped = data.get("skipped_existing") or []
    issues.extend(_component_list_issue(
        "status-skipped-existing",
        "warning",
        "存在跳过的目标",
        skipped,
        "这些目标当时没有写入，可能导致能力不完整。",
        [
            issue_action("navigate", "查看 Doctor", "检查目标是否可安全修复。", "navigation", page="doctor"),
            issue_action("doctor_fix", "安全修复", "确认后修复可恢复项。", "confirm"),
        ],
    ))
    runtime_external = data.get("runtime_external_required") or []
    issues.extend(_component_list_issue(
        "status-runtime-external",
        "warning",
        "Runtime / external 待确认",
        runtime_external,
        "这些运行时不会自动安装，需要人工确认。",
        [
            issue_action("navigate", "查看 Doctor", "查看 runtime 状态。", "navigation", page="doctor"),
            issue_action("manual_guide", "手动确认", "完成外部初始化后重新扫描。", "manual"),
        ],
    ))
    issues.extend(_command_health_issues(data.get("command_health", {}), "status-command"))
    last_task = data.get("last_task_run") or {}
    if last_task.get("status") in {"completed_with_warnings", "failed"}:
        issues.append(issue_record(
            "status-last-task",
            "error" if last_task.get("status") == "failed" else "warning",
            "最近任务需要跟进",
            last_task.get("label") or last_task.get("status"),
            "最近一次执行仍有 warning/fail，需要查看任务结果。",
            [issue_action("navigate", "查看任务结果", "打开最近任务结果。", "navigation", page="task")],
        ))
    return issues


def _relative_to_project(project: Path, path: str | Path) -> str:
    target = Path(path)
    try:
        return str(target.relative_to(project))
    except ValueError:
        return str(target)


def _record_codex_component(lock: dict[str, Any], project: Path, item: dict[str, Any]) -> None:
    component = item["component"]
    target = item.get("generated_file") or item.get("target") or (project / "AGENTS.md")
    record = lock.setdefault("codex_components", {}).setdefault(
        component,
        {
            "managed": True,
            "kind": item.get("kind"),
            "source": item.get("source"),
            "target": _relative_to_project(project, target),
            "required_by": [],
        },
    )
    record["kind"] = item.get("kind")
    record["source"] = item.get("source")
    record["target"] = _relative_to_project(project, target)
    if item.get("generated_file"):
        record["generated_file"] = _relative_to_project(project, item["generated_file"])
    if item.get("agent_name"):
        record["agent_name"] = item["agent_name"]
    if item.get("codex_name"):
        record["codex_name"] = item["codex_name"]
    for owner in item.get("required_by", []):
        if owner not in record["required_by"]:
            record["required_by"].append(owner)


def apply_codex_bridge(codex: dict[str, Any], lock: dict[str, Any], project: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    if not codex.get("enabled", False):
        return []
    lock["enable_codex"] = True
    lock["manage_agents_md"] = codex.get("manage_agents_md", _as_bool(config.get("manage_agents_md", True)))
    lock["generated_codex_file"] = config.get("generated_codex_file", CODEX_GENERATED_FILE_DEFAULT)
    lock.setdefault("codex_components", {})
    applied: list[dict[str, Any]] = []

    for item in codex.get("write", []):
        status = item.get("status")
        if item.get("kind") == "codex_skill" and status == "create_symlink":
            source = Path(item["source"])
            target = Path(item["target"])
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() and not target.is_symlink():
                target.symlink_to(source, target_is_directory=source.is_dir())
                applied.append(item)
        elif status in {"generate_file", "update_generated"}:
            target = Path(item.get("generated_file") or item["target"])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(item.get("content", ""), encoding="utf-8")
            applied.append(item)
        _record_codex_component(lock, project, item)

    for item in codex.get("existing_ok", []):
        _record_codex_component(lock, project, item)
    return applied


def _record_antigravity_component(lock: dict[str, Any], project: Path, item: dict[str, Any]) -> None:
    component = item["component"]
    target = item.get("generated_file") or item.get("target")
    record = lock.setdefault("antigravity_components", {}).setdefault(
        component,
        {
            "managed": True,
            "kind": item.get("kind"),
            "source": item.get("source"),
            "target": _relative_to_project(project, target),
            "required_by": [],
        },
    )
    if item.get("generated_file"):
        record["generated_file"] = _relative_to_project(project, item["generated_file"])
    if item.get("workflow_name"):
        record["workflow_name"] = item["workflow_name"]
    if item.get("agent_names"):
        record["agent_names"] = item["agent_names"]
    for owner in item.get("required_by", []):
        if owner not in record["required_by"]:
            record["required_by"].append(owner)


def apply_antigravity_bridge(antigravity: dict[str, Any], lock: dict[str, Any], project: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    if not antigravity.get("enabled", False):
        return []
    lock["enable_antigravity"] = True
    lock["manage_agents_md"] = antigravity.get("manage_agents_md", _as_bool(config.get("manage_agents_md", True)))
    lock["generated_antigravity_file"] = config.get("generated_antigravity_file", ANTIGRAVITY_GENERATED_FILE_DEFAULT)
    lock.setdefault("antigravity_components", {})
    applied: list[dict[str, Any]] = []

    for item in antigravity.get("write", []):
        status = item.get("status")
        if item.get("kind") == "antigravity_skill" and status == "create_symlink":
            source = Path(item["source"])
            target = Path(item["target"])
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() and not target.is_symlink():
                target.symlink_to(source, target_is_directory=source.is_dir())
                applied.append(item)
        elif status in {"generate_file", "update_generated"}:
            target = Path(item.get("generated_file") or item["target"])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(item.get("content", ""), encoding="utf-8")
            applied.append(item)
        _record_antigravity_component(lock, project, item)

    for item in antigravity.get("existing_ok", []):
        _record_antigravity_component(lock, project, item)
    return applied


def apply_plan(plan: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_config()
    project = normalize_project(plan["project"])
    validate_plan_paths_for_apply(plan, config, project)
    lock = read_lock(project) or default_lock(config)
    lock.setdefault("components", {})
    lock.setdefault("skipped_existing", [])

    applied: list[dict[str, Any]] = []
    for item in plan.get("create", []):
        source = Path(item["source"])
        target = Path(item["target"])
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() or target.is_symlink():
            continue
        target.symlink_to(source, target_is_directory=source.is_dir())
        applied.append(item)

    runtime_applied: list[dict[str, Any]] = []
    for item in plan.get("runtime", {}).get("create", []):
        source = Path(item["source"])
        target = Path(item["target"])
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() or target.is_symlink():
            continue
        target.symlink_to(source, target_is_directory=source.is_dir())
        runtime_applied.append(item)

    for item in plan.get("create", []) + plan.get("existing_ok", []):
        component = item["component"]
        record = lock["components"].setdefault(
            component,
            {
                "managed": True,
                "kind": item["kind"],
                "source": item["source"],
                "target": str(Path(item["target"]).relative_to(project)),
                "required_by": [],
            },
        )
        for owner in item.get("required_by", []):
            if owner not in record["required_by"]:
                record["required_by"].append(owner)

    for item in plan.get("runtime", {}).get("create", []) + plan.get("runtime", {}).get("existing_ok", []):
        component = item["component"]
        record = lock["components"].setdefault(
            component,
            {
                "managed": True,
                "kind": "runtime",
                "source": item.get("source"),
                "target": item.get("target"),
                "required_by": [],
            },
        )
        for owner in item.get("required_by", []):
            if owner not in record["required_by"]:
                record["required_by"].append(owner)

    for item in plan.get("skipped", []):
        entry = {
            "component": item["component"],
            "target": item["target"],
            "status": "skipped_existing",
            "reason": item["status"],
            "required_by": item.get("required_by", []),
        }
        if entry not in lock["skipped_existing"]:
            lock["skipped_existing"].append(entry)

    codex_applied = apply_codex_bridge(plan.get("codex", {}), lock, project, config)
    antigravity_applied = apply_antigravity_bridge(plan.get("antigravity", {}), lock, project, config)
    update_lock_profiles(lock, plan.get("profiles", []))
    lock["ecc_version"] = ecc_version_metadata(paths_from_config(config))
    lock["generated_claude_file"] = config.get("generated_claude_file", "CLAUDE.ecc.generated.md")
    lock["generated_codex_file"] = config.get("generated_codex_file", CODEX_GENERATED_FILE_DEFAULT)
    lock["generated_antigravity_file"] = config.get("generated_antigravity_file", ANTIGRAVITY_GENERATED_FILE_DEFAULT)
    lock["enable_claude"] = _as_bool(config.get("enable_claude", True))
    lock["enable_codex"] = _as_bool(config.get("enable_codex", True))
    lock["enable_antigravity"] = _as_bool(config.get("enable_antigravity", True))
    lock["manage_agents_md"] = (
        (lock["enable_codex"] and plan.get("codex", {}).get("manage_agents_md", True))
        or (lock["enable_antigravity"] and plan.get("antigravity", {}).get("manage_agents_md", True))
        or _as_bool(config.get("manage_agents_md", True))
    )
    lock["optional_pending"] = plan.get("optional", {})
    lock["runtime_external_required"] = plan.get("runtime", {}).get("external_required", [])
    lock["command_health"] = plan.get("command_health", {"commands": [], "stats": {}})
    write_json(lock_path(project), lock)
    generated_file = render_generated_claude(project, lock) if lock.get("enable_claude", True) else None
    codex_generated_file = None
    antigravity_generated_file = None
    if lock.get("enable_codex", True):
        codex_generated_file = render_generated_codex(project, lock)
    if lock.get("enable_antigravity", True):
        antigravity_generated_file = render_generated_antigravity(project, lock)
    if lock.get("manage_agents_md", True) and (lock.get("enable_codex", True) or lock.get("enable_antigravity", True)):
        update_agents_md(project, lock)
    result = {
        "ok": True,
        "applied": applied,
        "runtime_applied": runtime_applied,
        "codex_applied": codex_applied,
        "antigravity_applied": antigravity_applied,
        "lock": str(lock_path(project)),
        "generated": str(generated_file) if generated_file else None,
        "codex_generated": str(codex_generated_file) if codex_generated_file else None,
        "antigravity_generated": str(antigravity_generated_file) if antigravity_generated_file else None,
    }
    doctor_result = doctor(project, fix=False, config=config)
    task_run = build_task_run(plan, result, doctor_result, config)
    result["task_run"] = task_run
    result["task_summary"] = record_task_run(project, task_run)
    result["doctor"] = doctor_result
    return result


def update_lock_profiles(lock: dict[str, Any], profile_ids: list[str]) -> None:
    profiles = load_profiles(lock.get("profile_home", DEFAULT_CONFIG["profile_home"]))
    if not any(profiles.values()):
        profiles = {"phases": PHASES, "architectures": ARCHITECTURES, "project-types": PROJECT_TYPES, "packs": PACKS}
    groups = validate_profile_selection(profile_ids, profiles)
    if groups["phases"]:
        if lock.get("initial_phase") is None:
            lock["initial_phase"] = groups["phases"][0]
            rest = groups["phases"][1:]
        else:
            rest = groups["phases"]
        lock.setdefault("added_phases", [])
        for item in rest:
            if item not in lock["added_phases"] and item != lock.get("initial_phase"):
                lock["added_phases"].append(item)
    if groups["architectures"]:
        lock["architecture"] = groups["architectures"][-1]
    for key, group in [("project_types", "project-types"), ("packs", "packs")]:
        lock.setdefault(key, [])
        for item in groups[group]:
            if item not in lock[key]:
                lock[key].append(item)


def render_generated_claude(project: Path, lock: dict[str, Any]) -> Path:
    target = project / lock.get("generated_claude_file", "CLAUDE.ecc.generated.md")
    generated_name = target.name
    components = lock.get("components", {})

    def list_kind(kind: str) -> list[str]:
        prefix = f"{kind}/"
        return sorted(c[len(prefix):] for c in components if c.startswith(prefix))

    lines = [
        "# ECC 项目配置说明",
        "",
        "本文件由 ecc-use 自动生成。",
        "",
        "如果希望 Claude Code 自动读取本文件，请在项目 CLAUDE.md 中加入：",
        "",
        f"@{generated_name}",
        "",
        "## 当前配置",
        "",
        f"- 初始阶段：{lock.get('initial_phase') or '未设置'}",
        f"- 已追加阶段：{', '.join(lock.get('added_phases', [])) or '无'}",
        f"- 技术架构：{lock.get('architecture') or '未设置'}",
        f"- 技术栈片段：{', '.join(lock.get('project_types', [])) or '无'}",
        f"- 能力包：{', '.join(lock.get('packs', [])) or '无'}",
        f"- ECC 版本：{(lock.get('ecc_version') or {}).get('version') or 'unknown'}",
        f"- Codex 兼容层：{'启用' if lock.get('enable_codex', True) else '未启用'}",
        f"- Antigravity 兼容层：{'启用' if lock.get('enable_antigravity', True) else '未启用'}",
        "",
        "## 已启用能力",
        "",
    ]
    for title, kind in [("Commands", "commands"), ("Rules", "rules"), ("Skills", "skills"), ("Agents", "agents")]:
        lines.append(f"### {title}")
        items = list_kind(kind)
        lines.extend([f"- {item}" for item in items] or ["- 无"])
        lines.append("")
    lines.append("### Runtime")
    runtime_items = list_kind("runtime")
    lines.extend([f"- {item}" for item in runtime_items] or ["- 无"])
    if lock.get("runtime_external_required"):
        lines.append("")
        lines.append("需要单独确认的 runtime / external install：")
        for item in lock.get("runtime_external_required", []):
            installs = ", ".join(item.get("external_install", [])) or "无"
            lines.append(f"- {item.get('name')}: {installs}")
    lines.append("")
    last_task = lock.get("last_task_run")
    if last_task:
        lines.extend([
            "## 最近任务结果",
            "",
            f"- 目标：{last_task.get('goal')}",
            f"- 状态：{last_task.get('label') or last_task.get('status')}",
        ])
        next_commands = last_task.get("next_commands") or []
        if next_commands:
            lines.append(f"- 下一步命令：{', '.join(next_commands)}")
        next_actions = last_task.get("next_actions") or []
        if next_actions:
            lines.append("- 跟进行动：")
            lines.extend(f"  - {item.get('message')}" for item in next_actions[:5])
        lines.append("")
    health_commands = (lock.get("command_health") or {}).get("commands", [])
    if health_commands:
        lines.extend([
            "## 命令可运行性",
            "",
        ])
        for item in health_commands:
            label = item.get("label") or COMMAND_HEALTH_LABELS.get(item.get("status"), item.get("status", "unknown"))
            summary = item.get("summary") or ""
            lines.append(f"- {item.get('name')}: {label}" + (f"（{summary}）" if summary else ""))
        lines.append("")
    lines.extend([
        "## 注意",
        "",
        "- 本工具不会修改原始 CLAUDE.md。",
        "- 本工具不会管理 .claude/settings.json。",
        "- hooks / MCP / external install 只有在明确确认后才启用。",
    ])
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def _lock_component_names(lock: dict[str, Any], prefix: str) -> list[str]:
    components = lock.get("components", {})
    return sorted(component[len(prefix):] for component in components if component.startswith(prefix))


def _codex_component_names(lock: dict[str, Any], prefix: str) -> list[str]:
    components = lock.get("codex_components", {})
    return sorted(component[len(prefix):] for component in components if component.startswith(prefix))


def _codex_skill_invocations(lock: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for component, item in (lock.get("codex_components") or {}).items():
        if component.startswith("codex/skills/"):
            out.append(item.get("codex_name") or component.rsplit("/", 1)[-1])
    return sorted(dict.fromkeys(out))


def _antigravity_component_names(lock: dict[str, Any], prefix: str) -> list[str]:
    components = lock.get("antigravity_components", {})
    return sorted(component[len(prefix):] for component in components if component.startswith(prefix))


def _antigravity_workflow_invocations(lock: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for component, item in (lock.get("antigravity_components") or {}).items():
        if component.startswith("antigravity/workflows/"):
            out.append("/" + (item.get("workflow_name") or _codex_safe_name(component.rsplit("/", 1)[-1])))
    return sorted(dict.fromkeys(out))


def _antigravity_skill_names(lock: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for component in (lock.get("antigravity_components") or {}):
        if component.startswith("antigravity/skills/"):
            out.append(component[len("antigravity/skills/"):])
    if not out and lock.get("enable_codex"):
        out.extend(_codex_skill_invocations(lock))
    return sorted(dict.fromkeys(out))


def _antigravity_agent_names(lock: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for component, item in (lock.get("antigravity_components") or {}).items():
        if component.startswith("antigravity/agents/"):
            out.extend(item.get("agent_names") or [component[len("antigravity/agents/"):]])
    return sorted(dict.fromkeys(out))


def _antigravity_workflow_targets(lock: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for component, item in (lock.get("antigravity_components") or {}).items():
        if component.startswith("antigravity/workflows/"):
            invocation = "/" + (item.get("workflow_name") or _codex_safe_name(component.rsplit("/", 1)[-1]))
            target = item.get("target") or f"{ANTIGRAVITY_WORKFLOW_TARGET_ROOT}/{invocation.lstrip('/')}.md"
            out.append((invocation, target))
    return sorted(dict.fromkeys(out))


def render_generated_codex(project: Path, lock: dict[str, Any]) -> Path:
    target = project / lock.get("generated_codex_file", CODEX_GENERATED_FILE_DEFAULT)
    commands = _lock_component_names(lock, "commands/") or _codex_component_names(lock, "codex/commands/")
    rules = _lock_component_names(lock, "rules/") or _codex_component_names(lock, "codex/rules/")
    codex_skills = _codex_skill_invocations(lock)
    codex_agents = _codex_component_names(lock, "codex/agents/")
    agent_names = [
        item.get("agent_name") or _codex_agent_name(name)
        for name in codex_agents
        for item in [lock.get("codex_components", {}).get(f"codex/agents/{name}", {})]
    ]
    lines = [
        "# ECC Codex 项目说明",
        "",
        "本文件由 ecc-use 自动生成，供 Codex App/Desktop、CLI 和 IDE 扩展共享同一套项目级配置。",
        "",
        "Codex 桌面端、CLI 和 IDE 扩展都会使用项目级 AGENTS.md、.agents/skills 和 .codex/agents；ECC Manager 会在 AGENTS.md 中维护一个托管区，引用这里的能力摘要。",
        "",
        "## 当前配置",
        "",
        f"- 初始阶段：{lock.get('initial_phase') or '未设置'}",
        f"- 已追加阶段：{', '.join(lock.get('added_phases', [])) or '无'}",
        f"- 技术架构：{lock.get('architecture') or '未设置'}",
        f"- 技术栈片段：{', '.join(lock.get('project_types', [])) or '无'}",
        f"- 能力包：{', '.join(lock.get('packs', [])) or '无'}",
        f"- ECC 版本：{(lock.get('ecc_version') or {}).get('version') or 'unknown'}",
        "",
        "## Codex 使用方式",
        "",
        "- 项目指令入口：AGENTS.md 的 ECC Manager 托管区。",
        f"- Codex skills：{CODEX_SKILL_TARGET_ROOT}/",
        f"- Codex custom agents：{CODEX_AGENT_TARGET_ROOT}/",
        "- ECC slash-style command 在 Codex 中会生成 command skill；当用户输入类似 /review-pr 时，按下方命令索引找到对应 skill。",
        "",
        "## ECC 命令索引",
        "",
    ]
    lines.extend([f"- /{Path(name).stem}: ${_codex_safe_name(name)} ({CODEX_SKILL_TARGET_ROOT}/{_codex_safe_name(name)}/SKILL.md)" for name in commands] or ["- 无"])
    lines.extend(["", "## Codex Skills", ""])
    lines.extend([f"- ${name}" for name in codex_skills] or ["- 无"])
    lines.extend(["", "## Codex Custom Agents", ""])
    lines.extend([f"- {name}" for name in agent_names] or ["- 无"])
    lines.extend(["", "## ECC Rules", ""])
    lines.extend([f"- {name}: {CODEX_RULE_TARGET_ROOT}/{_codex_safe_name(name)}.md" for name in rules] or ["- 无"])
    lines.extend([
        "",
        "## 注意",
        "",
        "- AGENTS.md 只维护带 ecc-manager 标记的托管区；用户自己的内容会保留。",
        "- ECC commands 适配为 repo-scoped skills，因为 Codex 会扫描 .agents/skills/**/SKILL.md。",
        f"- ECC rules 写入 {CODEX_RULE_TARGET_ROOT}/，并在 AGENTS.md 托管区中列出。",
        "- hooks / MCP / external install 仍然只有在明确确认后才启用。",
    ])
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def render_generated_antigravity(project: Path, lock: dict[str, Any]) -> Path:
    target = project / lock.get("generated_antigravity_file", ANTIGRAVITY_GENERATED_FILE_DEFAULT)
    workflow_targets = _antigravity_workflow_targets(lock)
    workflows = [invocation for invocation, _target in workflow_targets]
    rules = _antigravity_component_names(lock, "antigravity/rules/")
    skills = _antigravity_skill_names(lock)
    agents = _antigravity_agent_names(lock)
    lines = [
        "# ECC Antigravity 项目说明",
        "",
        "本文件由 ecc-use 自动生成，供 Google Antigravity 读取项目级 ECC 配置。",
        "",
        "Antigravity 会读取项目 AGENTS.md；ECC Manager 会在 AGENTS.md 中维护 Antigravity 托管区，并生成 workspace agents、skills、rules 和 workflows。",
        "",
        "## 当前配置",
        "",
        f"- 初始阶段：{lock.get('initial_phase') or '未设置'}",
        f"- 已追加阶段：{', '.join(lock.get('added_phases', [])) or '无'}",
        f"- 技术架构：{lock.get('architecture') or '未设置'}",
        f"- 技术栈片段：{', '.join(lock.get('project_types', [])) or '无'}",
        f"- 能力包：{', '.join(lock.get('packs', [])) or '无'}",
        f"- ECC 版本：{(lock.get('ecc_version') or {}).get('version') or 'unknown'}",
        "",
        "## Antigravity 使用方式",
        "",
        "- 项目指令入口：AGENTS.md 的 ECC Manager Antigravity 托管区。",
        f"- Workspace agents：{ANTIGRAVITY_AGENTS_TARGET}",
        f"- Workspace skills：{CODEX_SKILL_TARGET_ROOT}/",
        f"- Workspace rules：{ANTIGRAVITY_RULE_TARGET_ROOT}/",
        f"- Workspace workflows：{ANTIGRAVITY_WORKFLOW_TARGET_ROOT}/",
        "",
        "## Antigravity Workflows",
        "",
    ]
    lines.extend([f"- {name}" for name in workflows] or ["- 无"])
    lines.extend(["", "## Workflow 调用索引", ""])
    lines.extend([f"- {invocation}: {target}" for invocation, target in workflow_targets] or ["- 无"])
    lines.extend(["", "## Workspace Agents", ""])
    lines.extend([f"- {name}" for name in agents] or ["- 无"])
    lines.extend(["", "## Workspace Skills", ""])
    lines.extend([f"- {name}" for name in skills] or ["- 无"])
    lines.extend(["", "## Workspace Rules", ""])
    lines.extend([f"- {name}: {ANTIGRAVITY_RULE_TARGET_ROOT}/{_codex_safe_name(name)}.md" for name in rules] or ["- 无"])
    lines.extend([
        "",
        "## 注意",
        "",
        "- AGENTS.md 只维护带 ecc-manager 标记的托管区；用户自己的内容会保留。",
        "- ECC agents 会聚合到 .agents/agents.md；ECC commands 会转成 Antigravity workflows；ECC rules 会转成 workspace rules。",
        "- hooks / MCP / external install 仍然只有在明确确认后才启用。",
    ])
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def render_codex_managed_block(lock: dict[str, Any]) -> str:
    commands = _lock_component_names(lock, "commands/") or _codex_component_names(lock, "codex/commands/")
    rules = _lock_component_names(lock, "rules/") or _codex_component_names(lock, "codex/rules/")
    skills = _codex_skill_invocations(lock)
    agents = _codex_component_names(lock, "codex/agents/")
    agent_names = [
        item.get("agent_name") or _codex_agent_name(name)
        for name in agents
        for item in [lock.get("codex_components", {}).get(f"codex/agents/{name}", {})]
    ]
    command_line = ", ".join(f"/{Path(name).stem}" for name in commands) or "无"
    rule_line = ", ".join(rules) or "无"
    command_skill_line = ", ".join(f"${_codex_safe_name(name)}" for name in commands) or "无"
    skill_line = ", ".join(f"${name}" for name in skills) or "无"
    agent_line = ", ".join(agent_names) or "无"
    generated = lock.get("generated_codex_file", CODEX_GENERATED_FILE_DEFAULT)
    return "\n".join([
        CODEX_MANAGED_BLOCK_START,
        "## ECC Manager",
        "",
        "Use the ECC profile installed for this project when a task matches the selected phase, architecture, stack fragments, or packs.",
        "This project-level block is intended for Codex App/Desktop, Codex CLI, and the Codex IDE extension.",
        f"Full generated ECC/Codex report: `{generated}`.",
        "",
        f"Enabled ECC commands: {command_line}.",
        f"Command adapters are repo-scoped skills under `{CODEX_SKILL_TARGET_ROOT}/`: {command_skill_line}.",
        "When the user asks for one of those slash-style commands, use the corresponding skill.",
        "",
        f"Enabled ECC rules: {rule_line}.",
        f"Rule files are under `{CODEX_RULE_TARGET_ROOT}/`; apply them when the task matches the active ECC profiles.",
        "",
        f"Enabled Codex skills: {skill_line}.",
        "Use `$skill` explicitly when the user names one, or implicitly when the task matches the skill description.",
        "",
        f"Available Codex custom agents: {agent_line}.",
        "Only spawn subagents when the user explicitly asks for parallel or delegated agent work.",
        CODEX_MANAGED_BLOCK_END,
        "",
    ])


def render_antigravity_managed_block(lock: dict[str, Any]) -> str:
    workflows = _antigravity_workflow_invocations(lock)
    agents = _antigravity_agent_names(lock)
    skills = _antigravity_skill_names(lock)
    rules = _antigravity_component_names(lock, "antigravity/rules/")
    workflow_line = ", ".join(workflows) or "无"
    agent_line = ", ".join(agents) or "无"
    skill_line = ", ".join(skills) or "无"
    rule_line = ", ".join(rules) or "无"
    generated = lock.get("generated_antigravity_file", ANTIGRAVITY_GENERATED_FILE_DEFAULT)
    return "\n".join([
        ANTIGRAVITY_MANAGED_BLOCK_START,
        "## ECC Manager for Antigravity",
        "",
        "Use the ECC profile installed for this project when a task matches the selected phase, architecture, stack fragments, or packs.",
        "This project-level block is intended for Google Antigravity.",
        f"Full generated ECC/Antigravity report: `{generated}`.",
        "",
        f"Enabled Antigravity workflows: {workflow_line}.",
        f"When the user asks for one of those slash-style commands, follow the matching workflow under `{ANTIGRAVITY_WORKFLOW_TARGET_ROOT}/`.",
        "",
        f"Available Antigravity agents: {agent_line}.",
        f"Agent personas are centralized in `{ANTIGRAVITY_AGENTS_TARGET}`.",
        "",
        f"Enabled workspace skills: {skill_line}.",
        f"Enabled workspace rules: {rule_line}.",
        f"Rule files are under `{ANTIGRAVITY_RULE_TARGET_ROOT}/` and include `alwaysApply: true`.",
        "Use the generated workspace skills and rules when they match the task.",
        ANTIGRAVITY_MANAGED_BLOCK_END,
        "",
    ])


def _upsert_managed_block(current: str, block: str, start: str, end: str) -> str:
    pattern = re.compile(
        re.escape(start) + r".*?" + re.escape(end) + r"\n?",
        re.DOTALL,
    )
    if start in current and end in current:
        return pattern.sub(block, current)
    separator = "" if current.endswith("\n\n") else "\n\n" if current.endswith("\n") else "\n\n"
    return current + separator + block


def update_agents_md(project: Path, lock: dict[str, Any]) -> Path:
    target = project / "AGENTS.md"
    blocks: list[tuple[str, str, str]] = []
    if lock.get("enable_codex", True):
        blocks.append((render_codex_managed_block(lock), CODEX_MANAGED_BLOCK_START, CODEX_MANAGED_BLOCK_END))
    if lock.get("enable_antigravity", True):
        blocks.append((render_antigravity_managed_block(lock), ANTIGRAVITY_MANAGED_BLOCK_START, ANTIGRAVITY_MANAGED_BLOCK_END))
    block_text = "\n".join(block for block, _, _ in blocks)
    if not target.exists():
        target.write_text("# AGENTS.md\n\n" + block_text, encoding="utf-8")
        return target
    current = target.read_text(encoding="utf-8", errors="ignore")
    updated = current
    for block, start, end in blocks:
        updated = _upsert_managed_block(updated, block, start, end)
    target.write_text(updated, encoding="utf-8")
    return target


def global_plan_paths(paths: Paths) -> tuple[Path, Path, Path]:
    source = paths.ecc_home / "commands" / GLOBAL_PLAN_SOURCE_NAME
    target = Path.home() / ".claude" / "commands" / GLOBAL_PLAN_COMMAND_NAME
    legacy_target = Path.home() / ".claude" / "commands" / LEGACY_GLOBAL_PLAN_COMMAND_NAME
    return source, target, legacy_target


def project_plan_path(project: Path) -> Path:
    return project / ".claude" / "commands" / GLOBAL_PLAN_COMMAND_NAME


def project_codex_plan_skill_path(project: Path) -> Path:
    return project / CODEX_SKILL_TARGET_ROOT / GLOBAL_PLAN_ENTRY_NAME / "SKILL.md"


def project_antigravity_plan_workflow_path(project: Path) -> Path:
    return project / ANTIGRAVITY_WORKFLOW_TARGET_ROOT / f"{GLOBAL_PLAN_ENTRY_NAME}.md"


def scan_project(project_path: str | Path | None = None, config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_config()
    paths = paths_from_config(config)
    project = normalize_project(project_path)
    claude_dir = project / ".claude"
    codex_dir = project / ".codex"
    codex_skills_dir = project / ".agents" / "skills"
    codex_rules_dir = project / CODEX_RULE_TARGET_ROOT
    antigravity_rules_dir = project / ANTIGRAVITY_RULE_TARGET_ROOT
    antigravity_workflows_dir = project / ANTIGRAVITY_WORKFLOW_TARGET_ROOT
    antigravity_agents_file = project / ANTIGRAVITY_AGENTS_TARGET
    antigravity_legacy_workflows_dir = project / ANTIGRAVITY_LEGACY_WORKFLOW_TARGET_ROOT
    lock = read_lock(project)
    plan_source, global_plan, legacy_global_plan = global_plan_paths(paths)
    project_plan = project_plan_path(project)
    codex_plan_skill = project_codex_plan_skill_path(project)
    antigravity_plan_workflow = project_antigravity_plan_workflow_path(project)
    compatibility = ecc_manifest_metadata(paths)
    claude_enabled = _as_bool(config.get("enable_claude", True))
    codex_enabled = _as_bool(config.get("enable_codex", True))
    antigravity_enabled = _as_bool(config.get("enable_antigravity", True))
    return {
        "project": str(project),
        "ecc_home": str(paths.ecc_home),
        "profile_home": str(paths.profile_home),
        "generated_claude_file": paths.generated_claude_file,
        "generated_codex_file": paths.generated_codex_file,
        "generated_antigravity_file": paths.generated_antigravity_file,
        "exists": project.exists(),
        "has_claude_dir": claude_dir.exists(),
        "has_claude_md": (project / "CLAUDE.md").exists(),
        "has_generated": (project / paths.generated_claude_file).exists(),
        "claude_enabled": claude_enabled,
        "codex_enabled": codex_enabled,
        "antigravity_enabled": antigravity_enabled,
        "has_codex_dir": codex_dir.exists(),
        "has_codex_skills": codex_skills_dir.exists(),
        "has_codex_rules": codex_rules_dir.exists(),
        "has_antigravity_rules": antigravity_rules_dir.exists(),
        "has_antigravity_workflows": antigravity_workflows_dir.exists(),
        "has_antigravity_agents": antigravity_agents_file.exists(),
        "has_antigravity_legacy_workflows": antigravity_legacy_workflows_dir.exists(),
        "has_agents_md": (project / "AGENTS.md").exists(),
        "has_agents_md_managed_block": (project / "AGENTS.md").exists() and CODEX_MANAGED_BLOCK_START in (project / "AGENTS.md").read_text(encoding="utf-8", errors="ignore"),
        "has_agents_md_antigravity_block": (project / "AGENTS.md").exists() and ANTIGRAVITY_MANAGED_BLOCK_START in (project / "AGENTS.md").read_text(encoding="utf-8", errors="ignore"),
        "has_generated_codex": (project / paths.generated_codex_file).exists(),
        "has_generated_antigravity": (project / paths.generated_antigravity_file).exists(),
        "codex_components": lock.get("codex_components", {}),
        "antigravity_components": lock.get("antigravity_components", {}),
        "has_lock": lock_path(project).exists(),
        "lock": lock,
        "ecc_status": "ok" if paths.ecc_home.exists() else "missing",
        "profiles_status": "ok" if paths.profile_home.exists() else "missing",
        "ecc_compatibility": compatibility,
        "global_plan_command": "/ecc-plan",
        "global_plan_status": symlink_status(global_plan, plan_source) if plan_source.exists() else "missing_source",
        "project_plan_status": symlink_status(project_plan, plan_source) if plan_source.exists() else "missing_source",
        "codex_plan_skill_status": "existing" if codex_plan_skill.exists() else "missing",
        "antigravity_plan_workflow_status": "existing" if antigravity_plan_workflow.exists() else "missing",
        "legacy_global_plan_status": symlink_status(legacy_global_plan, plan_source) if plan_source.exists() else "missing_source",
        "obsolete_codex_artifacts": find_obsolete_codex_artifacts(project),
    }


def global_init(
    config: dict[str, Any] | None = None,
    dry_run: bool = False,
    project_path: str | Path | None = None,
) -> dict[str, Any]:
    config = config or load_config()
    paths = paths_from_config(config)
    source, target, legacy_target = global_plan_paths(paths)
    project = normalize_project(project_path) if project_path else None
    project_target = project_plan_path(project) if project else None
    status = symlink_status(target, source)
    legacy_status = symlink_status(legacy_target, source)
    project_status = symlink_status(project_target, source) if project_target else None
    result = {
        "command": "/ecc-plan",
        "source": str(source),
        "target": str(target),
        "legacy_target": str(legacy_target),
        "project_target": str(project_target) if project_target else None,
        "status": status,
        "legacy_status": legacy_status,
        "project_status": project_status,
        "dry_run": dry_run,
        "migrated_legacy": False,
    }
    if not source.exists():
        return result | {"ok": False, "error": "source missing"}
    if dry_run:
        project_ok = project_status in {None, "missing", "linked"}
        return result | {"ok": status in {"missing", "linked"} and project_ok}
    if status == "missing":
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(source)
        status = "created"
    elif status != "linked":
        return result | {"ok": False, "error": f"target conflict: {status}"}
    if project_target:
        if project_status == "missing":
            project_target.parent.mkdir(parents=True, exist_ok=True)
            project_target.symlink_to(source)
            project_status = "created"
        elif project_status != "linked":
            return result | {"ok": False, "error": f"project target conflict: {project_status}"}
        lock = read_lock(project) or default_lock(config)
        lock.setdefault("components", {})
        lock.setdefault("codex_components", {})
        lock.setdefault("antigravity_components", {})
        lock["codex_components"].pop("codex/skills/ecc-ecc-plan", None)
        command_component = f"commands/{GLOBAL_PLAN_COMMAND_NAME}"
        lock["components"].setdefault(command_component, {
            "managed": True,
            "kind": "command",
            "source": str(source),
            "target": _relative_to_project(project, project_target),
            "required_by": ["global-core"],
        })
        if _as_bool(config.get("enable_codex", True)):
            codex_skill_file = project_codex_plan_skill_path(project)
            codex_skill_file.parent.mkdir(parents=True, exist_ok=True)
            codex_skill_file.write_text(render_codex_command_skill(source, GLOBAL_PLAN_COMMAND_NAME), encoding="utf-8")
            _record_codex_component(lock, project, {
                "component": f"codex/skills/{GLOBAL_PLAN_ENTRY_NAME}",
                "kind": "codex_skill",
                "name": GLOBAL_PLAN_ENTRY_NAME,
                "codex_name": GLOBAL_PLAN_ENTRY_NAME,
                "source": str(source),
                "target": str(codex_skill_file.parent),
                "generated_file": str(codex_skill_file),
                "required_by": ["global-core"],
            })
            lock["enable_codex"] = True
        if _as_bool(config.get("enable_antigravity", True)):
            antigravity_workflow = project_antigravity_plan_workflow_path(project)
            antigravity_workflow.parent.mkdir(parents=True, exist_ok=True)
            antigravity_workflow.write_text(render_antigravity_workflow(source, GLOBAL_PLAN_COMMAND_NAME), encoding="utf-8")
            _record_antigravity_component(lock, project, {
                "component": f"antigravity/workflows/{GLOBAL_PLAN_COMMAND_NAME}",
                "kind": "antigravity_workflow",
                "name": GLOBAL_PLAN_COMMAND_NAME,
                "source": str(source),
                "target": str(antigravity_workflow),
                "workflow_name": GLOBAL_PLAN_ENTRY_NAME,
                "required_by": ["global-core"],
            })
            lock["enable_antigravity"] = True
        lock["manage_agents_md"] = _as_bool(config.get("manage_agents_md", True))
        lock["generated_codex_file"] = config.get("generated_codex_file", CODEX_GENERATED_FILE_DEFAULT)
        lock["generated_antigravity_file"] = config.get("generated_antigravity_file", ANTIGRAVITY_GENERATED_FILE_DEFAULT)
        lock["ecc_version"] = ecc_version_metadata(paths)
        write_json(lock_path(project), lock)
        if lock.get("enable_codex", True):
            render_generated_codex(project, lock)
        if lock.get("enable_antigravity", True):
            render_generated_antigravity(project, lock)
        if lock.get("manage_agents_md", True) and (lock.get("enable_codex", True) or lock.get("enable_antigravity", True)):
            update_agents_md(project, lock)
    migrated_legacy = False
    if legacy_status == "linked":
        legacy_target.unlink()
        migrated_legacy = True
    return result | {
        "ok": True,
        "status": status,
        "project_status": project_status,
        "migrated_legacy": migrated_legacy,
    }


def status(project_path: str | Path | None = None) -> dict[str, Any]:
    scan = scan_project(project_path)
    lock = scan.get("lock") or {}
    data = {
        "scan": scan,
        "initial_phase": lock.get("initial_phase"),
        "added_phases": lock.get("added_phases", []),
        "architecture": lock.get("architecture"),
        "project_types": lock.get("project_types", []),
        "packs": lock.get("packs", []),
        "components": lock.get("components", {}),
        "codex_components": lock.get("codex_components", {}),
        "antigravity_components": lock.get("antigravity_components", {}),
        "enable_claude": lock.get("enable_claude", True),
        "enable_codex": lock.get("enable_codex", True),
        "enable_antigravity": lock.get("enable_antigravity", True),
        "generated_codex_file": lock.get("generated_codex_file", CODEX_GENERATED_FILE_DEFAULT),
        "generated_antigravity_file": lock.get("generated_antigravity_file", ANTIGRAVITY_GENERATED_FILE_DEFAULT),
        "skipped_existing": lock.get("skipped_existing", []),
        "optional_pending": lock.get("optional_pending", {}),
        "runtime_external_required": lock.get("runtime_external_required", []),
        "command_health": lock.get("command_health", {"commands": [], "stats": {}}),
        "last_task_run": lock.get("last_task_run"),
        "task_history": lock.get("task_history", []),
    }
    data["issues"] = status_issues(data)
    return data


def doctor(
    project_path: str | Path | None = None,
    fix: bool = False,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or load_config()
    paths = paths_from_config(config)
    project = normalize_project(project_path)
    checks: list[dict[str, str]] = []
    fixes: list[dict[str, str]] = []

    def add(level: str, name: str, message: str) -> None:
        checks.append({"level": level, "name": name, "message": message})

    def fixed(name: str, message: str) -> None:
        fixes.append({"name": name, "message": message})

    add("ok" if paths.ecc_home.exists() else "error", "ECC_HOME", str(paths.ecc_home))
    compatibility = ecc_manifest_metadata(paths)
    compatibility_level = "ok" if compatibility["status"] == "supported" else "warning"
    add(compatibility_level, "ECC compatibility", compatibility["message"])
    for name in compatibility.get("missing", []):
        add("warning", f"ECC manifest missing: {name}", compatibility["manifests"][name]["path"])
    for dirname in ["commands", "skills", "agents", "rules"]:
        add("ok" if (paths.ecc_home / dirname).exists() else "error", f"ECC {dirname}", str(paths.ecc_home / dirname))
    add("ok" if paths.profile_home.exists() else "warning", "profiles", str(paths.profile_home))

    profiles = load_profiles(paths.profile_home)
    if any(profiles.values()):
        for group, items in profiles.items():
            add("ok", f"profile group {group}", f"{len(items)} 个 profile")
            checked_sources = 0
            missing_sources: list[str] = []
            for profile_id, profile in items.items():
                level = "ok" if profile.get("schema_version") == 1 else "error"
                add(level, f"profile {profile_id}", "schema_version=1" if level == "ok" else "schema_version 不支持")
                for kind in KIND_DIRS:
                    for name in profile.get("required", {}).get(kind, []):
                        source, _, component = component_paths(paths.ecc_home, project, kind, name)
                        checked_sources += 1
                        if not source.exists():
                            missing_sources.append(f"{component} -> {source}")
            if missing_sources:
                for item in missing_sources:
                    add("error", f"source missing in {group}", item)
            else:
                add("ok", f"source components {group}", f"已检查 {checked_sources} 个源组件，未发现缺失")
    elif paths.profile_home.exists():
        add("warning", "profile JSON", "profiles 目录存在，但没有可读取的 profile")

    if not lock_path(project).exists() and not legacy_lock_path(project).exists():
        add("warning", "lock", "当前项目没有 .ecc-manager/ecc-lock/profile.json")
    lock = read_lock(project)
    locked_version = lock.get("ecc_version") or {}
    if locked_version:
        current_fingerprint = ecc_version_metadata(paths).get("fingerprint")
        locked_fingerprint = locked_version.get("fingerprint")
        if locked_fingerprint and current_fingerprint and locked_fingerprint != current_fingerprint:
            add("warning", "ECC version changed", f"安装时 {locked_fingerprint}，当前 {current_fingerprint}；建议重新扫描并检查 profile health")
    for component, item in (lock.get("components") or {}).items():
        target = lock_target_path(project, item.get("target"))
        source = Path(item.get("source", ""))
        st = symlink_status(target, source)
        add("ok" if st == "linked" else "error", component, st)
        if fix and item.get("managed") and st in {"missing", "broken"} and source.exists():
            if target.is_symlink():
                target.unlink()
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(source, target_is_directory=source.is_dir())
                fixed(component, f"已修复 symlink -> {source}")
        elif fix and st in {"existing_real", "foreign_symlink"}:
            fixed(component, f"跳过：{st}，不会覆盖用户文件")

    if lock.get("enable_codex", config.get("enable_codex", True)):
        generated_codex = project / lock.get("generated_codex_file", config.get("generated_codex_file", CODEX_GENERATED_FILE_DEFAULT))
        add("ok" if generated_codex.exists() else "warning", generated_codex.name, "存在" if generated_codex.exists() else "缺失")
        agents_md = project / "AGENTS.md"
        if lock.get("manage_agents_md", config.get("manage_agents_md", True)):
            has_block = agents_md.exists() and CODEX_MANAGED_BLOCK_START in agents_md.read_text(encoding="utf-8", errors="ignore")
            add("ok" if has_block else "warning", "AGENTS.md 托管区", "已写入" if has_block else "缺失 ECC Manager 托管区")
        for component, item in (lock.get("codex_components") or {}).items():
            target = lock_target_path(project, item.get("generated_file") or item.get("target"))
            source = Path(item.get("source", ""))
            if item.get("kind") == "codex_skill":
                st = symlink_status(lock_target_path(project, item.get("target")), source)
                add("ok" if st == "linked" else "error", component, st)
                if fix and item.get("managed") and st in {"missing", "broken"} and source.exists():
                    symlink_target = lock_target_path(project, item.get("target"))
                    if symlink_target.is_symlink():
                        symlink_target.unlink()
                    if not symlink_target.exists():
                        symlink_target.parent.mkdir(parents=True, exist_ok=True)
                        symlink_target.symlink_to(source, target_is_directory=source.is_dir())
                        fixed(component, f"已修复 symlink -> {source}")
            else:
                exists = target.exists() and CODEX_AGENT_MARKER in target.read_text(encoding="utf-8", errors="ignore")
                add("ok" if exists else "error", component, "managed file" if exists else "managed file missing")
        if fix and lock:
            render_generated_codex(project, lock)
            fixed(generated_codex.name, "已重新生成")
            if lock.get("manage_agents_md", config.get("manage_agents_md", True)):
                update_agents_md(project, lock)
                fixed("AGENTS.md", "已更新 ECC Manager 托管区")

    if lock.get("enable_codex", config.get("enable_codex", True)):
        unmanaged_codex = find_unmanaged_codex_artifacts(project, lock)
        for item in unmanaged_codex:
            add("warning", "未记录的 Codex 产物", item)
        for item in find_obsolete_codex_artifacts(project):
            add("warning", "旧版 Codex command 产物", f"{item} 已不再是 ECC Manager 推荐路径；commands 现在写入 .agents/skills")

    if lock.get("enable_antigravity", config.get("enable_antigravity", True)):
        generated_antigravity = project / lock.get("generated_antigravity_file", config.get("generated_antigravity_file", ANTIGRAVITY_GENERATED_FILE_DEFAULT))
        add("ok" if generated_antigravity.exists() else "warning", generated_antigravity.name, "存在" if generated_antigravity.exists() else "缺失")
        agents_md = project / "AGENTS.md"
        if lock.get("manage_agents_md", config.get("manage_agents_md", True)):
            has_block = agents_md.exists() and ANTIGRAVITY_MANAGED_BLOCK_START in agents_md.read_text(encoding="utf-8", errors="ignore")
            add("ok" if has_block else "warning", "AGENTS.md Antigravity 托管区", "已写入" if has_block else "缺失 ECC Manager Antigravity 托管区")
        for component, item in (lock.get("antigravity_components") or {}).items():
            target = lock_target_path(project, item.get("generated_file") or item.get("target"))
            source = Path(item.get("source", ""))
            if item.get("kind") == "antigravity_skill":
                st = symlink_status(lock_target_path(project, item.get("target")), source)
                add("ok" if st == "linked" else "error", component, st)
                if fix and item.get("managed") and st in {"missing", "broken"} and source.exists():
                    symlink_target = lock_target_path(project, item.get("target"))
                    if symlink_target.is_symlink():
                        symlink_target.unlink()
                    if not symlink_target.exists():
                        symlink_target.parent.mkdir(parents=True, exist_ok=True)
                        symlink_target.symlink_to(source, target_is_directory=source.is_dir())
                        fixed(component, f"已修复 symlink -> {source}")
            else:
                exists = target.exists() and ANTIGRAVITY_MARKER in target.read_text(encoding="utf-8", errors="ignore")
                add("ok" if exists else "error", component, "managed file" if exists else "managed file missing")
        if fix and lock:
            render_generated_antigravity(project, lock)
            fixed(generated_antigravity.name, "已重新生成")
            if lock.get("manage_agents_md", config.get("manage_agents_md", True)):
                update_agents_md(project, lock)
                fixed("AGENTS.md Antigravity", "已更新 ECC Manager Antigravity 托管区")

    unmanaged_antigravity = find_unmanaged_antigravity_artifacts(project, lock)
    for item in unmanaged_antigravity:
        add("warning", "未记录的 Antigravity 产物", item)

    health_levels = {
        "ready": "ok",
        "needs_confirmation": "warning",
        "degraded": "warning",
        "blocked": "error",
        "unknown": "info",
    }
    for item in (lock.get("command_health") or {}).get("commands", []):
        status_name = item.get("status", "unknown")
        label = item.get("label") or COMMAND_HEALTH_LABELS.get(status_name, status_name)
        summary = item.get("summary") or ""
        add(health_levels.get(status_name, "warning"), f"command {item.get('name')}", f"{label}：{summary}")

    unmanaged = find_unmanaged_ecc_links(project, paths.ecc_home, lock)
    for item in unmanaged:
        add("info", "未记录的 ECC symlink", item)

    claude_enabled = lock.get("enable_claude", config.get("enable_claude", True))
    generated = project / config.get("generated_claude_file", "CLAUDE.ecc.generated.md")
    if claude_enabled:
        add("ok" if generated.exists() else "warning", generated.name, "存在" if generated.exists() else "缺失")
        claude_md = project / "CLAUDE.md"
        if claude_md.exists():
            content = claude_md.read_text(encoding="utf-8", errors="ignore")
            has_ref = f"@{generated.name}" in content
            add("ok" if has_ref else "info", "CLAUDE.md 引用", "已引用" if has_ref else f"建议加入 @{generated.name}")
        else:
            add("info", "CLAUDE.md", "项目没有 CLAUDE.md")

    if fix:
        lock_path(project).parent.mkdir(parents=True, exist_ok=True)
        fixed("ecc-lock", "已确保 .ecc-manager/ecc-lock 目录存在")
        if lock and claude_enabled:
            render_generated_claude(project, lock)
            fixed(generated.name, "已重新生成")

    checks = enrich_doctor_checks(checks)
    return {"project": str(project), "fix": fix, "checks": checks, "fixes": fixes, "issues": doctor_issues({"checks": checks})}


def find_unmanaged_ecc_links(project: Path, ecc_home: Path, lock: dict[str, Any]) -> list[str]:
    managed_targets = {
        str(lock_target_path(project, item.get("target")).absolute())
        for item in (lock.get("components") or {}).values()
    }
    out: list[str] = []
    for _, target_root in KIND_DIRS.values():
        root = project / target_root
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_symlink():
                continue
            try:
                resolved = path.resolve(strict=True)
            except FileNotFoundError:
                continue
            try:
                resolved.relative_to(ecc_home.resolve())
            except ValueError:
                continue
            if str(path.absolute()) not in managed_targets:
                out.append(str(path.relative_to(project)))
    return sorted(out)


def find_unmanaged_codex_artifacts(project: Path, lock: dict[str, Any]) -> list[str]:
    managed_targets = {
        str(lock_target_path(project, item.get("target")).absolute())
        for item in (lock.get("codex_components") or {}).values()
        if item.get("target")
    }
    managed_targets.update(
        str(lock_target_path(project, item.get("generated_file")).absolute())
        for item in (lock.get("codex_components") or {}).values()
        if item.get("generated_file")
    )
    out: list[str] = []
    for root_path in [project / ".agents" / "skills", project / ".codex" / "agents", project / CODEX_RULE_TARGET_ROOT]:
        if not root_path.exists():
            continue
        for path in root_path.rglob("*"):
            if not (path.is_symlink() or path.is_file()):
                continue
            if str(path.absolute()) not in managed_targets:
                out.append(str(path.relative_to(project)))
    return sorted(dict.fromkeys(out))


def find_obsolete_codex_artifacts(project: Path) -> list[str]:
    out: list[str] = []
    obsolete_roots = [
        project / ".codex" / "commands",
    ]
    for root_path in obsolete_roots:
        if not root_path.exists():
            continue
        for path in root_path.rglob("*.md"):
            if not path.is_file():
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if CODEX_AGENT_MARKER in content:
                out.append(str(path.relative_to(project)))
    return sorted(out)


def find_unmanaged_antigravity_artifacts(project: Path, lock: dict[str, Any]) -> list[str]:
    managed_targets = {
        str(lock_target_path(project, item.get("target")).absolute())
        for item in (lock.get("antigravity_components") or {}).values()
        if item.get("target")
    }
    managed_targets.update(
        str(lock_target_path(project, item.get("generated_file")).absolute())
        for item in (lock.get("antigravity_components") or {}).values()
        if item.get("generated_file")
    )
    out: list[str] = []
    roots = [
        project / ANTIGRAVITY_RULE_TARGET_ROOT,
        project / ANTIGRAVITY_WORKFLOW_TARGET_ROOT,
        project / ANTIGRAVITY_LEGACY_WORKFLOW_TARGET_ROOT,
    ]
    for root_path in roots:
        if not root_path.exists():
            continue
        for path in root_path.rglob("*"):
            if not (path.is_symlink() or path.is_file()):
                continue
            if str(path.absolute()) not in managed_targets:
                out.append(str(path.relative_to(project)))
    return sorted(dict.fromkeys(out))


def remove_profile(profile_id: str, project_path: str | Path | None = None, dry_run: bool = False) -> dict[str, Any]:
    project = normalize_project(project_path)
    lock = read_lock(project)
    removed: list[str] = []
    kept: list[str] = []
    if not lock:
        return {"ok": False, "error": "No lock file", "removed": removed, "kept": kept}

    def retain_component(component: str) -> None:
        if component not in kept:
            kept.append(component)

    def forget_component(component: str) -> None:
        if not dry_run:
            lock["components"].pop(component, None)

    for component, item in list(lock.get("components", {}).items()):
        refs = item.get("required_by", [])
        if profile_id in refs:
            refs.remove(profile_id)
        if refs:
            kept.append(component)
            continue
        target = lock_target_path(project, item.get("target"))
        source_value = item.get("source")
        if source_value:
            status = symlink_status(target, Path(source_value))
        elif target.is_symlink():
            status = "broken"
        elif target.exists():
            status = "existing_real"
        else:
            status = "missing"
        if status in {"linked", "broken"}:
            removed.append(component)
            if not dry_run and target.is_symlink():
                target.unlink()
            forget_component(component)
        elif status == "missing":
            removed.append(component)
            forget_component(component)
        else:
            retain_component(component)

    for component, item in list((lock.get("codex_components") or {}).items()):
        refs = item.get("required_by", [])
        if profile_id in refs:
            refs.remove(profile_id)
        if refs:
            kept.append(component)
            continue
        target = lock_target_path(project, item.get("generated_file") or item.get("target"))
        symlink_target = lock_target_path(project, item.get("target"))
        if item.get("kind") == "codex_skill" and symlink_target.is_symlink():
            source_value = item.get("source")
            if source_value:
                status = symlink_status(symlink_target, Path(source_value))
            elif symlink_target.is_symlink():
                status = "broken"
            elif symlink_target.exists():
                status = "existing_real"
            else:
                status = "missing"
            if status in {"linked", "broken"}:
                removed.append(component)
                if not dry_run:
                    symlink_target.unlink()
                if not dry_run:
                    lock["codex_components"].pop(component, None)
            else:
                retain_component(component)
                continue
        elif target.exists() and CODEX_AGENT_MARKER in target.read_text(encoding="utf-8", errors="ignore"):
            removed.append(component)
            if not dry_run:
                target.unlink()
                parent = target.parent
                if parent.name.startswith("ecc-") and not any(parent.iterdir()):
                    parent.rmdir()
            if not dry_run:
                lock["codex_components"].pop(component, None)
        elif target.is_symlink():
            retain_component(component)
            continue
        elif target.exists():
            retain_component(component)
            continue
        else:
            removed.append(component)
            if not dry_run:
                lock["codex_components"].pop(component, None)

    for component, item in list((lock.get("antigravity_components") or {}).items()):
        refs = item.get("required_by", [])
        if profile_id in refs:
            refs.remove(profile_id)
        if refs:
            kept.append(component)
            continue
        target = lock_target_path(project, item.get("generated_file") or item.get("target"))
        symlink_target = lock_target_path(project, item.get("target"))
        if item.get("kind") == "antigravity_skill" and symlink_target.is_symlink():
            source_value = item.get("source")
            if source_value:
                status = symlink_status(symlink_target, Path(source_value))
            elif symlink_target.is_symlink():
                status = "broken"
            elif symlink_target.exists():
                status = "existing_real"
            else:
                status = "missing"
            if status in {"linked", "broken"}:
                removed.append(component)
                if not dry_run:
                    symlink_target.unlink()
                    lock["antigravity_components"].pop(component, None)
            else:
                retain_component(component)
                continue
        elif target.exists() and ANTIGRAVITY_MARKER in target.read_text(encoding="utf-8", errors="ignore"):
            removed.append(component)
            if not dry_run:
                target.unlink()
                parent = target.parent
                if parent.name.startswith("ecc-") and not any(parent.iterdir()):
                    parent.rmdir()
                lock["antigravity_components"].pop(component, None)
        elif target.is_symlink():
            retain_component(component)
            continue
        elif target.exists():
            retain_component(component)
            continue
        else:
            removed.append(component)
            if not dry_run:
                lock["antigravity_components"].pop(component, None)

    for key in ["added_phases", "project_types", "packs"]:
        if profile_id in lock.get(key, []):
            if not dry_run:
                lock[key].remove(profile_id)
    if lock.get("initial_phase") == profile_id and not dry_run:
        lock["initial_phase"] = None
    if lock.get("architecture") == profile_id and not dry_run:
        lock["architecture"] = None
    if not dry_run:
        write_json(lock_path(project), lock)
        if lock.get("enable_claude", True):
            render_generated_claude(project, lock)
        if lock.get("enable_codex", True):
            render_generated_codex(project, lock)
        if lock.get("enable_antigravity", True):
            render_generated_antigravity(project, lock)
        if lock.get("manage_agents_md", True) and (lock.get("enable_codex", True) or lock.get("enable_antigravity", True)):
            update_agents_md(project, lock)
    return {"ok": True, "dry_run": dry_run, "removed": removed, "kept": kept}
