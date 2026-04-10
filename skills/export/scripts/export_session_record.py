#!/usr/bin/env python3
"""Export a Codex rollout JSONL file into readable Markdown."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


HOME = Path.home()
DEFAULT_OUTPUT_DIR = Path.cwd() / "codex-exports"
CODEX_DIR = HOME / ".codex"
SKILL_DIR = Path(__file__).resolve().parent.parent
REFERENCE_PATH = SKILL_DIR / "references" / "session-storage.md"


@dataclass
class RenderedEvent:
    timestamp: str
    title: str
    body: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export a Codex session rollout to readable Markdown."
    )
    parser.add_argument("--rollout", help="Path to a rollout JSONL file")
    parser.add_argument("--session-id", help="Resolve a rollout by session id")
    parser.add_argument("--output-dir", help="Output directory for the markdown file")
    parser.add_argument("--file-name", help="Output markdown file name")
    parser.add_argument(
        "--file-name-escaped",
        help="Output markdown file name encoded with Python unicode escapes",
    )
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="Do not prompt for file name and output directory",
    )
    return parser.parse_args()


def prompt_with_default(label: str, default_value: str) -> str:
    raw = input(f"{label} [{default_value}]: ").strip()
    if not raw or raw.lower() == "default":
        return default_value
    return raw


def find_latest_rollout() -> Path:
    candidates = []
    for root in (CODEX_DIR / "sessions", CODEX_DIR / "archived_sessions"):
        if root.exists():
            candidates.extend(path for path in root.rglob("rollout-*.jsonl") if path.is_file())
    if not candidates:
        raise FileNotFoundError("No rollout JSONL files were found under ~/.codex.")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def decode_escaped_text(value: str) -> str:
    return bytes(value, "ascii").decode("unicode_escape")


def shell_safe_display(value: str | Path) -> str:
    text = str(value)
    if text.isascii():
        return text
    return text.encode("unicode_escape").decode("ascii")


def iter_rollout_candidates() -> list[Path]:
    candidates: list[Path] = []
    for root in (CODEX_DIR / "sessions", CODEX_DIR / "archived_sessions"):
        if root.exists():
            candidates.extend(path for path in root.rglob("rollout-*.jsonl") if path.is_file())
    return sorted(candidates, key=lambda path: path.stat().st_mtime, reverse=True)


def find_rollout_by_session_id(session_id: str) -> Path:
    for path in iter_rollout_candidates():
        try:
            with path.open("r", encoding="utf-8") as handle:
                first_line = handle.readline().strip()
        except OSError:
            continue
        if not first_line:
            continue
        try:
            entry = json.loads(first_line)
        except json.JSONDecodeError:
            continue
        payload = entry.get("payload", {})
        if entry.get("type") == "session_meta" and payload.get("id") == session_id:
            return path
    raise FileNotFoundError(f"No rollout matched session id: {session_id}")


def load_memory_paths(reference_path: Path) -> list[tuple[str, str, str]]:
    lines = reference_path.read_text(encoding="utf-8").splitlines()
    rows: list[tuple[str, str, str]] = []
    in_table = False
    for line in lines:
        if line.strip() == "## Canonical paths":
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if not in_table:
            continue
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 3:
            continue
        if cells[0] in {"Type", "---"}:
            continue
        rows.append(tuple(cell.strip("`") for cell in cells))
    if not rows:
        raise ValueError(f"No canonical path table found in {reference_path}")
    return rows


def safe_json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)


def strip_ansi(text: str) -> str:
    output = []
    index = 0
    while index < len(text):
        if text[index] == "\x1b" and index + 1 < len(text) and text[index + 1] == "[":
            index += 2
            while index < len(text) and text[index] not in "ABCDEFGHJKSTfmnsu":
                index += 1
            index += 1
            continue
        output.append(text[index])
        index += 1
    return "".join(output)


def extract_text_parts(content: list[dict[str, Any]] | None) -> str:
    if not content:
        return ""
    chunks: list[str] = []
    for item in content:
        item_type = item.get("type")
        if item_type in {"input_text", "output_text"}:
            text = item.get("text", "")
            if text:
                chunks.append(text)
        else:
            chunks.append(safe_json_dumps(item))
    return "\n\n".join(chunk.rstrip() for chunk in chunks if chunk.strip())


def format_message_block(role: str, payload: dict[str, Any]) -> str:
    phase = payload.get("phase")
    content = extract_text_parts(payload.get("content"))
    lines = [f"- role: `{role}`"]
    if phase:
        lines.append(f"- phase: `{phase}`")
    if content:
        lines.append("")
        lines.append(content)
    else:
        lines.append("")
        lines.append("```json")
        lines.append(safe_json_dumps(payload))
        lines.append("```")
    return "\n".join(lines).rstrip()


def format_function_call(payload: dict[str, Any]) -> str:
    lines = [f"- tool: `{payload.get('name', 'unknown')}`"]
    call_id = payload.get("call_id")
    if call_id:
        lines.append(f"- call_id: `{call_id}`")
    arguments = payload.get("arguments")
    if arguments:
        lines.append("")
        lines.append("```json")
        try:
            lines.append(safe_json_dumps(json.loads(arguments)))
        except json.JSONDecodeError:
            lines.append(arguments)
        lines.append("```")
    return "\n".join(lines).rstrip()


def format_function_output(payload: dict[str, Any]) -> str:
    lines = [f"- call_id: `{payload.get('call_id', 'unknown')}`"]
    output = payload.get("output", "")
    if output:
        lines.append("")
        lines.append("```text")
        lines.append(strip_ansi(output).rstrip())
        lines.append("```")
    return "\n".join(lines).rstrip()


def format_event_payload(event_type: str, payload: dict[str, Any]) -> str:
    if event_type == "user_message":
        message = payload.get("message", "")
        return message or safe_json_dumps(payload)
    if event_type == "agent_message":
        lines = []
        phase = payload.get("phase")
        if phase:
            lines.append(f"- phase: `{phase}`")
        message = payload.get("message", "")
        if lines:
            lines.append("")
        lines.append(message or safe_json_dumps(payload))
        return "\n".join(lines).rstrip()
    if event_type == "exec_command_end":
        lines = []
        command = payload.get("command")
        if command:
            lines.append("```text")
            lines.append(" ".join(str(part) for part in command))
            lines.append("```")
        summary = {
            "cwd": payload.get("cwd"),
            "exit_code": payload.get("exit_code"),
            "status": payload.get("status"),
            "duration": payload.get("duration"),
        }
        lines.append("```json")
        lines.append(safe_json_dumps(summary))
        lines.append("```")
        aggregated = payload.get("aggregated_output")
        if aggregated:
            lines.append("")
            lines.append("```text")
            lines.append(strip_ansi(aggregated).rstrip())
            lines.append("```")
        return "\n".join(lines).rstrip()
    if event_type == "token_count":
        return "```json\n" + safe_json_dumps(payload) + "\n```"
    if event_type == "web_search_end":
        action = payload.get("action")
        lines = []
        query = payload.get("query")
        if query:
            lines.append(f"- query: `{query}`")
        if action:
            lines.append("")
            lines.append("```json")
            lines.append(safe_json_dumps(action))
            lines.append("```")
        return "\n".join(lines).rstrip()
    return "```json\n" + safe_json_dumps(payload) + "\n```"


def render_entry(index: int, entry: dict[str, Any]) -> RenderedEvent | None:
    timestamp = entry.get("timestamp", "")
    entry_type = entry.get("type", "unknown")
    payload = entry.get("payload", {})

    if entry_type == "session_meta":
        return None
    if entry_type == "response_item":
        payload_type = payload.get("type", "unknown")
        if payload_type == "message":
            role = payload.get("role", "unknown")
            title = f"{index:04d} {role.title()} Message"
            return RenderedEvent(timestamp, title, format_message_block(role, payload))
        if payload_type == "function_call":
            title = f"{index:04d} Tool Call"
            return RenderedEvent(timestamp, title, format_function_call(payload))
        if payload_type == "function_call_output":
            title = f"{index:04d} Tool Output"
            return RenderedEvent(timestamp, title, format_function_output(payload))
        title = f"{index:04d} Response Item: {payload_type}"
        return RenderedEvent(
            timestamp,
            title,
            "```json\n" + safe_json_dumps(payload) + "\n```",
        )
    if entry_type == "event_msg":
        event_type = payload.get("type", "unknown")
        title = f"{index:04d} Runtime Event: {event_type}"
        return RenderedEvent(timestamp, title, format_event_payload(event_type, payload))
    title = f"{index:04d} Raw Entry: {entry_type}"
    return RenderedEvent(timestamp, title, "```json\n" + safe_json_dumps(entry) + "\n```")


def load_rollout(path: Path) -> tuple[dict[str, Any], list[RenderedEvent]]:
    session_meta: dict[str, Any] = {}
    rendered: list[RenderedEvent] = []
    with path.open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if entry.get("type") == "session_meta":
                session_meta = entry.get("payload", {})
                continue
            event = render_entry(index, entry)
            if event is not None:
                rendered.append(event)
    return session_meta, rendered


def markdown_table(rows: list[tuple[str, str, str]]) -> str:
    lines = ["| Type | Location | Description |", "| --- | --- | --- |"]
    for kind, location, note in rows:
        lines.append(f"| {kind} | `{location}` | {note} |")
    return "\n".join(lines)


def build_markdown(
    rollout_path: Path,
    output_path: Path,
    session_meta: dict[str, Any],
    rendered_events: list[RenderedEvent],
    memory_paths: list[tuple[str, str, str]],
) -> str:
    export_time = datetime.now().astimezone().isoformat(timespec="seconds")
    lines = [
        "# Session Record",
        "",
        "- format: `readable-markdown`",
        "- export_scope: `snapshot-at-export-start`",
        f"- export_time: `{export_time}`",
        f"- source_rollout: `{rollout_path}`",
        f"- output_file: `{output_path}`",
    ]
    if session_meta:
        if session_meta.get("id"):
            lines.append(f"- session_id: `{session_meta['id']}`")
        if session_meta.get("timestamp"):
            lines.append(f"- session_start: `{session_meta['timestamp']}`")
        if session_meta.get("cwd"):
            lines.append(f"- cwd: `{session_meta['cwd']}`")
        if session_meta.get("cli_version"):
            lines.append(f"- cli_version: `{session_meta['cli_version']}`")
        if session_meta.get("model_provider"):
            lines.append(f"- model_provider: `{session_meta['model_provider']}`")

    lines.extend(
        [
            "",
            "## Timeline",
            "",
            "Events are kept in original rollout order and rendered into terminal-readable blocks.",
        ]
    )

    for event in rendered_events:
        lines.extend(
            [
                "",
                f"### [{event.timestamp}] {event.title}",
                "",
                event.body.rstrip(),
            ]
        )

    lines.extend(
        [
            "",
            "## Source Files",
            "",
            markdown_table(
                [
                    ("Current rollout", str(rollout_path), "Direct source for this export"),
                    ("Session directory", str(CODEX_DIR / "sessions"), "Active rollout directory"),
                    ("Archive directory", str(CODEX_DIR / "archived_sessions"), "Archived rollout directory"),
                    ("History index", str(CODEX_DIR / "history.jsonl"), "Cross-session text history"),
                    ("Session index", str(CODEX_DIR / "session_index.jsonl"), "Session id and title index"),
                    ("Global state", str(CODEX_DIR / ".codex-global-state.json"), "Workspace and global preferences"),
                    ("Config file", str(CODEX_DIR / "config.toml"), "Model and project configuration"),
                    ("State database", str(CODEX_DIR / "state_5.sqlite"), "Internal state database"),
                    ("Logs database", str(CODEX_DIR / "logs_1.sqlite"), "Internal logs database"),
                ]
            ),
            "",
            "## Memory File Locations",
            "",
            markdown_table(memory_paths),
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    if args.rollout and args.session_id:
        raise ValueError("Use either --rollout or --session-id, not both.")
    if args.rollout:
        rollout_path = Path(args.rollout).expanduser()
    elif args.session_id:
        rollout_path = find_rollout_by_session_id(args.session_id)
    else:
        rollout_path = find_latest_rollout()
    if not rollout_path.exists():
        raise FileNotFoundError(f"Rollout file not found: {rollout_path}")

    default_name = f"session-record-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}.md"
    output_dir = Path(args.output_dir).expanduser() if args.output_dir else DEFAULT_OUTPUT_DIR
    file_name = (
        decode_escaped_text(args.file_name_escaped)
        if args.file_name_escaped
        else args.file_name or default_name
    )

    if not args.no_prompt:
        file_name = prompt_with_default("File name", file_name)
        output_dir = Path(prompt_with_default("Output directory", str(output_dir))).expanduser()

    if not file_name.lower().endswith(".md"):
        file_name += ".md"

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / file_name

    session_meta, rendered_events = load_rollout(rollout_path)
    memory_paths = load_memory_paths(REFERENCE_PATH)
    markdown = build_markdown(rollout_path, output_path, session_meta, rendered_events, memory_paths)
    output_path.write_text(markdown, encoding="utf-8")

    print(f"[ok] source rollout: {shell_safe_display(rollout_path)}")
    print(f"[ok] exported markdown: {shell_safe_display(output_path)}")
    if not str(output_path).isascii():
        print(f"[ok] exported markdown unicode: {output_path}")
    print(f"[ok] event count: {len(rendered_events)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
