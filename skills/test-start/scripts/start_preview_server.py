from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path


def load_summary(root: Path):
    for candidate in [root / "test-entry-summary.json", root / "docs" / "test-entry-summary.json"]:
        if candidate.exists():
            return candidate, json.loads(candidate.read_text(encoding="utf-8-sig"))
    return None, None


def verify_http(url: str, timeout: float):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read(4096)
            content_type = response.headers.get("Content-Type", "")
            status_code = getattr(response, "status", 200)
            text = body.decode("utf-8", errors="ignore").lower()
            plausible = 200 <= status_code < 400 and ("html" in content_type or "<html" in text or "doctype html" in text)
            return {"ok": plausible, "status_code": status_code, "content_type": content_type, "diagnosis": "HTTP response looks like an app page" if plausible else "HTTP response did not look like a normal app page"}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status_code": exc.code, "content_type": None, "diagnosis": f"HTTP error {exc.code}"}
    except Exception as exc:
        return {"ok": False, "status_code": None, "content_type": None, "diagnosis": f"Request failed: {exc}"}


def wait_for_http(url: str, startup_timeout: float, probe_timeout: float):
    deadline = time.time() + startup_timeout
    last_result = None
    while time.time() < deadline:
        result = verify_http(url, probe_timeout)
        last_result = result
        if result["ok"]:
            return result
        time.sleep(1.0)
    return last_result or {"ok": False, "status_code": None, "content_type": None, "diagnosis": "Timed out waiting for HTTP response"}


def choose_log_path(root: Path, requested: str | None, suffix: str, port: int) -> Path:
    base = Path(requested) if requested else root / f".codex-test-start-p{port}.{suffix}.log"
    if not base.is_absolute():
        base = root / base
    if not base.exists():
        return base
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    return base.with_name(f"{base.stem}-{timestamp}{base.suffix}")


def append_preview_flags(command: str, port: int) -> str:
    return f"{command} -- --host 127.0.0.1 --port {port}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--startup-timeout", type=float, default=30.0)
    parser.add_argument("--probe-timeout", type=float, default=5.0)
    parser.add_argument("--stdout-log")
    parser.add_argument("--stderr-log")
    args = parser.parse_args()

    root = Path.cwd()
    _, summary = load_summary(root)
    result = {"ok": False, "pid": None, "base_url": f"http://{args.host}:{args.port}/", "build_command": None, "preview_command": None, "stdout_log": None, "stderr_log": None, "status_code": None, "content_type": None, "diagnosis": None}
    if summary is None:
        result["diagnosis"] = "No summary file found"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    commands = summary.get("commands", {}) if isinstance(summary.get("commands"), dict) else {}
    build_command = commands.get("build_test_entry")
    preview_command = commands.get("preview_test_entry")
    if not build_command or not preview_command:
        result["diagnosis"] = "Summary is missing build or preview commands"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    stdout_log = choose_log_path(root, args.stdout_log, "out", args.port)
    stderr_log = choose_log_path(root, args.stderr_log, "err", args.port)
    stdout_log.parent.mkdir(parents=True, exist_ok=True)
    stderr_log.parent.mkdir(parents=True, exist_ok=True)

    build_run = subprocess.run(build_command, cwd=root, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    stdout_log.write_text(build_run.stdout or "", encoding="utf-8")
    stderr_log.write_text(build_run.stderr or "", encoding="utf-8")
    if build_run.returncode != 0:
        result.update({"build_command": build_command, "preview_command": append_preview_flags(preview_command, args.port), "stdout_log": str(stdout_log), "stderr_log": str(stderr_log), "diagnosis": build_run.stderr.strip() or build_run.stdout.strip() or "Build command failed"})
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    effective_preview_command = append_preview_flags(preview_command, args.port)
    with stdout_log.open("a", encoding="utf-8") as out_handle, stderr_log.open("a", encoding="utf-8") as err_handle:
        process = subprocess.Popen(effective_preview_command, cwd=root, stdout=out_handle, stderr=err_handle, shell=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)

    ready = wait_for_http(result["base_url"], args.startup_timeout, args.probe_timeout)
    result.update({"ok": ready["ok"], "pid": process.pid, "build_command": build_command, "preview_command": effective_preview_command, "stdout_log": str(stdout_log), "stderr_log": str(stderr_log), "status_code": ready["status_code"], "content_type": ready["content_type"], "diagnosis": ready["diagnosis"]})
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
