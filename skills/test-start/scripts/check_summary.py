from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REQUIRED_FIELDS = [
    "test_entry_supported",
    "project_type",
    "protocol_version",
    "entry_url_examples",
    "bridge_available",
    "bridge_name",
    "supported_screens",
    "supported_auth_modes",
    "supported_presets",
    "supported_features",
    "recommended_entry_flow",
    "limitations",
]


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def canonicalize_screen_label(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", value.lower())


def load_verified_aliases(root: Path):
    candidates = [
        root / "test-screen-aliases.json",
        root / "docs" / "test-screen-aliases.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            payload = load_json(candidate)
            if isinstance(payload, dict):
                aliases = payload.get("aliases", {})
                if isinstance(aliases, dict):
                    return candidate, aliases
    return None, {}


def normalize_requested_screen(
    requested_screen: str | None,
    supported_screens: list[str],
    verified_aliases: dict,
) -> tuple[str | None, str | None]:
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
        if not isinstance(resolved_target, str):
            continue
        if resolved_target not in supported_screens:
            continue
        if alias_key == direct_key:
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
    candidates = [
        root / "test-entry-summary.json",
        root / "docs" / "test-entry-summary.json",
    ]

    found_path = None
    payload = None
    for candidate in candidates:
        if candidate.exists():
            found_path = candidate
            payload = load_json(candidate)
            break

    result = {
        "exists": found_path is not None,
        "path": str(found_path) if found_path else None,
        "valid": False,
        "missing_required_fields": [],
        "supported_screens": [],
        "supported_auth_modes": [],
        "supported_presets": [],
        "verified_alias_file": None,
        "requested_screen": requested_screen,
        "normalized_screen": requested_screen,
        "screen_match_kind": None,
        "requested_auth": requested_auth,
        "requested_preset": requested_preset,
        "requested_screen_supported": None,
        "requested_auth_supported": None,
        "requested_preset_supported": None,
        "next_action": "use-test-init",
        "reason": "summary_missing",
    }

    if payload is None:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    result["missing_required_fields"] = missing
    result["supported_screens"] = payload.get("supported_screens", [])
    result["supported_auth_modes"] = payload.get("supported_auth_modes", [])
    result["supported_presets"] = payload.get("supported_presets", [])
    result["valid"] = payload.get("test_entry_supported") is True and not missing
    alias_path, verified_aliases = load_verified_aliases(root)
    result["verified_alias_file"] = str(alias_path) if alias_path else None

    if not result["valid"]:
        result["reason"] = "summary_invalid"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    normalized_screen, screen_match_kind = normalize_requested_screen(
        requested_screen,
        result["supported_screens"],
        verified_aliases,
    )
    result["normalized_screen"] = normalized_screen
    result["screen_match_kind"] = screen_match_kind

    if requested_screen is not None:
        result["requested_screen_supported"] = normalized_screen in result["supported_screens"]
    if requested_auth is not None:
        result["requested_auth_supported"] = requested_auth in result["supported_auth_modes"]
    if requested_preset is not None:
        result["requested_preset_supported"] = requested_preset in result["supported_presets"]

    if requested_screen is not None and result["requested_screen_supported"] is False:
        result["next_action"] = "offer-supported-or-test-init"
        result["reason"] = "unsupported_screen"
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
