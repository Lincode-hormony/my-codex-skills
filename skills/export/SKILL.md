---
name: export
description: Exports the current Codex session into a readable Markdown record with chat content, tool calls, runtime events, and source file locations. Use when the user wants the current session transcript exported to a file.
---

# Exporting Session Records

Use this skill when the user wants the current session exported as a readable Markdown file.

## Default behavior

- Keep the main path short.
- Ask only two questions before execution:
  - file name
  - output directory
- If the user replies with `default`, empty text, or equivalent, use the script defaults.
- After collecting those two values, run the bundled script immediately.

## Main workflow

1. Ask for the file name in the user's language.
2. Ask for the output directory in the user's language.
3. Run the script with explicit arguments instead of relying on interactive prompts.
4. Report the final output path and the source rollout path.

## Command

Preferred command:

```bash
python scripts/export_session_record.py --no-prompt --file-name "<name>.md" --output-dir "<dir>"
```

If the user wants defaults, use:

- file name: `session-record-YYYY-MM-DD-HHMMSS.md`
- output directory: `./codex-exports/`

## Scope

- By default, `current session` means the latest available session snapshot at the moment export starts.
- Keep original rollout order.
- Include messages, tool calls, tool outputs, runtime events, source file paths, and memory file locations.

## Only if needed

- If the user gives a specific rollout file, pass `--rollout`.
- If the user gives a specific session id, pass `--session-id`.
- On Windows PowerShell, if a non-ASCII file name is risky, use `--file-name-escaped`.
- The canonical memory-path table lives in [references/session-storage.md](references/session-storage.md).
