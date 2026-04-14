from __future__ import annotations

import json
import socket
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
    for group in [range(4173, 4181), range(3000, 3011), range(5173, 5184), range(8000, 8011), range(8080, 8091)]:
        for port in group:
            if port_is_free(port):
                return port
    return None


def load_summary(root: Path):
    for candidate in [root / "test-entry-summary.json", root / "docs" / "test-entry-summary.json"]:
        if candidate.exists():
            return candidate, json.loads(candidate.read_text(encoding="utf-8-sig"))
    return None, None


def main() -> int:
    root = Path.cwd()
    summary_path, summary = load_summary(root)
    result = {"ok": False, "summary_path": str(summary_path) if summary_path else None, "build_command": None, "preview_command": None, "port": None, "reason": None}
    if summary is None:
        result["reason"] = "No summary file found"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    commands = summary.get("commands", {}) if isinstance(summary.get("commands"), dict) else {}
    build_command = commands.get("build_test_entry")
    preview_command = commands.get("preview_test_entry")
    if not build_command or not preview_command:
        result["reason"] = "Summary is missing build or preview commands"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    port = choose_port()
    if port is None:
        result["reason"] = "No free candidate port found in common local preview ranges"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    result.update({"ok": True, "build_command": build_command, "preview_command": preview_command, "port": port, "reason": "Selected a free localhost port and accepted the summary's build-preview contract"})
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
