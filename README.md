# My Codex Skills

Personal Codex skill repository for repeatable local workflows.

## Skills

```text
skills/
  export/
  test-init/
  test-start/
```

| Skill | Purpose | Path |
| --- | --- | --- |
| `export` | Export the current Codex session into a readable Markdown record | `skills/export` |
| `test-init` | Create or extend a reusable test-entry contract for SPA-style web game demos | `skills/test-init` |
| `test-start` | Launch a local dev server and return one contract-approved launch URL | `skills/test-start` |

## Installation

Clone this repository and copy the desired skill folders into your local Codex skills directory.

Typical local target:

```text
C:/Users/<you>/.codex/skills/
```

Example:

```powershell
Copy-Item -Recurse -Force .\skills\test-start C:\Users\<you>\.codex\skills\test-start
Copy-Item -Recurse -Force .\skills\test-init C:\Users\<you>\.codex\skills\test-init
```

## `test-start`

`test-start` consumes an existing `test-entry-summary` contract and returns one verified local URL.

Use it when you want to:

- start the current project's local test-entry environment
- get one launch URL without re-reading project internals
- open a supported screen directly
- avoid occupied localhost ports
- route unsupported screens back to `test-init`

### What It Does

- validates `test-entry-summary.json`
- plans a free local port
- starts the dev server with platform-safe executable handling
- verifies HTTP readiness
- returns one contract-approved launch URL

### What It Does Not Do

- modify the project test-entry base
- invent unsupported screens
- use UI traversal to simulate unsupported pages
- treat a running process as success without HTTP verification

### Important Execution Rule

Bundled scripts are resolved from the skill directory, but they must run with the shell working directory kept at the target project root.

Correct pattern:

```powershell
python C:/Users/<you>/.codex/skills/test-start/scripts/check_summary.py
```

Run that command while your shell is already in the target project root.

### Launch Behavior

`test-start` now prefers the safest contract-defined path:

- If the project contract defines `preferred_direct_launch`, normal launch returns that direct URL instead of forcing the raw homepage.
- If you request a specific screen or preset and the contract supports `bypass`, `test-start` defaults to `testAuth=bypass` unless you explicitly ask for another auth mode.
- If normal launch includes contract-defined preflight query parameters, the returned URL must be used exactly as produced.

### Typical Usage

Ask Codex:

```text
$test-start 给我一个基础链接
```

Possible result:

```text
http://127.0.0.1:4174/?testEntry=1&testScreen=champion-select&testAuth=bypass&testPreset=champion-select-default
```

Ask for a specific module:

```text
$test-start 打开 shop 页面
```

Expected contract-style result:

```text
http://127.0.0.1:4174/?testEntry=1&testScreen=shop&testAuth=bypass
```

### Main Scripts

- `scripts/check_summary.py`
- `scripts/plan_dev_server.py`
- `scripts/start_dev_server.py`
- `scripts/finalize_launch.py`
- `scripts/record_verified_alias.py`

## `test-init`

`test-init` is the producer of the persistent public test-entry contract.

Use it when:

- the project has no valid `test-entry-summary`
- a downstream skill reports `next_action=use-test-init`
- a requested screen is truly unsupported and must be added permanently

### What It Produces

- URL-based `testEntry` protocol support
- dev/test-only `window.__TEST_ENTRY__`
- stable public screen names
- updated `test-entry-summary.json`

### Important Execution Rule

Just like `test-start`, resolve scripts from the skill directory but keep the shell working directory at the target project root.

Typical commands:

```powershell
python C:/Users/<you>/.codex/skills/test-init/scripts/check_summary.py
python C:/Users/<you>/.codex/skills/test-init/scripts/inspect_project.py
```

### Typical Usage

Ask Codex:

```text
$test-init 给这个项目补 test-entry
```

Or when extending an existing contract:

```text
$test-init 把 backpack 页面正式加进 test-entry-summary
```

## Workflow Recommendation

For web-game demo projects, the intended order is:

1. Use `test-init` once to create or extend the contract.
2. Use `test-start` to start the project and return a verified launch URL.
3. Use downstream skills such as screenshot or page-check workflows on top of the returned URL.

## Notes

- These skills are optimized for SPA-style web game demos.
- `test-start` is a consumer of the contract.
- `test-init` is the producer of the contract.
- If the contract and implementation disagree, fix the project with `test-init` rather than inventing ad hoc URLs.
