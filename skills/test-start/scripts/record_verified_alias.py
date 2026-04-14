from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def load_summary(root: Path):
    for candidate in [root / "test-entry-summary.json", root / "docs" / "test-entry-summary.json"]:
        if candidate.exists():
            return candidate, json.loads(candidate.read_text(encoding="utf-8"))
    return None, None


def canonicalize_alias(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", value.lower())


def load_alias_file(path: Path):
    if not path.exists():
        return {"aliases": {}, "evidence": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return {"aliases": {}, "evidence": []}
        payload.setdefault("aliases", {})
        payload.setdefault("evidence", [])
        return payload
    except Exception:
        return {"aliases": {}, "evidence": []}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--alias", required=True)
    parser.add_argument("--screen", required=True)
    parser.add_argument("--evidence", required=True)
    args = parser.parse_args()

    root = Path.cwd()
    _, summary = load_summary(root)
    result = {
        "ok": False,
        "path": None,
        "alias": args.alias,
        "screen": args.screen,
        "diagnosis": None,
    }

    if summary is None:
        result["diagnosis"] = "No summary file found"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    supported_screens = summary.get("supported_screens", [])
    if args.screen not in supported_screens:
        result["diagnosis"] = f"Unsupported screen: {args.screen}"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    alias_path = root / "test-screen-aliases.json"
    payload = load_alias_file(alias_path)
    payload["aliases"][args.alias] = {
        "screen": args.screen,
        "alias_key": canonicalize_alias(args.alias),
    }
    payload["evidence"].append(
        {
            "alias": args.alias,
            "alias_key": canonicalize_alias(args.alias),
            "screen": args.screen,
            "evidence": args.evidence,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    alias_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result["ok"] = True
    result["path"] = str(alias_path)
    result["diagnosis"] = "Recorded verified alias"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
