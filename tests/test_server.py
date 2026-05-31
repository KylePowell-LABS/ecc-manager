from __future__ import annotations

import tempfile
import subprocess
import unittest
from pathlib import Path

from ecc_manager import server
from ecc_manager.server import (
    Handler,
    choose_folder_script,
    choose_project_script,
    open_local_path,
    rebuild_apply_plan,
    static_file_target,
)


class ServerTests(unittest.TestCase):
    def test_choose_project_script_uses_existing_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = choose_project_script(tmp)

        self.assertIn(f'const defaultFolder = Path("{tmp}");', script)
        self.assertIn("app.chooseFolder", script)
        self.assertIn("chosenFolder.toString();", script)
        self.assertIn('withPrompt: "选择要由 ECC Manager 管理的项目目录"', script)

    def test_choose_project_script_accepts_localized_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = choose_project_script(tmp, "Choose the project folder")

        self.assertIn('withPrompt: "Choose the project folder"', script)

    def test_choose_project_script_uses_file_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file_path = root / "CLAUDE.md"
            file_path.write_text("test\n", encoding="utf-8")

            script = choose_project_script(str(file_path))

        self.assertIn(f'const defaultFolder = Path("{root}");', script)

    def test_choose_folder_script_uses_custom_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = choose_folder_script(tmp, "选择 ECC_HOME")

        self.assertIn(f'const defaultFolder = Path("{tmp}");', script)
        self.assertIn('withPrompt: "选择 ECC_HOME"', script)

    def test_open_local_path_reports_missing_path(self) -> None:
        data, status = open_local_path("/path/that/does/not/exist")

        self.assertEqual(status, 404)
        self.assertFalse(data["ok"])
        self.assertIn("路径不存在", data["error"])

    def test_open_local_path_reports_open_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            def fail_open(*_args, **_kwargs):
                return subprocess.CompletedProcess(["open", tmp], 1, stdout="", stderr="open failed")

            data, status = open_local_path(tmp, runner=fail_open)

        self.assertEqual(status, 500)
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"], "open failed")

    def test_static_file_target_rejects_paths_outside_web_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "web"
            root.mkdir()
            (root / "index.html").write_text("ok\n", encoding="utf-8")
            sibling = Path(f"{root}-evil")
            sibling.mkdir()
            (sibling / "index.html").write_text("no\n", encoding="utf-8")

            self.assertEqual(static_file_target("/", root), (root / "index.html").resolve())
            self.assertIsNone(static_file_target(f"/../{sibling.name}/index.html", root))

    def test_rebuild_apply_plan_ignores_client_supplied_paths(self) -> None:
        old_build_plan = server.core.build_plan

        def fake_build_plan(action, profiles, project, include_optional=False):
            self.assertEqual(action, "init")
            self.assertEqual(profiles, ["ph-init"])
            self.assertEqual(project, "/tmp/project")
            self.assertFalse(include_optional)
            return {
                "action": action,
                "profiles": profiles,
                "project": project,
                "create": [{"source": "/safe/source", "target": "/safe/target"}],
                "can_apply": True,
            }

        server.core.build_plan = fake_build_plan
        try:
            plan = rebuild_apply_plan({
                "action": "init",
                "profiles": ["ph-init"],
                "project": "/tmp/project",
                "create": [{"source": "/tmp/evil", "target": "/tmp/evil-target"}],
            })
        finally:
            server.core.build_plan = old_build_plan

        self.assertEqual(plan["create"][0]["source"], "/safe/source")

    def test_post_requires_local_session_token(self) -> None:
        class FakeHandler:
            headers = {"Host": "127.0.0.1:8765"}
            sent: tuple[dict, int] | None = None
            origin_allowed = Handler.origin_allowed

            def send_json(self, data, status=200):
                self.sent = (data, status)

        fake = FakeHandler()

        self.assertFalse(Handler.authorize_post(fake))
        self.assertEqual(fake.sent[1], 403)

        fake.headers = {"Host": "127.0.0.1:8765", "X-ECC-Manager-Token": server.SESSION_TOKEN}
        self.assertTrue(Handler.authorize_post(fake))

    def test_post_rejects_cross_origin_even_with_token(self) -> None:
        class FakeHandler:
            headers = {
                "Host": "127.0.0.1:8765",
                "Origin": "https://example.com",
                "X-ECC-Manager-Token": server.SESSION_TOKEN,
            }
            sent: tuple[dict, int] | None = None
            origin_allowed = Handler.origin_allowed

            def send_json(self, data, status=200):
                self.sent = (data, status)

        fake = FakeHandler()

        self.assertFalse(Handler.authorize_post(fake))
        self.assertEqual(fake.sent[1], 403)


if __name__ == "__main__":
    unittest.main()
