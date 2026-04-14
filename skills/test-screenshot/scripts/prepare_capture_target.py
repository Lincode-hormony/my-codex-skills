from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlencode


def load_summary(root: Path):
    for candidate in [root / "test-entry-summary.json", root / "docs" / "test-entry-summary.json"]:
        if candidate.exists():
            return candidate, json.loads(candidate.read_text(encoding="utf-8-sig"))
    return None, None


def verify_base_url(url: str, timeout: float):
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


def screen_map(summary: dict) -> dict[str, dict]:
    mapping = {}
    for item in summary.get("supported_screens", []):
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            mapping[item["name"]] = item
        elif isinstance(item, str):
            mapping[item] = {"name": item, "screenshot_ready": False}
    return mapping


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--screen")
    parser.add_argument("--auth")
    parser.add_argument("--preset")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--capture-request-file")
    args = parser.parse_args()

    _, summary = load_summary(Path.cwd())
    if summary is None:
        print(json.dumps({"ok": False, "mode": "provided-url" if not args.screen and not args.preset else "screen", "url": None, "status_code": None, "content_type": None, "diagnosis": "No summary file found", "next_action": "use-test-init", "supported_screens": [], "supported_auth_modes": [], "supported_presets": [], "ready_strategy": None, "wait_selector": None, "wait_expression": None}, ensure_ascii=False, indent=2))
        return 0

    base_check = verify_base_url(args.base_url, args.timeout)
    if not base_check["ok"]:
        print(json.dumps({"ok": False, "mode": "provided-url" if not args.screen and not args.preset else "screen", "url": None, "status_code": base_check["status_code"], "content_type": base_check["content_type"], "diagnosis": base_check["diagnosis"], "next_action": "fix-base-url", "supported_screens": [item["name"] if isinstance(item, dict) else item for item in summary.get("supported_screens", [])], "supported_auth_modes": summary.get("supported_auth_modes", []), "supported_presets": summary.get("supported_presets", []), "ready_strategy": None, "wait_selector": None, "wait_expression": None}, ensure_ascii=False, indent=2))
        return 0

    supported_screen_map = screen_map(summary)
    supported_screens = list(supported_screen_map.keys())
    supported_auth_modes = list(summary.get("supported_auth_modes", []))
    supported_presets = list(summary.get("supported_presets", []))

    if args.screen and args.screen not in supported_screens:
        diagnosis, next_action, ready_strategy, url = f"Unsupported screen: {args.screen}", "offer-supported-or-test-init", None, None
    elif args.auth and args.auth not in supported_auth_modes:
        diagnosis, next_action, ready_strategy, url = f"Unsupported auth mode: {args.auth}", "offer-supported-or-test-init", None, None
    elif args.preset and args.preset not in supported_presets:
        diagnosis, next_action, ready_strategy, url = f"Unsupported preset: {args.preset}", "offer-supported-or-test-init", None, None
    else:
        effective_auth = args.auth or ("bypass" if (args.screen or args.preset) and "bypass" in supported_auth_modes else None)
        params = {"testEntry": "1"}
        if args.screen:
            params["testScreen"] = args.screen
        if effective_auth:
            params["testAuth"] = effective_auth
        if args.preset:
            params["testPreset"] = args.preset
        url = args.base_url if not args.screen and not args.preset and not args.auth else args.base_url.rstrip("/") + "/?" + urlencode(params)
        diagnosis, next_action = "Contract-based screenshot URL", "proceed"
        ready_strategy = supported_screen_map.get(args.screen, {}).get("ready_strategy") if args.screen else None

    wait_selector = None
    wait_expression = None
    wait_images = False
    if isinstance(ready_strategy, dict):
        kind = ready_strategy.get("kind")
        if kind == "selector" and isinstance(ready_strategy.get("selector"), str):
            wait_selector = ready_strategy["selector"]
            wait_images = True
        elif kind == "js-expression" and isinstance(ready_strategy.get("expression"), str):
            wait_expression = ready_strategy["expression"]
            wait_images = True
        else:
            next_action = "offer-supported-or-test-init"
            diagnosis = "Unsupported or incomplete ready strategy for screenshot capture"

    capture_request = None
    if next_action == "proceed":
        capture_request = {
            "url": url,
            "wait_selector": wait_selector,
            "wait_expression": wait_expression,
            "wait_images": wait_images,
            "asset_timeout": 5000,
        }
        if args.capture_request_file:
            target = Path(args.capture_request_file)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(capture_request, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"ok": next_action == "proceed", "mode": "provided-url" if not args.screen and not args.preset and not args.auth else "screen", "url": url, "status_code": base_check["status_code"], "content_type": base_check["content_type"], "diagnosis": diagnosis, "next_action": next_action, "supported_screens": supported_screens, "supported_auth_modes": supported_auth_modes, "supported_presets": supported_presets, "ready_strategy": ready_strategy, "wait_selector": wait_selector, "wait_expression": wait_expression, "wait_images": wait_images, "capture_request_file": args.capture_request_file, "capture_request": capture_request}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
