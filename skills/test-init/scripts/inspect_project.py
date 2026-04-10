#!/usr/bin/env python3
"""Inspect a frontend project for web-game test-entry integration signals.

Outputs structured JSON for the skill workflow.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SKIP_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".codex-runtime",
    "codex-exports",
    ".worktrees",
    ".figma-cache",
}

SCAN_ROOT_HINTS = [
    "src",
    "scripts",
    "tests",
    "public",
]

PACKAGE_MARKERS = [
    "vite",
    "react",
    "vue",
    "playwright",
    "cypress",
]

ENTRY_CANDIDATES = [
    "src/App.jsx",
    "src/App.tsx",
    "src/main.jsx",
    "src/main.tsx",
    "src/main.js",
]

TEST_ENTRY_PATTERNS = {
    "query-debug": re.compile(r"debug(Screen|State|Auth|Mode|View)", re.IGNORECASE),
    "hash-debug": re.compile(r"#qa-|hash", re.IGNORECASE),
    "bridge-object": re.compile(r"__TEST_ENTRY__"),
    "test-id": re.compile(r"data-testid"),
    "playwright-script": re.compile(r"playwright|chromium\.launch", re.IGNORECASE),
    "cypress-script": re.compile(r"cypress|cy\.", re.IGNORECASE),
    "state-machine": re.compile(r"\b(view|scene|mode)\b"),
}


def safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        return ""


def detect_framework_signals(root: Path) -> list[str]:
    package_json = root / "package.json"
    text = safe_read(package_json)
    if not text:
        return []

    signals = []
    for marker in PACKAGE_MARKERS:
        if marker in text:
            signals.append(marker)
    return signals


def detect_entry_files(root: Path) -> list[str]:
    found = []
    for rel in ENTRY_CANDIDATES:
        path = root / rel
        if path.exists():
            found.append(rel)
    return found


def detect_test_entry_signals(root: Path) -> list[str]:
    hits: set[str] = set()
    scan_roots = [root / hint for hint in SCAN_ROOT_HINTS if (root / hint).exists()]
    if not scan_roots:
        scan_roots = [root]

    for base in scan_roots:
        for path in base.rglob("*"):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".json", ".md"}:
                continue
            text = safe_read(path)
            if not text:
                continue
            for name, pattern in TEST_ENTRY_PATTERNS.items():
                if pattern.search(text):
                    hits.add(name)
    return sorted(hits)


def classify_project(framework_signals: list[str], entry_files: list[str], signal_hits: list[str]) -> tuple[str, str]:
    if "vite" in framework_signals and any(sig in framework_signals for sig in ("react", "vue")) and entry_files:
        confidence = "high" if "state-machine" in signal_hits else "medium"
        return "spa_web_game_demo", confidence
    if entry_files:
        return "frontend_spa_candidate", "medium"
    return "unknown", "low"


def recommend_pattern(signal_hits: list[str]) -> str:
    if "query-debug" in signal_hits:
        return "query-first"
    if "hash-debug" in signal_hits:
        return "hash-first"
    if "state-machine" in signal_hits:
        return "state-machine-first"
    return "manual-review"


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    if not root.exists():
        print(
            json.dumps(
                {
                    "project_type": "unknown",
                    "confidence": "low",
                    "framework_signals": [],
                    "entry_files": [],
                    "existing_test_entry_signals": [],
                    "recommended_pattern": "manual-review",
                    "risks": [f"Project root does not exist: {root}"],
                },
                indent=2,
                ensure_ascii=True,
            )
        )
        return 1

    framework_signals = detect_framework_signals(root)
    entry_files = detect_entry_files(root)
    signal_hits = detect_test_entry_signals(root)
    project_type, confidence = classify_project(framework_signals, entry_files, signal_hits)

    risks = []
    if project_type == "unknown":
        risks.append("Could not confidently classify the project as a SPA-style web game demo.")
    if "bridge-object" not in signal_hits:
        risks.append("No existing test-entry bridge object detected.")
    if "query-debug" not in signal_hits and "hash-debug" not in signal_hits:
        risks.append("No obvious debug URL entry signal detected.")

    result = {
        "project_type": project_type,
        "confidence": confidence,
        "framework_signals": framework_signals,
        "entry_files": entry_files,
        "existing_test_entry_signals": signal_hits,
        "recommended_pattern": recommend_pattern(signal_hits),
        "risks": risks,
    }
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
