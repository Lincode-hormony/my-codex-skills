from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlencode


def load_summary(root: Path):
    for candidate in [root / "test-entry-summary.json", root / "docs" / "test-entry-summary.json"]:
        if candidate.exists():
            return candidate, json.loads(candidate.read_text(encoding="utf-8"))
    return None, None


def build_normal_launch_preflight(summary: dict):
    payload = summary.get("normal_launch_preflight")
    if not isinstance(payload, dict):
        return []

    kind = payload.get("kind")
    diagnosis = payload.get("diagnosis")
    steps = payload.get("steps")
    if not isinstance(kind, str) or not isinstance(diagnosis, str) or not isinstance(steps, list):
        return []

    normalized_steps = [step for step in steps if isinstance(step, str) and step.strip()]
    if not normalized_steps:
        return []

    return [{
        "kind": kind,
        "diagnosis": diagnosis,
        "steps": normalized_steps,
    }]


def build_preferred_direct_launch(summary: dict):
    payload = summary.get("preferred_direct_launch")
    if not isinstance(payload, dict):
        return None

    screen = payload.get("screen")
    auth = payload.get("auth")
    preset = payload.get("preset")

    supported_screens = set(summary.get("supported_screens", []))
    supported_auth_modes = set(summary.get("supported_auth_modes", []))
    supported_presets = set(summary.get("supported_presets", []))

    if screen is not None:
        if not isinstance(screen, str) or screen not in supported_screens:
            return None
    if auth is not None:
        if not isinstance(auth, str) or auth not in supported_auth_modes:
            return None
    if preset is not None:
        if not isinstance(preset, str) or preset not in supported_presets:
            return None

    if not screen and not auth and not preset:
        return None

    return {
        "screen": screen,
        "auth": auth,
        "preset": preset,
    }


def build_normal_launch_url(base_url: str, summary: dict):
    preferred = build_preferred_direct_launch(summary)
    if preferred:
        params = {"testEntry": "1"}
        if preferred.get("screen"):
            params["testScreen"] = preferred["screen"]
        if preferred.get("auth"):
            params["testAuth"] = preferred["auth"]
        if preferred.get("preset"):
            params["testPreset"] = preferred["preset"]
        return {
            "url": base_url.rstrip("/") + "/?" + urlencode(params),
            "mode": "preferred-direct",
            "diagnosis": "Contract-preferred direct launch URL",
        }

    payload = summary.get("normal_launch_preflight")
    if not isinstance(payload, dict):
        return {
            "url": base_url.rstrip("/") + "/",
            "mode": "normal",
            "diagnosis": "Normal launch URL",
        }

    query_params = payload.get("query_params")
    if not isinstance(query_params, dict) or not query_params:
        return {
            "url": base_url.rstrip("/") + "/",
            "mode": "normal",
            "diagnosis": "Normal launch URL",
        }

    params = {
        str(key): str(value)
        for key, value in query_params.items()
        if isinstance(key, str) and isinstance(value, (str, int, float, bool))
    }
    if not params:
        return {
            "url": base_url.rstrip("/") + "/",
            "mode": "normal",
            "diagnosis": "Normal launch URL",
        }

    return {
        "url": base_url.rstrip("/") + "/?" + urlencode(params),
        "mode": "normal",
        "diagnosis": "Normal launch URL with contract preflight",
    }


def verify_once(url: str, timeout: float):
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


def verify_base_url(url: str, timeout: float):
    attempts = [timeout, max(timeout * 3, timeout + 10)]
    last_result = None
    for idx, attempt_timeout in enumerate(attempts, start=1):
        result = verify_once(url, attempt_timeout)
        result["attempt"] = idx
        result["attempt_timeout_sec"] = attempt_timeout
        last_result = result
        if result["ok"]:
            if idx > 1:
                result["diagnosis"] = f"{result['diagnosis']} after retry {idx}"
            return result
        if idx < len(attempts):
            if "timed out" not in result["diagnosis"].lower() and "connection" not in result["diagnosis"].lower():
                break
            time.sleep(1.2)
    return last_result


def build_contract_url(base_url: str, summary: dict, screen: str | None, auth: str | None, preset: str | None):
    supported_screens = list(summary.get("supported_screens", []))
    supported_auth_modes = list(summary.get("supported_auth_modes", []))
    supported_presets = list(summary.get("supported_presets", []))

    if not screen and not preset and not auth:
        launch = build_normal_launch_url(base_url, summary)
        return {
            "ok": True,
            "mode": launch["mode"],
            "url": launch["url"],
            "diagnosis": launch["diagnosis"],
            "next_action": "proceed",
            "preflight_actions": build_normal_launch_preflight(summary),
            "supported_screens": supported_screens,
            "supported_auth_modes": supported_auth_modes,
            "supported_presets": supported_presets,
        }

    supported_screen_set = set(supported_screens)
    supported_auth_set = set(supported_auth_modes)
    supported_preset_set = set(supported_presets)

    effective_auth = auth
    if effective_auth is None and (screen or preset) and "bypass" in supported_auth_set:
        effective_auth = "bypass"

    if screen and screen not in supported_screen_set:
        return {
            "ok": False,
            "mode": "screen",
            "url": None,
            "diagnosis": f"Unsupported screen: {screen}",
            "next_action": "offer-supported-or-test-init",
            "supported_screens": supported_screens,
            "supported_auth_modes": supported_auth_modes,
            "supported_presets": supported_presets,
        }
    if effective_auth and effective_auth not in supported_auth_set:
        return {
            "ok": False,
            "mode": "screen",
            "url": None,
            "diagnosis": f"Unsupported auth mode: {effective_auth}",
            "next_action": "offer-supported-or-test-init",
            "supported_screens": supported_screens,
            "supported_auth_modes": supported_auth_modes,
            "supported_presets": supported_presets,
        }
    if preset and preset not in supported_preset_set:
        return {
            "ok": False,
            "mode": "screen",
            "url": None,
            "diagnosis": f"Unsupported preset: {preset}",
            "next_action": "offer-supported-or-test-init",
            "supported_screens": supported_screens,
            "supported_auth_modes": supported_auth_modes,
            "supported_presets": supported_presets,
        }

    params = {"testEntry": "1"}
    if screen:
        params["testScreen"] = screen
    if effective_auth:
        params["testAuth"] = effective_auth
    if preset:
        params["testPreset"] = preset

    return {
        "ok": True,
        "mode": "screen" if screen or preset else "auth",
        "url": base_url.rstrip("/") + "/?" + urlencode(params),
        "diagnosis": "Contract-based test-entry URL with default bypass auth" if auth is None and effective_auth == "bypass" and (screen or preset) else "Contract-based test-entry URL",
        "next_action": "proceed",
        "preflight_actions": [],
        "supported_screens": supported_screens,
        "supported_auth_modes": supported_auth_modes,
        "supported_presets": supported_presets,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--screen")
    parser.add_argument("--auth")
    parser.add_argument("--preset")
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()

    _, summary = load_summary(Path.cwd())
    if summary is None:
        print(json.dumps({
            "ok": False,
            "status_code": None,
            "content_type": None,
            "mode": "normal" if not args.screen and not args.preset else "screen",
            "url": None,
            "diagnosis": "No summary file found",
            "next_action": "use-test-init",
            "preflight_actions": [],
            "supported_screens": [],
            "supported_auth_modes": [],
            "supported_presets": [],
        }, ensure_ascii=False, indent=2))
        return 0

    base_check = verify_base_url(args.base_url, args.timeout)
    if not base_check["ok"]:
        print(json.dumps({
            "ok": False,
            "status_code": base_check["status_code"],
            "content_type": base_check["content_type"],
            "mode": "normal" if not args.screen and not args.preset else "screen",
            "url": None,
            "diagnosis": base_check["diagnosis"],
            "next_action": "fix-base-url",
            "preflight_actions": [],
            "supported_screens": summary.get("supported_screens", []),
            "supported_auth_modes": summary.get("supported_auth_modes", []),
            "supported_presets": summary.get("supported_presets", []),
        }, ensure_ascii=False, indent=2))
        return 0

    built = build_contract_url(args.base_url, summary, args.screen, args.auth, args.preset)
    result = {
        "ok": built["ok"],
        "status_code": base_check["status_code"],
        "content_type": base_check["content_type"],
        "mode": built["mode"],
        "url": built["url"],
        "diagnosis": built["diagnosis"],
        "next_action": built["next_action"],
        "preflight_actions": built.get("preflight_actions", []),
        "supported_screens": built["supported_screens"],
        "supported_auth_modes": built["supported_auth_modes"],
        "supported_presets": built["supported_presets"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
