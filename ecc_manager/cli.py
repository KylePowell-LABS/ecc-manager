"""Command line entry point for ecc-use."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from . import core


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def project_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project", "-p", default=str(Path.cwd()), help="Project directory. Defaults to current directory.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ecc-use", description="Manage project-level ECC profiles.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("profiles-init", help="Create default ECC profiles under PROFILE_HOME.")

    global_init = sub.add_parser("global-init", help="Link global /ecc-plan only.")
    global_init.add_argument("--dry-run", action="store_true")
    global_init.add_argument("--project", "-p", default=None, help="Also link /ecc-plan into this project.")

    init = sub.add_parser("init", help="Initialize project with phase, architecture, project type fragments, and optional packs.")
    init.add_argument("profiles", nargs="+")
    init.add_argument("--dry-run", action="store_true")
    project_arg(init)

    add = sub.add_parser("add", help="Add phase, architecture, project type fragment, or pack to a project.")
    add.add_argument("profiles", nargs="+")
    add.add_argument("--dry-run", action="store_true")
    project_arg(add)

    remove = sub.add_parser("remove", help="Remove a profile id using lock reference counts.")
    remove.add_argument("profile_id")
    remove.add_argument("--dry-run", action="store_true")
    project_arg(remove)

    status = sub.add_parser("status", help="Show current project ECC status.")
    project_arg(status)

    list_cmd = sub.add_parser("list", help="List available profiles.")
    list_cmd.add_argument("kind", nargs="?", choices=["phases", "architectures", "project-types", "packs"])

    doctor = sub.add_parser("doctor", help="Run project checks.")
    doctor.add_argument("--fix", action="store_true")
    project_arg(doctor)

    args = parser.parse_args(argv)

    try:
        if args.command == "profiles-init":
            print_json(core.bootstrap_profiles())
        elif args.command == "global-init":
            print_json(core.global_init(dry_run=args.dry_run, project_path=args.project))
        elif args.command in {"init", "add"}:
            plan = core.build_plan(args.command, args.profiles, args.project)
            if args.dry_run:
                print_json(plan)
            else:
                if not plan["can_apply"]:
                    print_json({"ok": False, "error": "missing source files or target conflicts", "plan": plan})
                    return 2
                print_json(core.apply_plan(plan))
        elif args.command == "remove":
            print_json(core.remove_profile(args.profile_id, args.project, args.dry_run))
        elif args.command == "status":
            print_json(core.status(args.project))
        elif args.command == "list":
            config = core.load_config()
            paths = core.paths_from_config(config)
            profiles = core.load_profiles(paths.profile_home)
            if not any(profiles.values()):
                from .default_profiles import ARCHITECTURES, PACKS, PHASES, PROJECT_TYPES

                profiles = {"phases": PHASES, "architectures": ARCHITECTURES, "project-types": PROJECT_TYPES, "packs": PACKS}
            print_json(profiles[args.kind] if args.kind else profiles)
        elif args.command == "doctor":
            print_json(core.doctor(args.project, args.fix))
    except Exception as exc:
        print_json({"ok": False, "error": str(exc)})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
