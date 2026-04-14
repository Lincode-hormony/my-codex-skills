from __future__ import annotations

import json
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
        "missing_required_fields": [],
        "supported_screens": [],
    }

    if payload is None:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    result["missing_required_fields"] = missing
    result["supported_screens"] = payload.get("supported_screens", [])
    result["valid"] = (
        payload.get("test_entry_supported") is True and len(missing) == 0
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
