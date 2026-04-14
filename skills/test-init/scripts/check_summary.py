from __future__ import annotations

import json
from pathlib import Path


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


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def main() -> int:
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
        "protocol_supported": False,
        "reason": None,
        "missing_required_fields": [],
        "missing_command_fields": [],
        "supported_screens": [],
        "launch_mode": None,
        "protocol_version": None,
    }

    if payload is None:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    commands = payload.get("commands", {}) if isinstance(payload.get("commands"), dict) else {}
    missing_command_fields = [
        field for field in REQUIRED_COMMAND_KEYS if not commands.get(field)
    ]
    protocol_version = str(payload.get("protocol_version", ""))
    launch_mode = payload.get("launch_mode")
    protocol_supported = protocol_version == "2" and launch_mode == "build-preview"

    result["missing_required_fields"] = missing
    result["missing_command_fields"] = missing_command_fields
    result["supported_screens"] = payload.get("supported_screens", [])
    result["launch_mode"] = launch_mode
    result["protocol_version"] = protocol_version
    result["protocol_supported"] = protocol_supported

    if payload.get("test_entry_supported") is not True:
        result["reason"] = "test_entry_not_supported"
    elif protocol_version != "2":
        result["reason"] = "unsupported_protocol_version"
    elif launch_mode != "build-preview":
        result["reason"] = "unsupported_launch_mode"
    elif missing:
        result["reason"] = "missing_required_fields"
    elif missing_command_fields:
        result["reason"] = "missing_command_fields"
    else:
        result["reason"] = "proceed"

    result["valid"] = result["reason"] == "proceed"

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
