# Session Storage

Use this file when the user asks where Codex stores session history, rollout logs, memory indexes, or global state.

The export script treats the table below as the canonical source for memory-file locations.

## Canonical paths

| Type | Location | Description |
| --- | --- | --- |
| Session raw record | `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` | Daily rollout source files and the primary source for current-session export. |
| Archived session record | `~/.codex/archived_sessions/rollout-*.jsonl` | Archived historical rollout files. |
| History index | `~/.codex/history.jsonl` | Cross-session text history. |
| Session index | `~/.codex/session_index.jsonl` | Session id and title index. |
| Global state | `~/.codex/.codex-global-state.json` | Workspace and global preferences. |
| Config file | `~/.codex/config.toml` | Model and project configuration. |
| State database | `~/.codex/state_5.sqlite` | Internal state database. |
| Logs database | `~/.codex/logs_1.sqlite` | Internal logs database. |

## Selection rules

- For the current session, start with the newest matching file in `~/.codex/sessions/`.
- If the session has been moved out of the active tree, check `~/.codex/archived_sessions/`.
- Use `session_index.jsonl` only to map ids and titles. Do not treat it as the primary transcript source.
- Use `history.jsonl` as a cross-session text reference, not as the canonical per-session event log.
- Mention SQLite paths in the exported document, but do not read database contents unless the user explicitly requests a deeper forensic export.
