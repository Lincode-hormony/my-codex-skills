from __future__ import annotations

import json
import socket
import os
from pathlib import Path


def port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def choose_port() -> int | None:
    ranges = [
        range(3000, 3011),
        range(4173, 4181),
        range(5173, 5184),
        range(8000, 8011),
        range(8080, 8091),
    ]
    for group in ranges:
        for port in group:
            if port_is_free(port):
                return port
    return None


def detect_package_manager(root: Path) -> str:
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    return "npm"


def build_command(package_manager: str, port: int) -> str:
    host_arg = "--host=127.0.0.1"
    port_arg = f"--port={port}"
    if package_manager == "pnpm":
        return f"pnpm run dev -- {host_arg} {port_arg}"
    if package_manager == "yarn":
        return f"yarn dev {host_arg} {port_arg}"
    return f"npm run dev -- {host_arg} {port_arg}"


def build_launch_spec(package_manager: str, port: int) -> tuple[str, list[str]]:
    host_arg = "--host=127.0.0.1"
    port_arg = f"--port={port}"
    if package_manager == "pnpm":
        launcher = "pnpm.cmd" if os.name == "nt" else "pnpm"
        args = ["run", "dev", "--", host_arg, port_arg]
        return launcher, args
    if package_manager == "yarn":
        launcher = "yarn.cmd" if os.name == "nt" else "yarn"
        args = ["dev", host_arg, port_arg]
        return launcher, args
    launcher = "npm.cmd" if os.name == "nt" else "npm"
    args = ["run", "dev", "--", host_arg, port_arg]
    return launcher, args


def main() -> int:
    root = Path.cwd()
    package_json = root / "package.json"
    result = {
        "ok": False,
        "package_manager": None,
        "dev_script": None,
        "port": None,
        "launcher": None,
        "arguments": None,
        "command": None,
        "reason": None,
    }

    if not package_json.exists():
        result["reason"] = "package.json not found in current directory"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    payload = json.loads(package_json.read_text(encoding="utf-8"))
    scripts = payload.get("scripts", {})
    dev_script = scripts.get("dev")
    if not dev_script:
        result["reason"] = "No dev script found in package.json"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    port = choose_port()
    if port is None:
        result["reason"] = "No free candidate port found in common local ranges"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    package_manager = detect_package_manager(root)
    launcher, arguments = build_launch_spec(package_manager, port)
    result.update(
        {
            "ok": True,
            "package_manager": package_manager,
            "dev_script": dev_script,
            "port": port,
            "launcher": launcher,
            "arguments": arguments,
            "command": build_command(package_manager, port),
            "reason": "Selected a free localhost port from common dev ranges",
        }
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
