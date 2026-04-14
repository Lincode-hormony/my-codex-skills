---
name: test-init
description: "Builds or incrementally extends a persistent build-plus-preview test-entry base for SPA-style web apps so downstream skills can launch stable screens, inject test state, and capture screenshots from contract-defined ready states. Use when a project needs initial formal test integration, when an existing `test-entry-summary` is missing or invalid, or when a supported screen or ready contract must be added permanently."
---

# Test Init

Use this skill to create or extend the project's persistent test-entry base. This skill is the only producer of the public `test-entry-summary` contract.

Use this skill only for client-rendered web apps with meaningful client-side state control.

## What this skill produces

- A build-first test-entry protocol
- A persistent `window.__TEST_ENTRY__` bridge or equivalent public bridge
- Stable public screen names and screenshot-ready metadata
- Project-level build and preview commands for test runs
- Validation results for downstream reuse
- A persistent `test-entry-summary` contract

This skill does not manage long-running servers. Downstream launch and screenshot skills must consume the summary instead of re-reading project internals.

## First Decision

Before reading project internals or editing code:

1. run `python <skill-dir>/scripts/check_summary.py`
2. choose exactly one mode:
   - `initial integration` when no valid summary exists
   - `incremental extension` when a valid summary exists and the requested public screen or ready contract is missing

Do not describe the task as incremental extension until the summary check confirms that a valid summary already exists.

## Modes

- `initial integration`
  Use when the project has no valid `test-entry-summary` yet.
- `incremental extension`
  Use when the project already has a valid summary, but a requested screen, launch capability, or ready contract must be added permanently.

This skill is the only valid next step when a downstream launch or screenshot skill reports that the public contract is missing, stale, or incomplete.

## Default Workflow

Copy this checklist into working notes and keep the order:

```text
Test Init Progress:
- [ ] Step 1: Run summary check
- [ ] Step 2: Choose full path or incremental fast path
- [ ] Step 3: Gather only the required references
- [ ] Step 4: Inspect implementation in bounded scope
- [ ] Step 5: Implement the smallest public-contract change
- [ ] Step 6: Run validator loop
- [ ] Step 7: Update summary
- [ ] Step 8: Prepare handoff
```

Record one concrete artifact in working notes before moving to the next step:

- Step 1: summary-check JSON result and chosen mode
- Step 2: chosen path, either `full path` or `incremental fast path`
- Step 3: exact reference files read
- Step 4: exact files inspected and changed
- Step 5: smallest public-surface change actually made
- Step 6: validator result
- Step 7: updated summary path
- Step 8: downstream handoff statement

## Full Path

Use the full path for `initial integration`, for broken or stale summaries, or when the change affects launch commands, bridge shape, auth flow, or multiple screens.

1. Run the summary checker:
   ```bash
   python <skill-dir>/scripts/check_summary.py
   ```
2. If the user request is ambiguous, normalize it into one stable public screen name before editing. Do not guess between multiple plausible public names.
3. Run the project inspection script:
   ```bash
   python <skill-dir>/scripts/inspect_project.py
   ```
4. Record the inspection output, especially:
   - `build_preview_capability.level`
   - `build_preview_capability.impact`
   - `existing_test_entry_signals`
   - `recommended_pattern`
5. Read [references/project-detection.md](references/project-detection.md) if the script reports mixed signals or you are about to edit the project.
6. Read [references/build-first-protocol.md](references/build-first-protocol.md) for the canonical public contract.
7. Read [references/build-first-integration-patterns.md](references/build-first-integration-patterns.md) to choose the least invasive attachment point.
8. Read [references/ready-contract.md](references/ready-contract.md) before defining screenshot-ready behavior.
   Do not inspect implementation code until Steps 5-8 are complete.
9. Inspect project code in this order before broad repo searches:
   - build config and scripts
   - app root or main entry
   - auth gate or session restore path
   - screen, scene, mode, or view switch logic
   - state restore or local storage bootstrap
   - existing debug query, test query, or hash entry
10. Read [references/anti-patterns.md](references/anti-patterns.md) once before editing.
11. If the project has protected routes, login gating, session restoration, or if you plan to add or modify any auth mode, bypass flow, login shortcut, or session bootstrap, read [references/auth-chain-checks.md](references/auth-chain-checks.md) before editing auth-related code.
12. If a valid summary already exists, read [references/incremental-extension.md](references/incremental-extension.md) before changing supported screens or capabilities.
13. Add or extend only the public protocol surface that downstream skills need:
   - URL parsing for `testEntry` parameters
   - a public bridge such as `window.__TEST_ENTRY__`
   - stable `open()`, `reset()`, `getCapabilities()`, and screenshot-related behavior where supported
   - one or more stable target screens
   - explicit test build and preview commands
   - at least one ready strategy per screenshot-capable screen

## Incremental Fast Path

Use the incremental fast path only when all of the following are true:

- the summary is valid
- the bridge is already valid
- build and preview commands do not change
- the task is limited to one new screen, one preset, one ready strategy, or one small capability addition tied to an existing screen
- auth flow does not change materially

This path exists to minimize exploration and validation cost for small permanent additions.

1. Run the summary checker:
   ```bash
   python <skill-dir>/scripts/check_summary.py
   ```
2. Read the current `test-entry-summary.json` before touching code.
3. Read only these references:
   - [references/build-first-protocol.md](references/build-first-protocol.md)
   - [references/ready-contract.md](references/ready-contract.md)
   - [references/incremental-extension.md](references/incremental-extension.md)
4. If auth changes are truly involved, stop using the fast path and switch to the full path.
5. Inspect only the bounded implementation surface for the requested change:
   - the current bridge definition
   - current screen registry or screen switch logic
   - the target screen component or preset builder
   - the summary file
   Do not broad-search the repository unless this bounded read fails.
6. Add the smallest stable change that exposes the new screen or ready strategy through the existing protocol.
7. Update the summary in the same change.
8. Run the validator loop with a narrow validation target:
   - validate the new screen
   - revalidate one existing stable anchor screen
   - do not re-run a broad multi-screen sweep unless the validator reveals a compatibility break

## Shared Validation Loop

Validate the integration with [references/validation-checklist.md](references/validation-checklist.md) and [references/build-validation.md](references/build-validation.md).

Run the build-contract validator from the target project root:

```bash
python <skill-dir>/scripts/validate_build_contract.py [--summary <path>] [--base-url <preview-url>] [--ready-screen <screen>]
```

- If `--base-url` is available, runtime validation is required unless it is genuinely blocked.
- Let the validator choose the default ready screen automatically unless you need to override it.
- For incremental fast path work, validate the newly added screen first, then one stable existing anchor screen.
- Do not move to the final handoff until the validator output is recorded. If runtime validation is blocked, state the blocker and whether only static validation passed.

## Utility Scripts

- `scripts/check_summary.py`
  Run it from the target project root with `python <skill-dir>/scripts/check_summary.py`.
  It checks common summary locations in the current project and returns structured JSON with:
  - `exists`
  - `path`
  - `valid`
  - `missing_required_fields`
  - `supported_screens`

- `scripts/inspect_project.py`
  Run it from the target project root with `python <skill-dir>/scripts/inspect_project.py`.
  It returns structured JSON with:
  - `project_type`
  - `confidence`
  - `framework_signals`
  - `entry_files`
  - `existing_test_entry_signals`
  - `recommended_pattern`
  - `build_preview_capability`
  - `risks`

- `scripts/validate_build_contract.py`
  Run it from the target project root with `python <skill-dir>/scripts/validate_build_contract.py [--summary <path>] [--base-url <preview-url>] [--ready-screen <screen>]`.
  It validates:
  - required build-first summary fields
  - required build and preview commands
  - consumable ready-strategy definitions for screenshot-capable screens
  - HTTP reachability for the preview runtime and one contract entry URL when `--base-url` is provided
  - runtime readiness for one screenshot-capable screen when `--base-url` is provided
  - automatic selection of the first screenshot-capable screen when runtime validation is possible and `--ready-screen` is omitted

## Decision Rules

- Treat `test-entry-summary` as the only public contract for downstream skills.
- If the summary is missing or invalid, do `initial integration`.
- If the summary exists and the requested screen or ready contract is missing, do `incremental extension` instead of inventing ad hoc URLs.
- Resolve bundled scripts and references from this skill's own directory first.
- Resolve bundled script paths from this skill's own directory, but keep the command working directory at the target project root so the scripts inspect the repository instead of the skill folder.
- Ignore similarly named `test-init` folders inside the user repository unless the user explicitly asks to use that copy.
- If a bundled script or reference path fails, re-check the skill-local path first. Do not broad-search the repository before confirming the skill-local resource is truly unavailable.
- Extend the existing protocol. Do not create a second test-entry mechanism.
- Persist all supported screens, ready strategies, and launch capabilities in the repository. Do not rely on session-only patches.
- Prefer one or two stable additions over broad but fragile coverage.
- Keep the launch contract build-first. Do not ship a summary that lacks an explicit test build path and an explicit preview path.
- Treat screenshot suitability as a runtime-validation concern. Do not guess from static startup heuristics when build-preview validation can answer it directly.
- Prefer the incremental fast path for narrow additions, but leave it immediately if the change spills outside its allowed scope.

## Validation Gate

Do not consider the project ready unless all of the following are true:

- The project recognizes `testEntry=1`
- The public bridge exists in the test build runtime
- `getCapabilities()` returns structured data
- `open()` can enter at least one stable target screen without manual UI traversal
- `reset()` can clear or neutralize test-only state where supported
- The project exposes explicit test build and preview commands
- At least one supported screen has a declared ready strategy
- The final `test-entry-summary` matches the real supported surface
- The implementation, `getCapabilities()`, and `test-entry-summary` agree about the supported public surface

Static build success is not enough by itself. Validate against the built preview path before presenting the integration as complete. If runtime validation was not performed, say so explicitly, state the blocker, and do not present the extension as fully runtime-verified.

If the protocol only supports partial bridge behavior or partial screenshot readiness, document that limitation in the summary.

## Downstream Handoff

The final output of this skill must include or update a persistent `test-entry-summary`.

The final output should also summarize:

- the work mode used for this run (`initial integration` or `incremental extension`)
- whether build-preview runtime validation was performed
- whether at least one screenshot-capable screen was runtime-verified
- any remaining limitation that still affects downstream screenshot capture

Downstream skills should be told to:

- read the `test-entry-summary` first
- use the recorded build and preview commands
- prefer the URL protocol for lightweight entry
- prefer the public bridge for complex state
- use each screen's ready contract instead of guessing timing
- avoid reading project internals if the bridge already exposes the needed capability

If the summary is missing or stale, the integration is incomplete.

## Final Handoff Template

Final reports must be concise, direct, and in Chinese. Use exactly these 5 lines:

- `本次模式`：首次接入 / 增量补充
- `处理结果`：本次新增、修改或确认了什么
- `启动判断`：适合继续用于 test 系列截图 / 暂不适合继续用于 test 系列截图
- `验证情况`：是否做了 build + preview 运行验证；如果没有，只写“仅做静态检查”，并补一句阻塞原因
- `后续建议`：一句话告诉下游先看 `test-entry-summary.json`

Expression rules:

- State the conclusion first. Do not narrate the whole process.
- Focus on target screens and screenshot stability, not tool internals.
- If there is risk, say it directly, for example `页面可能加载过慢` or `截图可能拿到白屏或半加载画面`.
- Judge suitability by whether the target screen can reach a stable screenshot-ready state in a reasonable time, not by whether a generic server starts.
