---
name: test-init
description: "Builds or incrementally extends a reusable test-entry protocol for SPA-style web game demos so downstream skills can bypass login, inject test state, and open stable target screens reliably. Use when a project needs initial test-entry integration, when an existing `test-entry-summary` is missing or invalid, or when a requested screen must be added permanently to the shared test base."
---

# Test Init

Use this skill to create or extend the project's persistent test-entry base. This skill is the only producer of the public `test-entry-summary` contract.

Do not use this skill for Unity, Unreal, Godot, Electron-native, or server-rendered apps that do not expose meaningful client-side state control.

## What this skill produces

- A minimal URL-based test-entry protocol
- A dev/test-only `window.__TEST_ENTRY__` bridge
- Stable public screen names and capability metadata
- Validation results for downstream reuse
- A persistent `test-entry-summary` contract

This skill does not manage long-running dev servers. Downstream launch skills should consume the summary instead of re-reading project internals.

## First Decision

Before reading project internals or editing code:

1. run `python <this-skill>/scripts/check_summary.py`
2. choose exactly one mode:
   - `initial integration` when no valid summary exists
   - `incremental extension` when a valid summary exists and the requested public screen or capability is missing

Do not describe the task as incremental extension until the summary check confirms that a valid summary already exists.

## Modes

- `initial integration`
  Use when the project has no valid `test-entry-summary` yet.
- `incremental extension`
  Use when the project already has a valid summary, but a requested screen or capability is missing and must be added permanently.

This skill is the only valid next step when a downstream launch or screenshot skill reports `next_action=offer-supported-or-test-init` and the user chooses permanent extension.

## Workflow

1. Run the summary checker from this skill directory:
   ```bash
   # keep the current working directory at the project root
   python <skill-dir>/scripts/check_summary.py
   ```
2. If the user request is ambiguous, normalize it into one stable public screen name before editing. Do not guess between multiple plausible public names.
3. Run the project inspection script from this skill directory:
   ```bash
   # keep the current working directory at the project root
   python <skill-dir>/scripts/inspect_project.py
   ```
4. Read [references/project-detection.md](references/project-detection.md) if the script reports mixed signals or you are about to edit the project.
5. Read [references/protocol.md](references/protocol.md) for the canonical public contract.
6. Read [references/integration-patterns.md](references/integration-patterns.md) to choose the least invasive attachment point.
7. Inspect project code in this order before broad repo searches:
   - app root or main entry
   - auth gate or session restore path
   - screen, scene, mode, or view switch logic
   - state restore or local storage bootstrap
   - existing debug query or hash entry
8. Read [references/anti-patterns.md](references/anti-patterns.md) once before editing.
9. If the project has protected routes, login gating, or session restoration, read [references/auth-chain-checks.md](references/auth-chain-checks.md) before editing auth-related code.
10. If a valid summary already exists, read [references/incremental-extension.md](references/incremental-extension.md) before changing supported screens or capabilities.
11. Add or extend only the public protocol surface that downstream skills need:
   - URL parsing for `testEntry` parameters
   - A dev/test-only `window.__TEST_ENTRY__` bridge
   - Stable `open()`, `login()`, `reset()`, and `snapshot()` behavior where supported
   - One or more stable target screens
12. Validate the integration with [references/validation-checklist.md](references/validation-checklist.md).
13. Update the public contract using [references/contract-update-rules.md](references/contract-update-rules.md).
14. Read [references/downstream-contract.md](references/downstream-contract.md) only after validation passes or when preparing the final handoff.

## Utility scripts

- `scripts/check_summary.py`
  Run it from the target project root with `python <skill-dir>/scripts/check_summary.py`.
  It checks common summary locations in the current project and returns structured JSON with:
  - `exists`
  - `path`
  - `valid`
  - `missing_required_fields`
  - `supported_screens`

Use this script before choosing between `initial integration` and `incremental extension`.

- `scripts/inspect_project.py`
  Run it from the target project root with `python <skill-dir>/scripts/inspect_project.py`.
  It returns structured JSON with:
  - `project_type`
  - `confidence`
  - `framework_signals`
  - `entry_files`
  - `existing_test_entry_signals`
  - `recommended_pattern`
  - `risks`

If Python is unavailable, inspect manually using [references/project-detection.md](references/project-detection.md), but prefer the script when possible.

## Decision rules

- Treat `test-entry-summary` as the only public contract for downstream skills.
- If the summary is missing or invalid, do `initial integration`.
- If the summary exists and the requested screen is missing, do `incremental extension` instead of inventing ad hoc URLs.
- Resolve bundled scripts and references from this skill's own directory first.
- Resolve bundled script paths from this skill's own directory, but keep the command working directory at the target project root so the scripts inspect the repository instead of the skill folder.
- Ignore similarly named `test-init` folders inside the user repository unless the user explicitly asks to use that copy.
- If a bundled script or reference path fails, re-check the skill-local path first. Do not broad-search the repository before confirming the skill-local resource is truly unavailable.
- Extend the existing protocol. Do not create a second test-entry mechanism.
- Persist all supported screens and capability changes in the repository. Do not rely on session-only patches.
- Prefer one or two stable additions over broad but fragile coverage.

## Incremental extension rule

When extending an existing test base:

- Read the current `test-entry-summary` first.
- Confirm the requested screen is truly unsupported, not just named differently.
- If the user named a user-facing page rather than a stable public screen, propose or confirm exactly one public screen name before editing whenever more than one mapping is plausible.
- Preserve existing public screen names, auth modes, and bridge shape unless a compatibility break is unavoidable.
- Add the new screen to the implementation and the summary in the same change.
- Update `supported_screens`, `entry_url_examples`, and any affected preset or feature fields in the same change.
- Revalidate both old screens and the new screen before finishing.

## Validation gate

Do not consider the project ready unless all of the following are true:

- The project recognizes `testEntry=1`
- `window.__TEST_ENTRY__` exists in dev or test mode
- `getCapabilities()` returns structured data
- `open()` can enter at least one stable target screen without manual UI traversal
- `reset()` can clear or neutralize test-only state
- The final `test-entry-summary` matches the real supported surface
- The implementation, `getCapabilities()`, and `test-entry-summary` agree about the supported public surface

`npm run build` or equivalent static validation is not enough by itself after an incremental extension. If runtime validation was not performed, say so explicitly and do not present the extension as fully runtime-verified.

If the protocol only bypasses client-side routing or only supports partial bridge behavior, document that limitation in the summary.

## Downstream handoff

The final output of this skill must include or update a persistent `test-entry-summary`.

Downstream skills should be told to:

- read the `test-entry-summary` first
- prefer the URL protocol for lightweight entry
- prefer `window.__TEST_ENTRY__` for complex state
- avoid reading project internals if the bridge already exposes the needed capability

If the summary is missing or stale, the integration is incomplete.
