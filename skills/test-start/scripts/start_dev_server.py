from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path


def load_plan(root: Path):
    package_json = root / "package.json"
    if not package_json.exists():
        return {"ok": False, "diagnosis": "package.json not found"}

    # Reuse planner output format locally instead of asking the caller to rebuild it.
    from plan_dev_server import detect_package_manager, build_command, build_launch_spec  # type: ignore

    payload = json.loads(package_json.read_text(encoding="utf-8"))
    scripts = payload.get("scripts", {})
    dev_script = scripts.get("dev")
    if not dev_script:
        return {"ok": False, "diagnosis": "No dev script found in package.json"}

    package_manager = detect_package_manager(root)
    return {
        "ok": True,
        "package_manager": package_manager,
        "dev_script": dev_script,
        "build_command": build_command,
        "build_launch_spec": build_launch_spec,
    }


def verify_http(url: str, timeout: float):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read(4096)
            content_type = response.headers.get("Content-Type", "")
            status_code = getattr(response, "status", 200)
            text = body.decode("utf-8", errors="ignore").lower()
            plausible = (
                200 <= status_code < 400
                and ("html" in content_type or "<html" in text or "doctype html" in text)
            )
            return {
                "ok": plausible,
                "status_code": status_code,
                "content_type": content_type,
                "diagnosis": "HTTP response looks like an app page" if plausible else "HTTP response did not look like a normal app page",
            }
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "status_code": exc.code,
            "content_type": None,
            "diagnosis": f"HTTP error {exc.code}",
        }
    except Exception as exc:
        return {
            "ok": False,
            "status_code": None,
            "content_type": None,
            "diagnosis": f"Request failed: {exc}",
        }


def wait_for_http(url: str, startup_timeout: float, probe_timeout: float):
    deadline = time.time() + startup_timeout
    last_result = None
    while time.time() < deadline:
        result = verify_http(url, probe_timeout)
        last_result = result
        if result["ok"]:
            return result
        time.sleep(1.0)
    return last_result or {
        "ok": False,
        "status_code": None,
        "content_type": None,
        "diagnosis": "Timed out waiting for HTTP response",
    }


def choose_log_path(root: Path, requested: str | None, suffix: str, port: int) -> Path:
    if requested:
        base = Path(requested)
        if not base.is_absolute():
            base = root / base
        stem = base.stem
        ext = base.suffix or ".log"
        candidate = base.with_name(f"{stem}-p{port}{ext}")
    else:
        candidate = root / f".codex-test-start-p{port}.{suffix}.log"

    if not candidate.exists():
        return candidate

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    return candidate.with_name(f"{candidate.stem}-{timestamp}{candidate.suffix}")


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
    plan = load_plan(root)
    result = {
        "ok": False,
        "pid": None,
        "base_url": f"http://{args.host}:{args.port}/",
        "launcher": None,
        "arguments": None,
        "stdout_log": None,
        "stderr_log": None,
        "status_code": None,
        "content_type": None,
        "diagnosis": None,
    }

    if not plan["ok"]:
        result["diagnosis"] = plan["diagnosis"]
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    launcher_name, arguments = plan["build_launch_spec"](plan["package_manager"], args.port)
    launcher_path = shutil.which(launcher_name)
    if launcher_path is None:
        result["diagnosis"] = f"Launcher not found: {launcher_name}"
        result["launcher"] = launcher_name
        result["arguments"] = arguments
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    stdout_log = choose_log_path(root, args.stdout_log, "out", args.port)
    stderr_log = choose_log_path(root, args.stderr_log, "err", args.port)
    stdout_log.parent.mkdir(parents=True, exist_ok=True)
    stderr_log.parent.mkdir(parents=True, exist_ok=True)

    with stdout_log.open("w", encoding="utf-8") as out_handle, stderr_log.open("w", encoding="utf-8") as err_handle:
        process = subprocess.Popen(
            [launcher_path, *arguments],
            cwd=root,
            stdout=out_handle,
            stderr=err_handle,
            shell=False,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

    ready = wait_for_http(result["base_url"], args.startup_timeout, args.probe_timeout)
    result.update(
        {
            "pid": process.pid,
            "launcher": launcher_path,
            "arguments": arguments,
            "stdout_log": str(stdout_log),
            "stderr_log": str(stderr_log),
            "status_code": ready["status_code"],
            "content_type": ready["content_type"],
            "diagnosis": ready["diagnosis"],
            "ok": ready["ok"],
        }
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
