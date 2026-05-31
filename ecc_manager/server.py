"""Small local web server for ECC Manager."""

from __future__ import annotations

import argparse
import errno
import json
import mimetypes
import secrets
import subprocess
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from . import core
from .default_profiles import ARCHITECTURES, PACKS, PHASES, PROJECT_TYPES


WEB_ROOT = Path(__file__).with_name("web")
SESSION_TOKEN = secrets.token_urlsafe(32)
CSP = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'"


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


def choose_folder_script(current: str, prompt: str) -> str:
    default_path = Path(current).expanduser()
    if not default_path.exists():
        default_path = Path.cwd()
    elif not default_path.is_dir():
        default_path = default_path.parent
    return "\n".join([
        "const app = Application.currentApplication();",
        "app.includeStandardAdditions = true;",
        f"const defaultFolder = Path({json.dumps(str(default_path))});",
        f"const chosenFolder = app.chooseFolder({{withPrompt: {json.dumps(prompt, ensure_ascii=False)}, defaultLocation: defaultFolder}});",
        "chosenFolder.toString();",
    ])


def choose_project_script(current: str, prompt: str = "选择要由 ECC Manager 管理的项目目录") -> str:
    return choose_folder_script(current, prompt)


def profile_catalog() -> dict[str, Any]:
    config = core.load_config()
    paths = core.paths_from_config(config)
    profiles = core.load_profiles(paths.profile_home)
    if not any(profiles.values()):
        profiles = {"phases": PHASES, "architectures": ARCHITECTURES, "project-types": PROJECT_TYPES, "packs": PACKS}
    return {"config": config, "profiles": profiles}


def rebuild_apply_plan(client_plan: dict[str, Any]) -> dict[str, Any]:
    action = client_plan.get("action")
    profiles = client_plan.get("profiles")
    project = client_plan.get("project")
    if action not in {"init", "add", "phase"}:
        raise ValueError("invalid plan action")
    if not isinstance(profiles, list) or not all(isinstance(item, str) for item in profiles):
        raise ValueError("invalid plan profiles")
    if not isinstance(project, str) or not project.strip():
        raise ValueError("invalid plan project")
    return core.build_plan(action, profiles, project, include_optional=bool(client_plan.get("include_optional", False)))


def open_local_path(target: str | None, runner: Any = subprocess.run) -> tuple[dict[str, Any], int]:
    if not target:
        return {"ok": False, "error": "missing path"}, 400

    path = Path(target).expanduser()
    if not path.exists():
        return {"ok": False, "error": f"路径不存在：{path}", "path": str(path)}, 404

    result = runner(["open", str(path)], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        error = result.stderr.strip() or result.stdout.strip() or f"open exited with {result.returncode}"
        return {"ok": False, "error": error, "path": str(path)}, 500

    return {"ok": True, "path": str(path)}, 200


def static_file_target(request_path: str, web_root: Path = WEB_ROOT) -> Path | None:
    root = web_root.resolve()
    rel = "index.html" if request_path in {"/", ""} else unquote(request_path).lstrip("/")
    target = (root / rel).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return None
    if not target.exists() or target.is_dir():
        return None
    return target


class Handler(BaseHTTPRequestHandler):
    server_version = "ECCManager/0.1"

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[ecc-manager] {self.address_string()} - {format % args}")

    def send_json(self, data: Any, status: int = 200) -> None:
        payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def read_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def origin_allowed(self) -> bool:
        origin = self.headers.get("Origin")
        if not origin:
            return True
        origin_url = urlparse(origin)
        host_url = urlparse(f"//{self.headers.get('Host', '')}")
        return origin_url.hostname == host_url.hostname and origin_url.port == host_url.port

    def authorize_post(self) -> bool:
        if self.headers.get("X-ECC-Manager-Token") != SESSION_TOKEN:
            self.send_json({"ok": False, "error": "invalid or missing local session token; reload ECC Manager"}, 403)
            return False
        if not self.origin_allowed():
            self.send_json({"ok": False, "error": "cross-origin requests are not allowed"}, 403)
            return False
        return True

    def do_OPTIONS(self) -> None:
        self.send_response(403)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/bootstrap":
            config = core.load_config()
            self.send_json({
                "config": config,
                "scan": core.scan_project(Path.cwd(), config),
                "cwd": str(Path.cwd()),
                "home": str(Path.home()),
                "csrf_token": SESSION_TOKEN,
            })
            return
        if path == "/api/catalog":
            self.send_json(profile_catalog())
            return
        if path == "/api/assets":
            self.send_json(core.asset_inventory())
            return

        target = static_file_target(path)
        if target is None:
            self.send_error(404)
            return
        content = target.read_bytes()
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if target.name == "index.html":
            self.send_header("Content-Security-Policy", CSP)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:
        try:
            if not self.authorize_post():
                return
            body = self.read_body()
            path = urlparse(self.path).path
            if path == "/api/profiles/init":
                self.send_json(core.bootstrap_profiles(force=bool(body.get("force", False))))
            elif path == "/api/project/scan":
                self.send_json(core.scan_project(body.get("project")))
            elif path == "/api/global-init":
                self.send_json(core.global_init(dry_run=bool(body.get("dry_run", False)), project_path=body.get("project")))
            elif path == "/api/plan":
                self.send_json(core.build_plan(
                    body.get("action", "init"),
                    body.get("profiles", []),
                    body.get("project"),
                    include_optional=bool(body.get("include_optional", False)),
                ))
            elif path == "/api/apply":
                plan = rebuild_apply_plan(body.get("plan") or {})
                if not plan.get("can_apply", False):
                    self.send_json({"ok": False, "error": "存在缺失源文件或目标冲突，不能执行", "plan": plan}, 400)
                else:
                    self.send_json(core.apply_plan(plan))
            elif path == "/api/status":
                self.send_json(core.status(body.get("project")))
            elif path == "/api/doctor":
                self.send_json(core.doctor(body.get("project"), fix=bool(body.get("fix", False))))
            elif path == "/api/ecc/scan":
                self.send_json(core.ecc_scan())
            elif path == "/api/ecc/apply-suggestions":
                self.send_json(core.apply_ecc_suggestions(body.get("suggestions", [])))
            elif path == "/api/remove":
                self.send_json(core.remove_profile(body.get("profile_id", ""), body.get("project"), dry_run=bool(body.get("dry_run", False))))
            elif path == "/api/open-path":
                data, status = open_local_path(body.get("path"))
                self.send_json(data, status)
            elif path == "/api/settings":
                config = core.save_config(body)
                self.send_json({"ok": True, "config": config})
            elif path == "/api/choose-project":
                current = body.get("current") or str(Path.cwd())
                prompt = body.get("prompt") or "选择要由 ECC Manager 管理的项目目录"
                script = choose_project_script(current, prompt)
                result = subprocess.run(["osascript", "-l", "JavaScript", "-e", script], capture_output=True, text=True, check=False)
                if result.returncode == 0:
                    self.send_json({"ok": True, "path": result.stdout.strip().rstrip("/")})
                else:
                    self.send_json({"ok": False, "cancelled": True, "error": result.stderr.strip() or "cancelled"})
            elif path == "/api/choose-folder":
                current = body.get("current") or str(Path.cwd())
                prompt = body.get("prompt") or "选择目录"
                script = choose_folder_script(current, prompt)
                result = subprocess.run(["osascript", "-l", "JavaScript", "-e", script], capture_output=True, text=True, check=False)
                if result.returncode == 0:
                    self.send_json({"ok": True, "path": result.stdout.strip().rstrip("/")})
                else:
                    self.send_json({"ok": False, "cancelled": True, "error": result.stderr.strip() or "cancelled"})
            else:
                self.send_error(404)
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, 500)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ecc-manager", description="Start ECC Manager local web UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args(argv)

    port = args.port
    for offset in range(10):
        try:
            server = ReusableThreadingHTTPServer((args.host, port), Handler)
            break
        except OSError as exc:
            if exc.errno != errno.EADDRINUSE or args.port != 8765 or offset == 9:
                raise
            port += 1
    url = f"http://{args.host}:{port}"
    print(f"ECC Manager running at {url}")
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nECC Manager stopped")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
