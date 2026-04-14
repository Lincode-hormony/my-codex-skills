from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REQUIRED_FIELDS = [
    "test_entry_supported", "project_type", "protocol_version", "launch_mode", "commands",
    "entry_url_examples", "bridge_available", "bridge_name", "supported_screens",
    "supported_auth_modes", "supported_presets", "supported_features",
    "recommended_entry_flow", "test_series_readiness", "limitations", "validation",
]
REQUIRED_COMMAND_KEYS = ["build_test_entry", "preview_test_entry"]


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def normalize_optional(value: str | None) -> str | None:
    return value.strip() or None if value is not None else None


def canonicalize_screen_label(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", value.lower())


def normalize_supported_screens(supported_screens: list) -> tuple[list[str], dict[str, dict]]:
    names, mapping = [], {}
    for item in supported_screens:
        if isinstance(item, str):
            names.append(item)
            mapping[item] = {"name": item, "screenshot_ready": False}
        elif isinstance(item, dict) and isinstance(item.get("name"), str):
            names.append(item["name"])
            mapping[item["name"]] = item
    return names, mapping


def load_verified_aliases(root: Path):
    for candidate in [root / "test-screen-aliases.json", root / "docs" / "test-screen-aliases.json"]:
        if candidate.exists():
            payload = load_json(candidate)
            if isinstance(payload, dict) and isinstance(payload.get("aliases"), dict):
                return candidate, payload["aliases"]
    return None, {}


def normalize_requested_screen(requested_screen: str | None, supported_screens: list[str], verified_aliases: dict) -> tuple[str | None, str | None]:
    if requested_screen is None:
        return None, None
    if requested_screen in supported_screens:
        return requested_screen, None
    supported_by_key = {canonicalize_screen_label(screen): screen for screen in supported_screens}
    direct_key = canonicalize_screen_label(requested_screen)
    if direct_key in supported_by_key:
        return supported_by_key[direct_key], "direct-normalization"
    for alias, target in verified_aliases.items():
        if not isinstance(alias, str):
            continue
        if isinstance(target, str):
            resolved_target = target
            alias_key = canonicalize_screen_label(alias)
        elif isinstance(target, dict):
            resolved_target = target.get("screen")
            alias_key = target.get("alias_key") or canonicalize_screen_label(alias)
        else:
            continue
        if isinstance(resolved_target, str) and resolved_target in supported_screens and alias_key == direct_key:
            return resolved_target, "verified-alias"
    return requested_screen, None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requested-screen")
    parser.add_argument("--requested-auth")
    parser.add_argument("--requested-preset")
    args = parser.parse_args()

    requested_screen = normalize_optional(args.requested_screen)
    requested_auth = normalize_optional(args.requested_auth)
    requested_preset = normalize_optional(args.requested_preset)
    root = Path.cwd()

    found_path = None
    payload = None
    for candidate in [root / "test-entry-summary.json", root / "docs" / "test-entry-summary.json"]:
        if candidate.exists():
            found_path = candidate
            payload = load_json(candidate)
            break

    result = {
        "exists": found_path is not None, "path": str(found_path) if found_path else None,
        "valid": False, "protocol_supported": False, "missing_required_fields": [],
        "missing_command_fields": [], "supported_screens": [], "screenshot_ready_screens": [],
        "supported_auth_modes": [], "supported_presets": [], "verified_alias_file": None,
        "requested_screen": requested_screen, "normalized_screen": requested_screen,
        "screen_match_kind": None, "requested_auth": requested_auth, "requested_preset": requested_preset,
        "requested_screen_supported": None, "requested_screen_capture_ready": None,
        "requested_auth_supported": None, "requested_preset_supported": None,
        "launch_mode": None, "protocol_version": None, "next_action": "use-test-init",
        "reason": "summary_missing",
    }
    if payload is None:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    commands = payload.get("commands", {}) if isinstance(payload.get("commands"), dict) else {}
    missing_command_fields = [field for field in REQUIRED_COMMAND_KEYS if not commands.get(field)]
    supported_screen_names, supported_screen_map = normalize_supported_screens(payload.get("supported_screens", []))
    result["missing_required_fields"] = missing
    result["missing_command_fields"] = missing_command_fields
    result["supported_screens"] = supported_screen_names
    result["screenshot_ready_screens"] = [name for name, spec in supported_screen_map.items() if spec.get("screenshot_ready") is True and isinstance(spec.get("ready_strategy"), dict)]
    result["supported_auth_modes"] = payload.get("supported_auth_modes", [])
    result["supported_presets"] = payload.get("supported_presets", [])
    result["launch_mode"] = payload.get("launch_mode")
    result["protocol_version"] = str(payload.get("protocol_version", ""))
    result["protocol_supported"] = result["protocol_version"] == "2" and result["launch_mode"] == "build-preview"
    result["valid"] = payload.get("test_entry_supported") is True and result["protocol_supported"] and not missing and not missing_command_fields
    alias_path, verified_aliases = load_verified_aliases(root)
    result["verified_alias_file"] = str(alias_path) if alias_path else None

    if not result["valid"]:
        if payload.get("test_entry_supported") is not True:
            result["reason"] = "summary_invalid"
        elif result["protocol_version"] != "2":
            result["reason"] = "unsupported_protocol_version"
        elif result["launch_mode"] != "build-preview":
            result["reason"] = "unsupported_launch_mode"
        elif missing:
            result["reason"] = "summary_invalid"
        else:
            result["reason"] = "missing_command_fields"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    normalized_screen, screen_match_kind = normalize_requested_screen(requested_screen, supported_screen_names, verified_aliases)
    result["normalized_screen"] = normalized_screen
    result["screen_match_kind"] = screen_match_kind
    if requested_screen is not None:
        result["requested_screen_supported"] = normalized_screen in supported_screen_names
        if result["requested_screen_supported"]:
            spec = supported_screen_map.get(normalized_screen, {})
            result["requested_screen_capture_ready"] = spec.get("screenshot_ready") is True and isinstance(spec.get("ready_strategy"), dict)
    if requested_auth is not None:
        result["requested_auth_supported"] = requested_auth in result["supported_auth_modes"]
    if requested_preset is not None:
        result["requested_preset_supported"] = requested_preset in result["supported_presets"]

    if requested_screen is not None and result["requested_screen_supported"] is False:
        result["next_action"] = "offer-supported-or-test-init"
        result["reason"] = "unsupported_screen"
    elif requested_screen is not None and result["requested_screen_capture_ready"] is False:
        result["next_action"] = "offer-supported-or-test-init"
        result["reason"] = "screen_not_capture_ready"
    elif requested_auth is not None and result["requested_auth_supported"] is False:
        result["next_action"] = "offer-supported-or-test-init"
        result["reason"] = "unsupported_auth"
    elif requested_preset is not None and result["requested_preset_supported"] is False:
        result["next_action"] = "offer-supported-or-test-init"
        result["reason"] = "unsupported_preset"
    else:
        result["next_action"] = "proceed"
        result["reason"] = "ready"

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
