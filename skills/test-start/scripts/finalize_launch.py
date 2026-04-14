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


def verify_once(url: str, timeout: float):
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


def screen_names(summary: dict) -> list[str]:
    names = []
    for item in summary.get("supported_screens", []):
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, dict) and isinstance(item.get("name"), str):
            names.append(item["name"])
    return names


def build_contract_url(base_url: str, summary: dict, screen: str | None, auth: str | None, preset: str | None):
    supported_screens = screen_names(summary)
    supported_auth_modes = list(summary.get("supported_auth_modes", []))
    supported_presets = list(summary.get("supported_presets", []))
    if not screen and not preset and not auth:
        example_urls = summary.get("entry_url_examples", [])
        if example_urls and isinstance(example_urls[0], str):
            first = example_urls[0]
            return {"ok": True, "mode": "normal", "url": first if first.startswith("http") else base_url.rstrip("/") + "/" + first.lstrip("/"), "diagnosis": "Contract-approved entry URL from summary example", "next_action": "proceed", "supported_screens": supported_screens, "supported_auth_modes": supported_auth_modes, "supported_presets": supported_presets}
        return {"ok": True, "mode": "normal", "url": base_url.rstrip("/") + "/", "diagnosis": "Base preview URL", "next_action": "proceed", "supported_screens": supported_screens, "supported_auth_modes": supported_auth_modes, "supported_presets": supported_presets}
    if screen and screen not in supported_screens:
        return {"ok": False, "mode": "screen", "url": None, "diagnosis": f"Unsupported screen: {screen}", "next_action": "offer-supported-or-test-init", "supported_screens": supported_screens, "supported_auth_modes": supported_auth_modes, "supported_presets": supported_presets}
    if auth and auth not in supported_auth_modes:
        return {"ok": False, "mode": "screen", "url": None, "diagnosis": f"Unsupported auth mode: {auth}", "next_action": "offer-supported-or-test-init", "supported_screens": supported_screens, "supported_auth_modes": supported_auth_modes, "supported_presets": supported_presets}
    if preset and preset not in supported_presets:
        return {"ok": False, "mode": "screen", "url": None, "diagnosis": f"Unsupported preset: {preset}", "next_action": "offer-supported-or-test-init", "supported_screens": supported_screens, "supported_auth_modes": supported_auth_modes, "supported_presets": supported_presets}
    effective_auth = auth or ("bypass" if (screen or preset) and "bypass" in supported_auth_modes else None)
    params = {"testEntry": "1"}
    if screen:
        params["testScreen"] = screen
    if effective_auth:
        params["testAuth"] = effective_auth
    if preset:
        params["testPreset"] = preset
    return {"ok": True, "mode": "screen" if screen or preset else "auth", "url": base_url.rstrip("/") + "/?" + urlencode(params), "diagnosis": "Contract-based test-entry URL", "next_action": "proceed", "supported_screens": supported_screens, "supported_auth_modes": supported_auth_modes, "supported_presets": supported_presets}


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
        print(json.dumps({"ok": False, "status_code": None, "content_type": None, "mode": "normal" if not args.screen and not args.preset else "screen", "url": None, "diagnosis": "No summary file found", "next_action": "use-test-init", "supported_screens": [], "supported_auth_modes": [], "supported_presets": []}, ensure_ascii=False, indent=2))
        return 0
    base_check = verify_once(args.base_url, args.timeout)
    if not base_check["ok"]:
        print(json.dumps({"ok": False, "status_code": base_check["status_code"], "content_type": base_check["content_type"], "mode": "normal" if not args.screen and not args.preset else "screen", "url": None, "diagnosis": base_check["diagnosis"], "next_action": "fix-base-url", "supported_screens": screen_names(summary), "supported_auth_modes": summary.get("supported_auth_modes", []), "supported_presets": summary.get("supported_presets", [])}, ensure_ascii=False, indent=2))
        return 0
    built = build_contract_url(args.base_url, summary, args.screen, args.auth, args.preset)
    print(json.dumps({"ok": built["ok"], "status_code": base_check["status_code"], "content_type": base_check["content_type"], "mode": built["mode"], "url": built["url"], "diagnosis": built["diagnosis"], "next_action": built["next_action"], "supported_screens": built["supported_screens"], "supported_auth_modes": built["supported_auth_modes"], "supported_presets": built["supported_presets"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
