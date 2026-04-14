from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


REQUIRED_FIELDS = [
    "test_entry_supported",
    "project_type",
    "protocol_version",
    "launch_mode",
    "commands",
    "entry_url_examples",
    "bridge_available",
    "bridge_name",
    "supported_screens",
    "supported_auth_modes",
    "supported_presets",
    "supported_features",
    "recommended_entry_flow",
    "test_series_readiness",
    "limitations",
    "validation",
]

REQUIRED_COMMAND_KEYS = [
    "build_test_entry",
    "preview_test_entry",
]


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def fetch_status(url: str, timeout: float) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "codex-test-init-validator/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return {
            "url": url,
            "status": getattr(response, "status", None),
            "content_type": response.headers.get("Content-Type"),
        }


def ready_strategy_is_consumable(strategy: Any) -> bool:
    if not isinstance(strategy, dict):
        return False
    kind = strategy.get("kind")
    if kind == "selector":
        return isinstance(strategy.get("selector"), str) and bool(strategy.get("selector").strip())
    if kind == "js-expression":
        return isinstance(strategy.get("expression"), str) and bool(strategy.get("expression").strip())
    if kind == "bridge-method":
        return isinstance(strategy.get("method"), str) and bool(strategy.get("method").strip())
    return False


def extract_screenshot_ready_specs(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    supported_screens = payload.get("supported_screens", [])
    if not isinstance(supported_screens, list):
        return specs
    for screen in supported_screens:
        if not isinstance(screen, dict):
            continue
        name = screen.get("name")
        ready = screen.get("ready_strategy")
        if isinstance(name, str) and screen.get("screenshot_ready") is True and isinstance(ready, dict):
            specs[name] = ready
    return specs


def choose_default_ready_screen(payload: dict[str, Any]) -> str | None:
    specs = extract_screenshot_ready_specs(payload)
    if not specs:
        return None
    preferred_examples = payload.get("entry_url_examples", [])
    if isinstance(preferred_examples, list):
        for example in preferred_examples:
            if not isinstance(example, str):
                continue
            marker = "testScreen="
            if marker in example:
                candidate = example.split(marker, 1)[1].split("&", 1)[0]
                if candidate in specs:
                    return candidate
    return next(iter(specs.keys()), None)


def run_playwright_ready_check(base_url: str, screen: str, strategy: dict[str, Any], timeout: float) -> dict[str, Any]:
    npx_executable = shutil.which("npx.cmd") or shutil.which("npx") or "npx"
    target_url = base_url.rstrip("/") + "/?testEntry=1&testScreen=" + screen

    kind = strategy.get("kind")
    if kind == "selector":
        with tempfile.TemporaryDirectory(prefix="codex-test-init-ready-") as temp_dir:
            output_path = Path(temp_dir) / "ready-check.png"
            redirect_path = Path(temp_dir) / "redirect.html"
            redirect_path.write_text(
                (
                    "<!doctype html><meta charset=\"utf-8\">"
                    "<script>"
                    f"location.replace({json.dumps(target_url)});"
                    "</script>"
                ),
                encoding="utf-8",
            )
            command = [
                npx_executable,
                "playwright",
                "screenshot",
                "--browser",
                "chromium",
                "--timeout",
                str(int(timeout * 1000)),
                "--wait-for-selector",
                str(strategy["selector"]),
                redirect_path.resolve().as_uri(),
                str(output_path),
            ]
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            ok = completed.returncode == 0 and output_path.exists()
            if ok:
                return {"ok": True, "url": target_url, "diagnosis": "Playwright confirmed the selector ready strategy at runtime"}
            return {
                "ok": False,
                "url": target_url,
                "diagnosis": completed.stderr.strip() or completed.stdout.strip() or "Playwright ready check failed",
            }
    if kind in {"js-expression", "bridge-method"}:
        return {
            "ok": False,
            "url": target_url,
            "diagnosis": f"Runtime validation for ready strategy kind '{kind}' is not implemented in the validator yet",
        }
    return {"ok": False, "diagnosis": f"Unsupported ready strategy kind: {kind}"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default=None)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--ready-screen", default=None)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    root = Path.cwd()
    summary_path = (
        Path(args.summary)
        if args.summary
        else root / "test-entry-summary.json"
    )

    payload = load_json(summary_path)
    result: dict[str, Any] = {
        "ok": False,
        "summary_path": str(summary_path),
        "static_valid": False,
        "runtime_checked": False,
        "runtime_ok": False,
        "missing_required_fields": [],
        "missing_command_fields": [],
        "screenshot_ready_screens": [],
        "invalid_ready_screens": [],
        "ready_runtime_screen": args.ready_screen,
        "ready_runtime_checked": False,
        "ready_runtime_ok": False,
        "ready_runtime_diagnosis": None,
        "reasons": [],
        "http_checks": [],
    }

    if payload is None:
        result["reasons"].append("summary_unreadable_or_missing")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    missing_required = [field for field in REQUIRED_FIELDS if field not in payload]
    commands = payload.get("commands", {}) if isinstance(payload.get("commands"), dict) else {}
    missing_command_fields = [
        field for field in REQUIRED_COMMAND_KEYS if not commands.get(field)
    ]
    supported_screens = payload.get("supported_screens", [])
    screenshot_ready_screens = []
    if isinstance(supported_screens, list):
        for screen in supported_screens:
            if not isinstance(screen, dict):
                continue
            ready = screen.get("ready_strategy")
            if screen.get("screenshot_ready") is True:
                if ready_strategy_is_consumable(ready):
                    screenshot_ready_screens.append(screen.get("name"))
                else:
                    result["invalid_ready_screens"].append(screen.get("name"))

    result["missing_required_fields"] = missing_required
    result["missing_command_fields"] = missing_command_fields
    result["screenshot_ready_screens"] = screenshot_ready_screens

    if payload.get("test_entry_supported") is not True:
        result["reasons"].append("test_entry_not_supported")
    if str(payload.get("protocol_version")) != "2":
        result["reasons"].append("unsupported_protocol_version")
    if payload.get("launch_mode") != "build-preview":
        result["reasons"].append("unsupported_launch_mode")
    if missing_required:
        result["reasons"].append("missing_required_fields")
    if missing_command_fields:
        result["reasons"].append("missing_command_fields")
    if payload.get("bridge_available") is not True:
        result["reasons"].append("bridge_not_available")
    if not payload.get("entry_url_examples"):
        result["reasons"].append("missing_entry_url_examples")
    if not screenshot_ready_screens:
        result["reasons"].append("missing_screenshot_ready_screen")
    if result["invalid_ready_screens"]:
        result["reasons"].append("invalid_ready_strategy")

    result["static_valid"] = len(result["reasons"]) == 0

    if args.base_url:
        result["runtime_checked"] = True
        try:
            result["http_checks"].append(fetch_status(args.base_url, args.timeout))
            examples = payload.get("entry_url_examples", [])
            if examples:
                first_example = examples[0]
                example_url = (
                    first_example
                    if isinstance(first_example, str) and first_example.startswith("http")
                    else urljoin(args.base_url.rstrip("/") + "/", str(first_example).lstrip("/"))
                )
                result["http_checks"].append(fetch_status(example_url, args.timeout))
            result["runtime_ok"] = all(
                check.get("status") and 200 <= int(check["status"]) < 400
                for check in result["http_checks"]
            )
            if not result["runtime_ok"]:
                result["reasons"].append("runtime_http_check_failed")
        except (URLError, OSError, ValueError) as exc:
            result["reasons"].append(f"runtime_http_check_failed:{exc}")
            result["runtime_ok"] = False

    ready_specs = extract_screenshot_ready_specs(payload)
    selected_ready_screen = args.ready_screen
    if args.base_url and not selected_ready_screen:
        selected_ready_screen = choose_default_ready_screen(payload)
    result["ready_runtime_screen"] = selected_ready_screen
    if args.base_url and selected_ready_screen:
        result["ready_runtime_checked"] = True
        ready_strategy = ready_specs.get(selected_ready_screen)
        if not ready_strategy:
            result["reasons"].append("ready_screen_not_screenshot_capable")
            result["ready_runtime_diagnosis"] = "Requested ready screen is missing or not screenshot-capable"
        else:
            ready_result = run_playwright_ready_check(args.base_url, selected_ready_screen, ready_strategy, args.timeout)
            result["ready_runtime_ok"] = ready_result["ok"]
            result["ready_runtime_diagnosis"] = ready_result["diagnosis"]
            if not ready_result["ok"]:
                result["reasons"].append("ready_runtime_check_failed")

    result["ok"] = result["static_valid"] and (
        not result["runtime_checked"] or result["runtime_ok"]
    ) and (
        not result["ready_runtime_checked"] or result["ready_runtime_ok"]
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
