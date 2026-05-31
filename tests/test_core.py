from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ecc_manager import core
from ecc_manager.default_profiles import ARCHITECTURES, DEFAULT_CONFIG, PACKS, PHASES, PROJECT_TYPES


class CoreTests(unittest.TestCase):
    def make_config(self, root: Path) -> dict:
        ecc_home = root / "ecc"
        for dirname in ["commands", "skills", "agents", "rules"]:
            (ecc_home / dirname).mkdir(parents=True, exist_ok=True)
        for path in [
            ecc_home / "commands" / "plan.md",
            ecc_home / "commands" / "plan-prd.md",
            ecc_home / "skills" / "context-budget",
            ecc_home / "skills" / "strategic-compact",
            ecc_home / "skills" / "codebase-onboarding",
            ecc_home / "skills" / "coding-standards",
            ecc_home / "skills" / "api-design",
            ecc_home / "agents" / "planner.md",
            ecc_home / "agents" / "code-architect.md",
            ecc_home / "agents" / "code-explorer.md",
            ecc_home / "rules" / "common",
        ]:
            if path.suffix:
                path.write_text("test\n", encoding="utf-8")
            else:
                path.mkdir(parents=True, exist_ok=True)
                (path / "README.md").write_text("test\n", encoding="utf-8")
        config = dict(DEFAULT_CONFIG)
        config["ecc_home"] = str(ecc_home)
        config["profile_home"] = str(root / "profiles")
        return config

    def populate_required_assets(self, ecc_home: Path, profile_ids: list[str]) -> None:
        all_profiles = {**ARCHITECTURES, **PROJECT_TYPES}
        for profile_id in profile_ids:
            profile = all_profiles[profile_id]
            self.populate_profile_assets(ecc_home, profile)

    def populate_profile_assets(self, ecc_home: Path, profile: dict, seen: set[str] | None = None) -> None:
        seen = seen or set()
        profile_id = profile.get("id")
        if profile_id in seen:
            return
        if profile_id:
            seen.add(profile_id)
        for include_id in core.profile_include_ids(profile):
            include_profile = ARCHITECTURES.get(include_id) or PROJECT_TYPES.get(include_id) or PACKS.get(include_id) or PHASES.get(include_id)
            if include_profile:
                self.populate_profile_assets(ecc_home, include_profile, seen)
        for kind, (source_dir, _target_dir) in core.KIND_DIRS.items():
            for name in profile.get("required", {}).get(kind, []):
                path = ecc_home / source_dir / name
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.suffix:
                    path.write_text("test\n", encoding="utf-8")
                else:
                    path.mkdir(parents=True, exist_ok=True)
                    (path / "README.md").write_text("test\n", encoding="utf-8")

    def populate_all_default_assets(self, ecc_home: Path) -> None:
        for profiles in [PHASES, ARCHITECTURES, PROJECT_TYPES, PACKS]:
            for profile in profiles.values():
                self.populate_profile_assets(ecc_home, profile)

    def write_asset(self, ecc_home: Path, kind: str, name: str, content: str = "test\n") -> None:
        source_dir = core.KIND_DIRS[kind][0]
        path = ecc_home / source_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix:
            path.write_text(content, encoding="utf-8")
        else:
            path.mkdir(parents=True, exist_ok=True)
            (path / "SKILL.md").write_text(content, encoding="utf-8")

    def write_pack(self, config: dict, profile: dict) -> None:
        core.write_json(Path(config["profile_home"]) / "packs" / f"{profile['id']}.json", profile)

    def write_command_dependencies(self, config: dict, commands: dict) -> None:
        core.write_json(
            Path(config["profile_home"]) / "dependencies" / "commands.json",
            {"schema_version": 1, "commands": commands},
        )

    def test_apply_plan_creates_symlinks_and_generated_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            project = root / "project"
            project.mkdir()

            plan = core.build_plan("init", ["ph-init"], project, config)
            self.assertTrue(plan["can_apply"])
            self.assertGreater(len(plan["create"]), 0)

            result = core.apply_plan(plan, config)
            second = core.apply_plan(plan, config)
            self.assertTrue(result["ok"])
            self.assertTrue(second["ok"])
            self.assertTrue((project / ".claude" / "commands" / "plan-prd.md").is_symlink())
            self.assertTrue((project / ".claude" / "commands" / "plan.md").is_symlink())
            self.assertTrue((project / "CLAUDE.ecc.generated.md").exists())
            self.assertFalse((project / "AGENTS.md").exists())
            self.assertFalse((project / "AGENTS.ecc.generated.md").exists())
            self.assertFalse((project / "ANTIGRAVITY.ecc.generated.md").exists())
            self.assertFalse((project / ".agent" / "workflows" / "ecc-plan-prd.md").exists())
            self.assertFalse((project / ".agents" / "rules" / "ecc-common.md").exists())
            self.assertFalse((project / ".codex" / "agents" / "ecc-planner.toml").exists())
            lock = core.read_lock(project)
            self.assertEqual(lock["initial_phase"], "ph-init")
            self.assertIn("skills/api-design", lock["components"])
            self.assertFalse(lock["enable_codex"])
            self.assertFalse(lock["enable_antigravity"])
            self.assertEqual(lock["codex_components"], {})
            self.assertEqual(lock["antigravity_components"], {})

    def test_global_init_can_also_link_project_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            project = root / "project"
            config = self.make_config(root)
            config["enable_codex"] = True
            config["enable_antigravity"] = True
            project.mkdir()
            (Path(config["ecc_home"]) / "commands" / "plan.md").write_text("plan\n", encoding="utf-8")

            with patch.object(Path, "home", return_value=home):
                result = core.global_init(config, project_path=project)
                scan = core.scan_project(project, config)

            self.assertTrue(result["ok"])
            self.assertTrue((home / ".claude" / "commands" / "ecc-plan.md").is_symlink())
            self.assertTrue((project / ".claude" / "commands" / "ecc-plan.md").is_symlink())
            self.assertTrue((project / ".agents" / "skills" / "ecc-plan" / "SKILL.md").exists())
            self.assertTrue((project / ".agents" / "workflows" / "ecc-plan.md").exists())
            self.assertTrue((project / "AGENTS.md").exists())
            self.assertTrue((project / "AGENTS.ecc.generated.md").exists())
            self.assertTrue((project / "ANTIGRAVITY.ecc.generated.md").exists())
            self.assertEqual(scan["global_plan_status"], "linked")
            self.assertEqual(scan["project_plan_status"], "linked")
            self.assertEqual(scan["codex_plan_skill_status"], "existing")
            self.assertEqual(scan["antigravity_plan_workflow_status"], "existing")

    def test_each_phase_includes_plan_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            profiles = core.load_profiles(config["profile_home"])

            for phase_id in core.PHASES:
                project = root / phase_id
                project.mkdir()
                self.populate_profile_assets(Path(config["ecc_home"]), profiles["phases"][phase_id])
                plan = core.build_plan("init", [phase_id], project, config)
                self.assertIn("plan.md", plan["required"]["commands"], phase_id)
                self.assertTrue(any(item["name"] == "plan.md" for item in plan["create"]), phase_id)

    def test_selected_clients_create_only_requested_bridge_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            config["enable_codex"] = True
            config["enable_antigravity"] = True
            project = root / "project"
            project.mkdir()

            plan = core.build_plan("init", ["ph-init"], project, config)
            result = core.apply_plan(plan, config)

            self.assertTrue(result["ok"])
            self.assertTrue((project / "AGENTS.md").exists())
            self.assertTrue((project / "AGENTS.ecc.generated.md").exists())
            self.assertTrue((project / "ANTIGRAVITY.ecc.generated.md").exists())
            self.assertTrue((project / ".agents" / "workflows" / "ecc-plan-prd.md").exists())
            self.assertTrue((project / ".agents" / "agents.md").exists())
            self.assertTrue((project / ".agents" / "rules" / "ecc-common.md").exists())
            self.assertTrue((project / ".agents" / "skills" / "ecc-plan" / "SKILL.md").exists())
            self.assertTrue((project / ".agents" / "skills" / "ecc-plan-prd" / "SKILL.md").exists())
            self.assertFalse((project / ".agents" / "skills" / "ecc-rule-common" / "SKILL.md").exists())
            self.assertTrue((project / ".codex" / "rules" / "ecc-common.md").exists())
            self.assertTrue((project / ".codex" / "agents" / "ecc-planner.toml").exists())
            self.assertTrue((project / ".agents" / "skills" / "ecc-context-budget" / "SKILL.md").exists())
            lock = core.read_lock(project)
            self.assertIn("codex/commands/plan.md", lock["codex_components"])
            self.assertIn("codex/rules/common", lock["codex_components"])
            self.assertEqual(lock["codex_components"]["codex/rules/common"]["kind"], "codex_rule")
            self.assertIn("codex/agents/planner.md", lock["codex_components"])
            self.assertIn("antigravity/agents/agents.md", lock["antigravity_components"])
            self.assertIn("antigravity/workflows/plan-prd.md", lock["antigravity_components"])
            self.assertIn("antigravity/rules/common", lock["antigravity_components"])
            antigravity_agents = (project / ".agents" / "agents.md").read_text(encoding="utf-8")
            self.assertIn(core.ANTIGRAVITY_MARKER, antigravity_agents)
            self.assertIn("Planner (@planner)", antigravity_agents)
            agents_md = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn(core.CODEX_MANAGED_BLOCK_START, agents_md)
            self.assertIn(core.ANTIGRAVITY_MANAGED_BLOCK_START, agents_md)

    def test_claude_target_can_be_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            config["enable_claude"] = False
            config["enable_codex"] = True
            config["enable_antigravity"] = True
            project = root / "project"
            project.mkdir()

            plan = core.build_plan("init", ["ph-init"], project, config)
            result = core.apply_plan(plan, config)
            lock = core.read_lock(project)

            self.assertTrue(result["ok"])
            self.assertFalse(any(item["target"].startswith(str(project / ".claude" / "commands")) for item in plan["create"]))
            self.assertFalse((project / ".claude" / "commands" / "plan.md").exists())
            self.assertFalse((project / ".claude" / "skills" / "context-budget").exists())
            self.assertFalse((project / "CLAUDE.ecc.generated.md").exists())
            self.assertTrue((project / ".ecc-manager" / "ecc-lock" / "profile.json").exists())
            self.assertFalse((project / ".claude").exists())
            self.assertTrue((project / ".agents" / "skills" / "ecc-plan" / "SKILL.md").exists())
            self.assertFalse((project / ".agents" / "skills" / "ecc-rule-common" / "SKILL.md").exists())
            self.assertTrue((project / ".codex" / "rules" / "ecc-common.md").exists())
            self.assertTrue((project / ".agents" / "skills" / "ecc-context-budget" / "SKILL.md").exists())
            self.assertTrue((project / ".agents" / "workflows" / "ecc-plan.md").exists())
            self.assertTrue((project / ".codex" / "agents" / "ecc-planner.toml").exists())
            self.assertFalse(lock["enable_claude"])

    def test_codex_target_writes_agents_md_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            config["enable_claude"] = False
            config["enable_codex"] = True
            config["enable_antigravity"] = False
            config["manage_agents_md"] = False
            project = root / "project"
            project.mkdir()

            plan = core.build_plan("init", ["ph-init"], project, config)
            result = core.apply_plan(plan, config)
            agents_md = (project / "AGENTS.md").read_text(encoding="utf-8")
            lock = core.read_lock(project)

            self.assertTrue(result["ok"])
            self.assertTrue(any(item["path"].endswith("/AGENTS.md") for item in plan["generated"]))
            self.assertIn(core.CODEX_MANAGED_BLOCK_START, agents_md)
            self.assertIn(".agents/skills", agents_md)
            self.assertIn(".codex/rules", agents_md)
            self.assertIn("$ecc-plan", agents_md)
            self.assertIn("Enabled ECC rules: common", agents_md)
            self.assertNotIn("$ecc-rule-common", agents_md)
            self.assertTrue(lock["manage_agents_md"])

    def test_codex_generated_skill_adapters_include_origin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            config["enable_claude"] = False
            config["enable_codex"] = True
            config["enable_antigravity"] = False
            project = root / "project"
            project.mkdir()

            plan = core.build_plan("init", ["ph-init"], project, config)
            result = core.apply_plan(plan, config)

            self.assertTrue(result["ok"])
            for skill_file in [
                project / ".agents" / "skills" / "ecc-plan" / "SKILL.md",
                project / ".agents" / "skills" / "ecc-context-budget" / "SKILL.md",
            ]:
                self.assertIn("origin: ECC", skill_file.read_text(encoding="utf-8"))
            self.assertFalse((project / ".agents" / "skills" / "ecc-rule-common" / "SKILL.md").exists())
            self.assertIn("ECC rule: common", (project / ".codex" / "rules" / "ecc-common.md").read_text(encoding="utf-8"))

    def test_codex_uses_skill_symlink_when_skill_has_skill_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            config["enable_codex"] = True
            ecc_home = Path(config["ecc_home"])
            (ecc_home / "skills" / "context-budget" / "SKILL.md").write_text(
                "---\nname: context-budget\ndescription: Budget context.\n---\nUse less context.\n",
                encoding="utf-8",
            )
            project = root / "project"
            project.mkdir()

            plan = core.build_plan("init", ["ph-init"], project, config)
            core.apply_plan(plan, config)

            self.assertTrue((project / ".agents" / "skills" / "context-budget").is_symlink())
            lock = core.read_lock(project)
            self.assertEqual(lock["codex_components"]["codex/skills/context-budget"]["codex_name"], "context-budget")

    def test_codex_agent_conflict_blocks_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            config["enable_codex"] = True
            project = root / "project"
            target = project / ".codex" / "agents" / "ecc-planner.toml"
            target.parent.mkdir(parents=True)
            target.write_text("user agent\n", encoding="utf-8")

            plan = core.build_plan("init", ["ph-init"], project, config)

            self.assertFalse(plan["can_apply"])
            self.assertEqual(plan["codex"]["skipped"][0]["status"], "existing_real")

    def test_agents_md_managed_block_preserves_user_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            config["enable_codex"] = True
            config["enable_antigravity"] = True
            project = root / "project"
            project.mkdir()
            (project / "AGENTS.md").write_text("# Team rules\n\nKeep this.\n", encoding="utf-8")

            plan = core.build_plan("init", ["ph-init"], project, config)
            core.apply_plan(plan, config)

            agents = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Keep this.", agents)
            self.assertIn(core.CODEX_MANAGED_BLOCK_START, agents)
            self.assertIn(core.ANTIGRAVITY_MANAGED_BLOCK_START, agents)
            self.assertIn("Enabled ECC commands", agents)

    def test_antigravity_bridge_works_without_codex(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            config["enable_codex"] = False
            config["enable_antigravity"] = True
            project = root / "project"
            project.mkdir()

            plan = core.build_plan("init", ["ph-init"], project, config)
            result = core.apply_plan(plan, config)

            self.assertTrue(result["ok"])
            self.assertFalse((project / "AGENTS.ecc.generated.md").exists())
            self.assertTrue((project / "ANTIGRAVITY.ecc.generated.md").exists())
            self.assertTrue((project / ".agents" / "workflows" / "ecc-plan-prd.md").exists())
            self.assertTrue((project / ".agents" / "rules" / "ecc-common.md").exists())
            self.assertTrue((project / ".agents" / "skills" / "ecc-context-budget" / "SKILL.md").exists())
            agents_md = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertNotIn(core.CODEX_MANAGED_BLOCK_START, agents_md)
            self.assertIn(core.ANTIGRAVITY_MANAGED_BLOCK_START, agents_md)
            self.assertIn("/ecc-plan", agents_md)
            self.assertIn(".agents/workflows", agents_md)
            self.assertNotIn(".claude/commands", agents_md)
            antigravity_report = (project / "ANTIGRAVITY.ecc.generated.md").read_text(encoding="utf-8")
            self.assertIn("/ecc-plan", antigravity_report)
            self.assertIn(".agents/workflows/ecc-plan.md", antigravity_report)
            self.assertIn("context-budget", antigravity_report)
            self.assertNotIn(".claude/commands", antigravity_report)
            rule_text = (project / ".agents" / "rules" / "ecc-common.md").read_text(encoding="utf-8")
            self.assertIn("description:", rule_text)
            self.assertIn("alwaysApply: true", rule_text)
            workflow_text = (project / ".agents" / "workflows" / "ecc-plan.md").read_text(encoding="utf-8")
            self.assertIn("description:", workflow_text)
            self.assertIn("# ECC Workflow: /ecc-plan", workflow_text)
            lock = core.read_lock(project)
            self.assertFalse(lock["enable_codex"])
            self.assertIn("antigravity/skills/context-budget", lock["antigravity_components"])

    def test_codex_and_antigravity_share_workspace_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            config["enable_claude"] = False
            config["enable_codex"] = True
            config["enable_antigravity"] = True
            project = root / "project"
            project.mkdir()

            plan = core.build_plan("init", ["ph-init"], project, config)
            result = core.apply_plan(plan, config)
            lock = core.read_lock(project)

            self.assertTrue(result["ok"])
            self.assertTrue((project / ".agents" / "skills" / "ecc-context-budget" / "SKILL.md").exists())
            self.assertIn("codex/skills/context-budget", lock["codex_components"])
            self.assertNotIn("antigravity/skills/context-budget", lock["antigravity_components"])
            antigravity_report = (project / "ANTIGRAVITY.ecc.generated.md").read_text(encoding="utf-8")
            self.assertIn("ecc-context-budget", antigravity_report)
            self.assertIn("/ecc-plan", antigravity_report)
            self.assertNotIn(".claude/commands", antigravity_report)

    def test_antigravity_rule_and_workflow_are_truncated_to_document_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            config["enable_codex"] = False
            config["enable_antigravity"] = True
            ecc_home = Path(config["ecc_home"])
            (ecc_home / "commands" / "plan.md").write_text("x" * 14000, encoding="utf-8")
            (ecc_home / "rules" / "common" / "README.md").write_text("y" * 14000, encoding="utf-8")
            project = root / "project"
            project.mkdir()

            plan = core.build_plan("init", ["ph-init"], project, config)
            core.apply_plan(plan, config)

            workflow_text = (project / ".agents" / "workflows" / "ecc-plan.md").read_text(encoding="utf-8")
            rule_text = (project / ".agents" / "rules" / "ecc-common.md").read_text(encoding="utf-8")
            self.assertLessEqual(len(workflow_text), core.ANTIGRAVITY_FILE_CHAR_LIMIT)
            self.assertLessEqual(len(rule_text), core.ANTIGRAVITY_FILE_CHAR_LIMIT)
            self.assertIn("Truncated by ecc-manager", workflow_text)
            self.assertIn("Truncated by ecc-manager", rule_text)

    def test_antigravity_workflow_conflict_blocks_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            config["enable_antigravity"] = True
            project = root / "project"
            target = project / ".agents" / "workflows" / "ecc-plan-prd.md"
            target.parent.mkdir(parents=True)
            target.write_text("user workflow\n", encoding="utf-8")

            plan = core.build_plan("init", ["ph-init"], project, config)

            self.assertFalse(plan["can_apply"])
            self.assertTrue(any(item["status"] == "existing_real" for item in plan["antigravity"]["skipped"]))

    def test_doctor_reports_unmanaged_codex_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            config["enable_codex"] = True
            project = root / "project"
            project.mkdir()

            plan = core.build_plan("init", ["ph-init"], project, config)
            core.apply_plan(plan, config)
            rogue = project / ".codex" / "agents" / "rogue.toml"
            rogue.write_text("name = \"rogue\"\n", encoding="utf-8")

            result = core.doctor(project, fix=False, config=config)
            unmanaged = [item for item in result["checks"] if item["name"] == "未记录的 Codex 产物"]

            self.assertTrue(any("rogue.toml" in item["message"] for item in unmanaged))

    def test_doctor_reports_obsolete_codex_command_adapters_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            config["enable_claude"] = False
            config["enable_codex"] = True
            project = root / "project"
            project.mkdir()
            obsolete_command = project / ".codex" / "commands" / "ecc-plan.md"
            obsolete_rule = project / ".codex" / "rules" / "ecc-common.md"
            obsolete_command.parent.mkdir(parents=True, exist_ok=True)
            obsolete_rule.parent.mkdir(parents=True, exist_ok=True)
            obsolete_command.write_text(core.CODEX_AGENT_MARKER + "\nold command\n", encoding="utf-8")
            obsolete_rule.write_text(core.CODEX_AGENT_MARKER + "\nold rule\n", encoding="utf-8")

            scan = core.scan_project(project, config)
            result = core.doctor(project, fix=False, config=config)

            self.assertEqual(scan["obsolete_codex_artifacts"], [
                ".codex/commands/ecc-plan.md",
            ])
            warnings = [item for item in result["checks"] if item["name"] == "旧版 Codex command 产物"]
            self.assertEqual(len(warnings), 1)
            self.assertTrue(warnings[0]["message"].startswith(".codex/commands"))

    def test_doctor_reports_legacy_antigravity_workflows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            config["enable_antigravity"] = True
            project = root / "project"
            project.mkdir()

            plan = core.build_plan("init", ["ph-init"], project, config)
            core.apply_plan(plan, config)
            legacy = project / ".agent" / "workflows" / "old-plan.md"
            legacy.parent.mkdir(parents=True)
            legacy.write_text("old workflow\n", encoding="utf-8")

            result = core.doctor(project, fix=False, config=config)
            unmanaged = [item for item in result["checks"] if item["name"] == "未记录的 Antigravity 产物"]

            self.assertTrue(any(".agent/workflows/old-plan.md" in item["message"] for item in unmanaged))

    def test_build_plan_blocks_target_conflicts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            config["enable_codex"] = True
            config["enable_antigravity"] = True
            project = root / "project"
            project.mkdir()
            target = project / ".claude" / "commands" / "plan-prd.md"
            target.parent.mkdir(parents=True)
            target.write_text("user file\n", encoding="utf-8")

            plan = core.build_plan("init", ["ph-init"], project, config)

            self.assertFalse(plan["can_apply"])
            self.assertEqual(plan["skipped"][0]["status"], "existing_real")

    def test_apply_plan_rejects_paths_outside_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            config["enable_codex"] = True
            config["enable_antigravity"] = True
            project = root / "project"
            project.mkdir()
            source = root / "ecc" / "commands" / "plan-prd.md"
            plan = {
                "project": str(project),
                "profiles": ["ph-init"],
                "create": [
                    {
                        "kind": "command",
                        "component": "commands/plan-prd.md",
                        "name": "plan-prd.md",
                        "source": str(source),
                        "target": str(root / "outside.md"),
                        "required_by": ["ph-init"],
                    }
                ],
                "existing_ok": [],
                "skipped": [],
                "missing": [],
                "runtime": {},
                "codex": {
                    "write": [
                        {
                            "kind": "codex_agent",
                            "component": "codex/agents/planner.md",
                            "name": "planner.md",
                            "source": str(root / "ecc" / "agents" / "planner.md"),
                            "target": str(root / "outside.toml"),
                            "status": "generate_file",
                            "required_by": ["ph-init"],
                            "content": core.CODEX_AGENT_MARKER,
                        }
                    ],
                    "existing_ok": [],
                    "skipped": [],
                    "missing": [],
                    "generated": [],
                },
            }

            with self.assertRaises(ValueError):
                core.apply_plan(plan, config)

    def test_apply_plan_rejects_codex_paths_outside_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            config["enable_codex"] = True
            config["enable_antigravity"] = True
            project = root / "project"
            project.mkdir()
            plan = {
                "project": str(project),
                "profiles": ["ph-init"],
                "create": [],
                "existing_ok": [],
                "skipped": [],
                "missing": [],
                "runtime": {},
                "codex": {
                    "write": [
                        {
                            "kind": "codex_agent",
                            "component": "codex/agents/planner.md",
                            "name": "planner.md",
                            "source": str(root / "ecc" / "agents" / "planner.md"),
                            "target": str(root / "outside.toml"),
                            "status": "generate_file",
                            "required_by": ["ph-init"],
                            "content": core.CODEX_AGENT_MARKER,
                        }
                    ],
                    "existing_ok": [],
                    "skipped": [],
                    "missing": [],
                    "generated": [],
                },
            }

            with self.assertRaises(ValueError):
                core.apply_plan(plan, config)

    def test_apply_plan_rejects_antigravity_paths_outside_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            project = root / "project"
            project.mkdir()
            plan = {
                "project": str(project),
                "profiles": ["ph-init"],
                "create": [],
                "existing_ok": [],
                "skipped": [],
                "missing": [],
                "runtime": {},
                "codex": {},
                "antigravity": {
                    "write": [
                        {
                            "kind": "antigravity_workflow",
                            "component": "antigravity/workflows/plan-prd.md",
                            "name": "plan-prd.md",
                            "source": str(root / "ecc" / "commands" / "plan-prd.md"),
                            "target": str(root / "outside.md"),
                            "status": "generate_file",
                            "required_by": ["ph-init"],
                            "content": core.ANTIGRAVITY_MARKER,
                        }
                    ],
                    "existing_ok": [],
                    "skipped": [],
                    "missing": [],
                    "generated": [],
                },
            }

            with self.assertRaises(ValueError):
                core.apply_plan(plan, config)

    def test_generated_claude_reference_uses_configured_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            config["generated_claude_file"] = "CUSTOM.generated.md"
            project = root / "project"
            project.mkdir()
            plan = core.build_plan("init", ["ph-init"], project, config)

            core.apply_plan(plan, config)

            generated = project / "CUSTOM.generated.md"
            self.assertIn("@CUSTOM.generated.md", generated.read_text(encoding="utf-8"))

    def test_asset_summary_reads_body_after_frontmatter(self) -> None:
        raw = "---\nname: demo\ndescription: Demo skill\n---\n# Body Title\nFastAPI review testing\n"

        summary = core._asset_summary_text(raw)

        self.assertIn("description: Demo skill", summary)
        self.assertIn("# Body Title", summary)
        self.assertIn("FastAPI review testing", summary)

    def test_common_ecc_packs_cover_daily_workflows(self) -> None:
        expected = {
            "prp-workflow-pack": "prp-implement.md",
            "github-pr-pack": "review-pr.md",
            "session-memory-pack": "save-session.md",
            "continuous-learning-pack": "learn.md",
            "ops-runtime-pack": "pm2.md",
            "ecc-governance-pack": "skill-health.md",
            "language-python-pack": "python-review.md",
            "language-cpp-pack": "cpp-review.md",
            "language-go-pack": "go-review.md",
            "language-rust-pack": "rust-review.md",
            "language-flutter-dart-pack": "flutter-review.md",
            "language-kotlin-pack": "kotlin-review.md",
        }

        for pack_id, command_name in expected.items():
            self.assertIn(pack_id, PACKS)
            self.assertIn(command_name, PACKS[pack_id]["required"]["commands"])

    def test_command_registry_dependencies_are_used_as_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            project = root / "project"
            project.mkdir()
            ecc_home = Path(config["ecc_home"])
            self.write_asset(ecc_home, "commands", "python-review.md")
            self.write_asset(ecc_home, "skills", "python-patterns")
            self.write_asset(ecc_home, "agents", "python-reviewer.md")
            self.write_pack(config, {
                "schema_version": 1,
                "id": "python-registry-pack",
                "type": "pack",
                "name_zh": "Python Registry",
                "description_zh": "Registry-backed command dependencies",
                "required": {"commands": ["python-review.md"], "skills": [], "agents": [], "rules": []},
                "optional": {},
            })
            core.write_json(ecc_home / "docs" / "COMMAND-REGISTRY.json", {
                "schemaVersion": 1,
                "commands": [
                    {
                        "command": "python-review",
                        "path": "commands/python-review.md",
                        "skills": ["python-patterns"],
                        "allAgents": ["python-reviewer"],
                    }
                ],
            })

            contracts = core.load_command_contracts(core.paths_from_config(config), config["profile_home"])

            self.assertEqual(contracts["python-review.md"]["source"], "registry")
            dependency = contracts["python-review.md"]["dependency"]
            self.assertIn("python-patterns", dependency["required"]["skills"])
            self.assertIn("python-reviewer.md", dependency["required"]["agents"])

            plan = core.build_plan("add", ["python-registry-pack"], project, config)

            self.assertTrue(plan["can_apply"])
            self.assertIn("python-patterns", plan["required"]["skills"])
            self.assertIn("python-reviewer.md", plan["required"]["agents"])
            self.assertTrue(any(item["component"] == "skills/python-patterns" for item in plan["create"]))
            self.assertTrue(any(item["component"] == "agents/python-reviewer.md" for item in plan["create"]))

    def test_ecc_manifest_metadata_reports_supported_and_missing_states(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            ecc_home = Path(config["ecc_home"])
            (ecc_home / "VERSION").write_text("2.0.0-rc.1\n", encoding="utf-8")
            core.write_json(ecc_home / "manifests" / "install-profiles.json", {"version": 1, "profiles": {"core": {}}})
            core.write_json(ecc_home / "manifests" / "install-modules.json", {"version": 1, "modules": []})
            core.write_json(ecc_home / "manifests" / "install-components.json", {"version": 1, "components": []})
            core.write_json(ecc_home / "config" / "project-stack-mappings.json", {"version": 1, "stacks": []})
            core.write_json(ecc_home / "docs" / "COMMAND-REGISTRY.json", {"schemaVersion": 1, "commands": []})

            metadata = core.ecc_manifest_metadata(core.paths_from_config(config))
            self.assertEqual(metadata["status"], "supported")

            (ecc_home / "VERSION").write_text("9.9.9\n", encoding="utf-8")
            metadata = core.ecc_manifest_metadata(core.paths_from_config(config))
            self.assertEqual(metadata["status"], "unsupported_version")

    def test_apply_plan_returns_task_run_with_completion_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            project = root / "project"
            project.mkdir()

            plan = core.build_plan("init", ["ph-init"], project, config)
            result = core.apply_plan(plan, config)
            task_run = result["task_run"]

            self.assertEqual(task_run["goal"], "初始化项目能力：项目初期")
            self.assertEqual(task_run["status"], "completed_with_warnings")
            criteria = {item["id"]: item for item in task_run["verification"]["criteria"]}
            self.assertEqual(criteria["sources_available"]["status"], "pass")
            self.assertEqual(criteria["required_symlinks"]["status"], "pass")
            self.assertEqual(criteria["lock_written"]["status"], "pass")
            self.assertEqual(criteria["generated_written"]["status"], "pass")
            self.assertEqual(criteria["command_health"]["status"], "warning")
            self.assertEqual(criteria["codex_bridge"]["status"], "pass")
            self.assertEqual(criteria["antigravity_bridge"]["status"], "pass")
            self.assertTrue(task_run["next_commands"])
            self.assertIn("/plan-prd", task_run["next_commands"])
            self.assertTrue(any("CLAUDE.md" in item["message"] for item in task_run["next_actions"]))
            self.assertTrue(task_run["issues"])
            self.assertTrue(all(item.get("actions") for item in task_run["issues"]))

    def test_apply_plan_records_task_history_in_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            project = root / "project"
            project.mkdir()

            plan = core.build_plan("init", ["ph-init"], project, config)
            result = core.apply_plan(plan, config)
            lock = core.read_lock(project)

            self.assertEqual(lock["last_task_run"]["id"], result["task_run"]["id"])
            self.assertEqual(lock["task_history"][-1]["id"], result["task_run"]["id"])
            self.assertEqual(lock["task_history"][-1]["status"], "completed_with_warnings")

    def test_remove_profile_uses_reference_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            config["enable_codex"] = True
            config["enable_antigravity"] = True
            project = root / "project"
            project.mkdir()

            plan = core.build_plan("init", ["ph-init"], project, config)
            core.apply_plan(plan, config)
            removed = core.remove_profile("ph-init", project)

            self.assertTrue(removed["ok"])
            self.assertIn("commands/plan-prd.md", removed["removed"])
            self.assertIn("codex/agents/planner.md", removed["removed"])
            self.assertIn("antigravity/workflows/plan-prd.md", removed["removed"])
            self.assertIn("antigravity/rules/common", removed["removed"])
            self.assertFalse((project / ".claude" / "commands" / "plan-prd.md").exists())
            self.assertFalse((project / ".codex" / "agents" / "ecc-planner.toml").exists())
            self.assertFalse((project / ".agent" / "workflows" / "ecc-plan-prd.md").exists())
            self.assertFalse((project / ".agents" / "rules" / "ecc-common.md").exists())

    def test_remove_profile_preserves_real_files_in_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            config["enable_codex"] = True
            config["enable_antigravity"] = True
            project = root / "project"
            project.mkdir()

            plan = core.build_plan("init", ["ph-init"], project, config)
            core.apply_plan(plan, config)

            command_target = project / ".claude" / "commands" / "plan-prd.md"
            if command_target.is_symlink():
                command_target.unlink()
            command_target.write_text("user file\n", encoding="utf-8")

            codex_target = project / ".codex" / "agents" / "ecc-planner.toml"
            if codex_target.is_symlink():
                codex_target.unlink()
            codex_target.write_text("user toml\n", encoding="utf-8")

            antigravity_target = project / ".agents" / "workflows" / "ecc-plan-prd.md"
            antigravity_target.write_text("user workflow\n", encoding="utf-8")

            removed = core.remove_profile("ph-init", project)
            lock = core.read_lock(project)

            self.assertTrue(removed["ok"])
            self.assertIn("commands/plan-prd.md", removed["kept"])
            self.assertIn("codex/agents/planner.md", removed["kept"])
            self.assertIn("antigravity/workflows/plan-prd.md", removed["kept"])
            self.assertIn("commands/plan-prd.md", lock["components"])
            self.assertIn("codex/agents/planner.md", lock["codex_components"])
            self.assertIn("antigravity/workflows/plan-prd.md", lock["antigravity_components"])
            self.assertTrue(command_target.exists())
            self.assertFalse(command_target.is_symlink())
            self.assertTrue(codex_target.exists())
            self.assertFalse(codex_target.is_symlink())
            self.assertTrue(antigravity_target.exists())

    def test_multi_model_plan_records_runtime_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            project = root / "project"
            project.mkdir()
            commands = root / "ecc" / "commands"
            for name in ["multi-plan.md", "multi-execute.md", "multi-backend.md", "multi-frontend.md", "multi-workflow.md"]:
                (commands / name).write_text("test\n", encoding="utf-8")

            plan = core.build_plan("add", ["multi-model-planning-pack"], project, config)

            self.assertTrue(plan["can_apply"])
            self.assertTrue(plan["requires_confirmation"])
            self.assertIn("ccg-workflow", plan["required"]["runtime"])
            self.assertEqual(plan["runtime"]["external_required"][0]["name"], "ccg-workflow")
            health = {item["name"]: item for item in plan["command_health"]["commands"]}
            self.assertEqual(health["multi-plan.md"]["status"], "needs_confirmation")
            self.assertTrue(any(issue["id"].endswith("needs_confirmation") for issue in plan["issues"]))

    def test_required_command_dependency_blocks_plan_when_source_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            project = root / "project"
            project.mkdir()
            ecc_home = Path(config["ecc_home"])
            self.write_asset(ecc_home, "commands", "custom.md")
            self.write_asset(ecc_home, "skills", "optional-skill")
            self.write_pack(config, {
                "schema_version": 1,
                "id": "custom-command-pack",
                "type": "pack",
                "name_zh": "Custom",
                "description_zh": "Custom command",
                "required": {"commands": ["custom.md"], "skills": [], "agents": [], "rules": []},
                "optional": {},
            })
            self.write_command_dependencies(config, {
                "custom.md": {
                    "required": {"skills": ["required-skill"]},
                    "optional": {},
                }
            })

            plan = core.build_plan("add", ["custom-command-pack"], project, config)

            self.assertFalse(plan["can_apply"])
            self.assertIn("required-skill", plan["required"]["skills"])
            self.assertTrue(any(item["component"] == "skills/required-skill" for item in plan["missing"]))
            self.assertEqual(plan["command_health"]["commands"][0]["status"], "blocked")
            self.assertEqual(plan["command_health"]["commands"][0]["required_missing"][0]["name"], "required-skill")
            blocked_issue = next(issue for issue in plan["issues"] if issue["id"].endswith("blocked"))
            self.assertEqual(blocked_issue["level"], "error")
            self.assertTrue(blocked_issue["actions"])

    def test_required_command_dependency_is_added_to_install_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            project = root / "project"
            project.mkdir()
            ecc_home = Path(config["ecc_home"])
            self.write_asset(ecc_home, "commands", "custom.md")
            self.write_asset(ecc_home, "skills", "required-skill")
            self.write_asset(ecc_home, "agents", "required-agent.md")
            self.write_pack(config, {
                "schema_version": 1,
                "id": "custom-command-pack",
                "type": "pack",
                "name_zh": "Custom",
                "description_zh": "Custom command",
                "required": {"commands": ["custom.md"], "skills": [], "agents": [], "rules": []},
                "optional": {},
            })
            self.write_command_dependencies(config, {
                "custom.md": {
                    "required": {"skills": ["required-skill"], "agents": ["required-agent.md"]},
                    "optional": {},
                }
            })

            plan = core.build_plan("add", ["custom-command-pack"], project, config)

            self.assertTrue(plan["can_apply"])
            self.assertEqual(plan["command_health"]["commands"][0]["status"], "ready")
            self.assertIn("required-skill", plan["required"]["skills"])
            self.assertIn("required-agent.md", plan["required"]["agents"])
            self.assertIn("custom-command-pack via custom.md", plan["required"]["skills"]["required-skill"])
            self.assertTrue(any(item["component"] == "skills/required-skill" for item in plan["create"]))
            self.assertTrue(any(item["component"] == "agents/required-agent.md" for item in plan["create"]))

    def test_frontmatter_command_contract_is_primary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            project = root / "project"
            project.mkdir()
            ecc_home = Path(config["ecc_home"])
            self.write_asset(
                ecc_home,
                "commands",
                "frontmatter.md",
                "---\ndescription: test\nrequires:\n  skills:\n    - required-skill\noptional:\n  agents:\n    - optional-agent.md\n---\n# Command\n",
            )
            self.write_asset(ecc_home, "skills", "required-skill")
            self.write_pack(config, {
                "schema_version": 1,
                "id": "frontmatter-pack",
                "type": "pack",
                "name_zh": "Frontmatter",
                "description_zh": "Command contract",
                "required": {"commands": ["frontmatter.md"], "skills": ["required-skill"], "agents": [], "rules": []},
                "optional": {},
            })
            self.write_command_dependencies(config, {
                "frontmatter.md": {
                    "required": {"skills": ["legacy-skill"]},
                    "optional": {},
                }
            })

            plan = core.build_plan("add", ["frontmatter-pack"], project, config)

            self.assertTrue(plan["can_apply"])
            health = plan["command_health"]["commands"][0]
            self.assertEqual(health["contract_source"], "frontmatter")
            self.assertEqual(health["status"], "degraded")
            self.assertEqual(health["optional_pending"][0]["name"], "optional-agent.md")
            self.assertNotIn("legacy-skill", plan["required"]["skills"])

    def test_optional_command_dependency_marks_degraded_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            project = root / "project"
            project.mkdir()
            ecc_home = Path(config["ecc_home"])
            self.write_asset(ecc_home, "commands", "custom.md")
            self.write_asset(ecc_home, "skills", "optional-skill")
            self.write_pack(config, {
                "schema_version": 1,
                "id": "optional-command-pack",
                "type": "pack",
                "name_zh": "Optional",
                "description_zh": "Optional command",
                "required": {"commands": ["custom.md"], "skills": [], "agents": [], "rules": []},
                "optional": {},
            })
            self.write_command_dependencies(config, {
                "custom.md": {
                    "required": {},
                    "optional": {"skills": ["optional-skill"]},
                }
            })

            plan = core.build_plan("add", ["optional-command-pack"], project, config)

            self.assertTrue(plan["can_apply"])
            self.assertTrue(plan["requires_confirmation"])
            self.assertIn("optional-skill", plan["optional"]["skills"])
            self.assertEqual(plan["command_health"]["commands"][0]["status"], "degraded")
            self.assertEqual(plan["command_health"]["commands"][0]["optional_pending"][0]["name"], "optional-skill")
            degraded_issue = next(issue for issue in plan["issues"] if issue["id"].endswith("degraded"))
            self.assertEqual(degraded_issue["level"], "warning")
            self.assertTrue(any(action["kind"] == "preview_full_config" for action in degraded_issue["actions"]))

            result = core.apply_plan(plan, config)
            self.assertTrue(result["ok"])
            lock = core.read_lock(project)
            self.assertEqual(lock["command_health"]["commands"][0]["status"], "degraded")

            full_plan = core.build_plan("add", ["optional-command-pack"], project, config, include_optional=True)
            self.assertTrue(full_plan["include_optional"])
            self.assertIn("optional-skill", full_plan["required"]["skills"])
            self.assertNotIn("optional-skill", full_plan["optional"]["skills"])
            self.assertEqual(full_plan["command_health"]["commands"][0]["status"], "ready")
            self.assertFalse(any(issue["id"].endswith("degraded") for issue in full_plan["issues"]))

    def test_inferred_command_relations_do_not_drive_install_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            project = root / "project"
            project.mkdir()
            ecc_home = Path(config["ecc_home"])
            self.write_asset(
                ecc_home,
                "commands",
                "mentions.md",
                "# Mentions\nInvoke the `reviewer` agent.\n\n## Related\n- Skill: `mentioned-skill`\n",
            )
            self.write_asset(ecc_home, "skills", "mentioned-skill")
            self.write_asset(ecc_home, "agents", "reviewer.md", "---\nname: reviewer\n---\n")
            self.write_pack(config, {
                "schema_version": 1,
                "id": "mentions-pack",
                "type": "pack",
                "name_zh": "Mentions",
                "description_zh": "Mentions relations without manifest dependencies",
                "required": {"commands": ["mentions.md"], "skills": [], "agents": [], "rules": []},
                "optional": {},
            })
            self.write_command_dependencies(config, {})

            plan = core.build_plan("add", ["mentions-pack"], project, config)

            self.assertTrue(plan["can_apply"])
            self.assertNotIn("mentioned-skill", plan["required"]["skills"])
            self.assertNotIn("reviewer.md", plan["required"]["agents"])
            self.assertEqual(plan["command_health"]["commands"][0]["status"], "unknown")

            inventory = core.asset_inventory(config)
            contract = next(item for item in inventory["command_contracts"] if item["command"] == "mentions.md")
            self.assertEqual(contract["health"], "unknown")
            candidate_names = {item["name"] for item in contract["candidates"]}
            self.assertIn("mentioned-skill", candidate_names)
            self.assertIn("reviewer.md", candidate_names)

    def test_save_config_persists_user_selected_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old_app_config = core.APP_CONFIG_PATH
            core.APP_CONFIG_PATH = root / "app-config.json"
            try:
                config = core.save_config({
                    "ecc_home": str(root / "ecc-home"),
                    "profile_home": str(root / "profiles-home"),
                    "generated_codex_file": "CODEx.generated.md",
                    "generated_antigravity_file": "ANT.generated.md",
                    "enable_claude": False,
                    "enable_codex": False,
                    "enable_antigravity": False,
                    "manage_agents_md": False,
                })

                profile_config = core.read_json(root / "profiles-home" / "ecc-use.config.json")
                app_config = core.read_json(root / "app-config.json")
            finally:
                core.APP_CONFIG_PATH = old_app_config

        self.assertEqual(config["ecc_home"], str((root / "ecc-home").resolve()))
        self.assertEqual(config["profile_home"], str((root / "profiles-home").resolve()))
        self.assertEqual(config["generated_codex_file"], "CODEx.generated.md")
        self.assertEqual(config["generated_antigravity_file"], "ANT.generated.md")
        self.assertFalse(config["enable_claude"])
        self.assertFalse(config["enable_codex"])
        self.assertFalse(config["enable_antigravity"])
        self.assertFalse(config["manage_agents_md"])
        self.assertEqual(profile_config["ecc_home"], str((root / "ecc-home").resolve()))
        self.assertEqual(app_config["profile_home"], str((root / "profiles-home").resolve()))

    def test_architecture_presets_are_separate_profile_group(self) -> None:
        expected = [
            "arch-web-saas-next-postgres",
            "arch-ai-agent-fastapi-web",
            "arch-crawler-data-platform",
            "arch-browser-extension-with-api",
            "arch-devops-automation-platform",
        ]

        for profile_id in expected:
            self.assertIn(profile_id, ARCHITECTURES)
            self.assertNotIn(profile_id, PROJECT_TYPES)
            self.assertEqual(ARCHITECTURES[profile_id].get("type"), "architecture")

    def test_legacy_architecture_project_type_files_load_as_architectures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            legacy = dict(ARCHITECTURES["arch-web-saas-next-postgres"])
            legacy["type"] = "project-type"
            core.write_json(Path(config["profile_home"]) / "project-types" / "arch-web-saas-next-postgres.json", legacy)

            profiles = core.load_profiles(config["profile_home"])

        self.assertIn("arch-web-saas-next-postgres", profiles["architectures"])
        self.assertNotIn("arch-web-saas-next-postgres", profiles["project-types"])
        self.assertEqual(profiles["architectures"]["arch-web-saas-next-postgres"]["type"], "architecture")

    def test_architecture_presets_build_applicable_plans(self) -> None:
        architecture_ids = [
            profile_id
            for profile_id, profile in ARCHITECTURES.items()
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = dict(DEFAULT_CONFIG)
            config["ecc_home"] = str(root / "ecc")
            config["profile_home"] = str(root / "profiles")
            project = root / "project"
            project.mkdir()
            self.populate_required_assets(root / "ecc", architecture_ids + ["api-python-fastapi"])

            for profile_id in architecture_ids:
                plan = core.build_plan("init", [profile_id], project, config)
                self.assertTrue(plan["can_apply"], profile_id)

            architecture_only = core.build_plan("init", ["arch-ai-agent-fastapi-web"], project, config)
            self.assertIn("fastapi-patterns", architecture_only["required"]["skills"])
            self.assertEqual(architecture_only["required"]["skills"]["fastapi-patterns"], ["arch-ai-agent-fastapi-web"])

            combined = core.build_plan(
                "init",
                ["arch-ai-agent-fastapi-web", "api-python-fastapi"],
                project,
                config,
            )
            self.assertTrue(combined["can_apply"])
            owners = combined["required"]["skills"]["fastapi-patterns"]
            self.assertIn("arch-ai-agent-fastapi-web", owners)
            self.assertIn("api-python-fastapi", owners)

            result = core.apply_plan(combined, config)
            self.assertTrue(result["ok"])
            lock = core.read_lock(project)
            self.assertEqual(lock["architecture"], "arch-ai-agent-fastapi-web")
            self.assertIn("api-python-fastapi", lock["project_types"])

    def test_build_plan_rejects_multiple_architectures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            project = root / "project"
            project.mkdir()
            self.populate_required_assets(root / "ecc", ["arch-web-saas-next-postgres", "arch-ai-agent-fastapi-web"])

            with self.assertRaises(ValueError):
                core.build_plan(
                    "init",
                    ["arch-web-saas-next-postgres", "arch-ai-agent-fastapi-web"],
                    project,
                    config,
                )

    def test_asset_inventory_reports_coverage_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            self.populate_all_default_assets(root / "ecc")
            extra_skill = root / "ecc" / "skills" / "unassigned-skill"
            extra_skill.mkdir(parents=True)
            (extra_skill / "SKILL.md").write_text("test\n", encoding="utf-8")
            extra_command = root / "ecc" / "commands" / "unassigned.md"
            extra_command.write_text("test\n", encoding="utf-8")
            review_command = root / "ecc" / "commands" / "github-review-extra.md"
            review_command.write_text("# Review PR\nReview a GitHub pull request and run tests.\n", encoding="utf-8")

            inventory = core.asset_inventory(config)

        self.assertGreaterEqual(inventory["totals"]["covered"], 1)
        self.assertIn(
            "unassigned.md",
            [item["name"] for item in inventory["groups"]["commands"]["items"] if item["status"] == "unassigned"],
        )
        self.assertIn(
            "unassigned-skill",
            [item["name"] for item in inventory["groups"]["skills"]["items"] if item["status"] == "unassigned"],
        )
        self.assertEqual(inventory["totals"]["missing_references"], 0)
        self.assertIn("sync", inventory)
        self.assertIn("suggestions", inventory)
        self.assertIn("command_contracts", inventory)
        self.assertIn("profile_health", inventory)
        self.assertGreaterEqual(inventory["sync"]["command_contracts"]["total"], 1)
        review_item = next(
            item for item in inventory["groups"]["commands"]["items"] if item["name"] == "github-review-extra.md"
        )
        category_ids = {category["id"] for category in review_item["categories"]}
        self.assertIn("github-project-ops", category_ids)
        self.assertIn("quality-review-testing", category_ids)
        classified_names = {
            item["name"]
            for category in inventory["classification"]["categories"]
            for item in category["items"]
        }
        self.assertIn("github-review-extra.md", classified_names)

    def test_profile_health_reports_missing_profile_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            self.write_pack(config, {
                "schema_version": 1,
                "id": "broken-pack",
                "type": "pack",
                "name_zh": "Broken",
                "description_zh": "Broken profile reference",
                "required": {"commands": ["missing-command.md"], "skills": [], "agents": [], "rules": []},
                "optional": {},
            })

            inventory = core.asset_inventory(config)

        broken = next(item for item in inventory["profile_health"] if item["profile_id"] == "broken-pack")
        self.assertEqual(broken["status"], "missing_references")
        self.assertEqual(broken["missing"][0]["component"], "commands/missing-command.md")

    def test_asset_inventory_reports_missing_command_dependency_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            ecc_home = Path(config["ecc_home"])
            self.write_asset(ecc_home, "commands", "custom.md")
            self.write_pack(config, {
                "schema_version": 1,
                "id": "custom-command-pack",
                "type": "pack",
                "name_zh": "Custom",
                "description_zh": "Custom command",
                "required": {"commands": ["custom.md"], "skills": [], "agents": [], "rules": []},
                "optional": {},
            })
            self.write_command_dependencies(config, {
                "custom.md": {
                    "required": {"skills": ["required-skill"], "agents": ["required-agent.md"]},
                    "optional": {},
                }
            })

            inventory = core.asset_inventory(config)

        broken = next(item for item in inventory["profile_health"] if item["profile_id"] == "custom-command-pack")
        missing_components = {item["component"] for item in broken["missing"]}
        self.assertEqual(broken["status"], "missing_references")
        self.assertIn("skills/required-skill", missing_components)
        self.assertIn("agents/required-agent.md", missing_components)
        self.assertIn("required-skill", [item["name"] for item in inventory["groups"]["skills"]["missing"]])
        self.assertIn("required-agent.md", [item["name"] for item in inventory["groups"]["agents"]["missing"]])
        self.assertTrue(any(item["name"] == "required-skill" for item in inventory["missing_references"]))

    def test_apply_command_dependency_suggestion_writes_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            ecc_home = Path(config["ecc_home"])
            self.write_asset(ecc_home, "commands", "candidate.md", "# Candidate\n\n## Related\n- Skill: `candidate-skill`\n")
            self.write_asset(ecc_home, "skills", "candidate-skill")

            result = core.apply_ecc_suggestions([
                {
                    "action": "confirm_command_dependency",
                    "target_id": "candidate.md",
                    "dependency_kind": "skills",
                    "dependency_name": "candidate-skill",
                    "level": "required",
                }
            ], config)

            self.assertEqual(len(result["applied"]), 1)
            raw = (ecc_home / "commands" / "candidate.md").read_text(encoding="utf-8")
            self.assertIn("requires:", raw)
            self.assertIn("candidate-skill", raw)
            contracts = core.load_command_contracts(core.paths_from_config(config), config["profile_home"])
            self.assertEqual(contracts["candidate.md"]["source"], "frontmatter")
            self.assertIn("candidate-skill", contracts["candidate.md"]["dependency"]["required"]["skills"])

    def test_command_dependency_can_move_from_required_to_optional(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            ecc_home = Path(config["ecc_home"])
            self.write_asset(
                ecc_home,
                "commands",
                "candidate.md",
                "---\nrequires:\n  skills:\n    - candidate-skill\noptional:\n  skills: []\n---\n# Candidate\n",
            )

            result = core.write_command_contract_dependency(
                core.paths_from_config(config),
                "candidate.md",
                "optional",
                "skills",
                "candidate-skill",
            )

            self.assertTrue(result["ok"])
            _declared, dependency = core.parse_command_frontmatter_dependency(
                (ecc_home / "commands" / "candidate.md").read_text(encoding="utf-8")
            )
            self.assertNotIn("candidate-skill", dependency["required"]["skills"])
            self.assertIn("candidate-skill", dependency["optional"]["skills"])

    def test_inline_frontmatter_map_dependencies_are_parsed(self) -> None:
        raw = (
            "---\n"
            "requires: {skills: [required-skill, second-skill], agents: [required-agent.md]}\n"
            "optional: {commands: [helper.md], mcp: [ace-tool]}\n"
            "---\n"
            "# Command\n"
        )

        declared, dependency = core.parse_command_frontmatter_dependency(raw)

        self.assertTrue(declared)
        self.assertEqual(dependency["required"]["skills"], ["required-skill", "second-skill"])
        self.assertEqual(dependency["required"]["agents"], ["required-agent.md"])
        self.assertEqual(dependency["optional"]["commands"], ["helper.md"])
        self.assertEqual(dependency["optional"]["mcp"], ["ace-tool"])

    def test_remove_profile_cleans_stale_lock_entries_when_target_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            project = root / "project"
            project.mkdir()
            lock = core.default_lock(config)
            lock["initial_phase"] = "ph-init"
            lock["components"] = {
                "commands/stale.md": {
                    "managed": True,
                    "kind": "command",
                    "source": str(root / "ecc" / "commands" / "stale.md"),
                    "target": ".claude/commands/stale.md",
                    "required_by": ["ph-init"],
                }
            }
            core.write_json(core.lock_path(project), lock)

            result = core.remove_profile("ph-init", project)
            updated = core.read_lock(project)

        self.assertTrue(result["ok"])
        self.assertIn("commands/stale.md", result["removed"])
        self.assertNotIn("commands/stale.md", updated["components"])

    def test_asset_relations_extract_command_edges_without_install_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ecc_home = root / "ecc"
            config = self.make_config(root)
            self.populate_all_default_assets(ecc_home)

            for agent in [
                "fastapi-reviewer.md",
                "cpp-build-resolver.md",
                "code-reviewer.md",
                "comment-analyzer.md",
                "pr-test-analyzer.md",
                "silent-failure-hunter.md",
                "type-design-analyzer.md",
                "code-simplifier.md",
            ]:
                self.write_asset(ecc_home, "agents", agent, f"---\nname: {Path(agent).stem}\ndescription: test agent\n---\n")
            self.write_asset(
                ecc_home,
                "agents",
                "security-reviewer.md",
                "---\nname: security-reviewer\ndescription: Security reviewer\n---\n## Prompt Defense Baseline\nsecurity github session\n",
            )
            for skill in ["fastapi-patterns", "security-scan", "cpp-coding-standards"]:
                self.write_asset(ecc_home, "skills", skill, f"---\nname: {skill}\ndescription: test skill\n---\n")

            self.write_asset(
                ecc_home,
                "commands",
                "fastapi-review.md",
                "# FastAPI Review\nInvoke the `fastapi-reviewer` agent.\n\n## Related\n- Agent: `fastapi-reviewer`\n- Skill: `fastapi-patterns`\n- Skill: `security-scan`\n",
            )
            self.write_asset(
                ecc_home,
                "commands",
                "cpp-build.md",
                "# C++ Build\nThis command invokes the **cpp-build-resolver** agent.\n\n## Related\n- Agent: `agents/cpp-build-resolver.md`\n- Skill: `skills/cpp-coding-standards/`\n",
            )
            self.write_asset(
                ecc_home,
                "commands",
                "review-pr.md",
                "## Steps\nRun specialized review agents:\n- `code-reviewer`\n- `comment-analyzer`\n- `pr-test-analyzer`\n- `silent-failure-hunter`\n- `type-design-analyzer`\n- `code-simplifier`\n",
            )
            self.write_asset(ecc_home, "commands", "plain.md", "# Plain\nNo known command relation.\n")

            inventory = core.asset_inventory(config)

        commands = {item["name"]: item for item in inventory["relations"]["commands"]}

        fastapi_targets = {edge["target"]: edge for edge in commands["fastapi-review.md"]["relations"]}
        self.assertEqual(fastapi_targets["agents/fastapi-reviewer.md"]["relation_type"], "explicit")
        self.assertEqual(fastapi_targets["skills/fastapi-patterns"]["relation_type"], "explicit")
        self.assertEqual(fastapi_targets["skills/security-scan"]["relation_type"], "explicit")

        cpp_targets = {edge["target"] for edge in commands["cpp-build.md"]["relations"]}
        self.assertIn("agents/cpp-build-resolver.md", cpp_targets)
        self.assertIn("skills/cpp-coding-standards", cpp_targets)

        review_targets = {edge["target"] for edge in commands["review-pr.md"]["relations"]}
        self.assertTrue({
            "agents/code-reviewer.md",
            "agents/comment-analyzer.md",
            "agents/pr-test-analyzer.md",
            "agents/silent-failure-hunter.md",
            "agents/type-design-analyzer.md",
            "agents/code-simplifier.md",
        }.issubset(review_targets))

        self.assertEqual(commands["plain.md"]["relation_count"], 0)
        self.assertEqual(commands["plain.md"]["message"], "未发现明确关联")
        plain_targets = {edge["target"] for edge in commands["plain.md"]["relations"]}
        self.assertNotIn("agents/security-reviewer.md", plain_targets)
        self.assertTrue(any(edge["type"] == "profile_requires_asset" for edge in inventory["relations"]["edges"]))


if __name__ == "__main__":
    unittest.main()
