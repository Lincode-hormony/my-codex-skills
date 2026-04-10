---
name: test-init
description: "Integrates a reusable test-entry protocol into SPA-style web game demo projects so other skills can bypass login, inject test state, and open target screens reliably."
---

# Test Init

Use this skill when a project is a SPA-style web game demo and needs a stable test-entry protocol that other skills can reuse.

Do not use this skill for Unity, Unreal, Godot, Electron-native, or server-rendered applications that do not expose meaningful client-side state control.

## What this skill produces

- A minimal URL-based test-entry protocol
- A `window.__TEST_ENTRY__` bridge for complex state injection
- A short capability contract that downstream skills can call
- A validation result showing whether the integration is usable
- A `test entry summary` that downstream skills must treat as the public integration contract

This skill does not add screenshot automation, full Playwright suites, visual baselines, or long-running dev-server management. Those belong in downstream skills.

## Workflow

1. Run the utility script from the project root:
   ```bash
   python scripts/inspect_project.py
   ```
   The script returns structured JSON. Use it as the first-pass classifier instead of manually guessing project fit.
2. Read [references/project-detection.md](references/project-detection.md) after the script run whenever:
   - the project type is not an obvious fit
   - the script reports mixed signals
   - you are about to integrate the project rather than just classify it
3. Read [references/protocol.md](references/protocol.md) to apply the standard contract.
4. Read [references/integration-patterns.md](references/integration-patterns.md) to choose the least invasive integration pattern.
5. Inspect project code in this order before broad searches:
   - app root or main entry
   - auth gate or session restore path
   - screen, scene, mode, or view switch logic
   - state restore or local storage bootstrap
   - existing query or hash debug entry points
6. Read [references/anti-patterns.md](references/anti-patterns.md) once before editing any files.
7. If the project has protected routes, login gating, or session restoration, read [references/auth-chain-checks.md](references/auth-chain-checks.md) before editing auth-related code.
8. Add or normalize:
   - URL parsing for `testEntry` parameters
   - A dev/test-only `window.__TEST_ENTRY__` bridge
   - At least one auth mode and one target screen
9. Validate the integration with [references/validation-checklist.md](references/validation-checklist.md).
10. Read [references/downstream-contract.md](references/downstream-contract.md) only after validation passes or when preparing the final handoff.
11. Produce a `test entry summary` using [assets/test-entry-summary-template.json](assets/test-entry-summary-template.json) and tell the user to treat it as the public contract for downstream skills.

## Utility script

This skill includes one utility script:

- `scripts/inspect_project.py`
  Run it with `python scripts/inspect_project.py`.
  It returns structured JSON with:
  - `project_type`
  - `confidence`
  - `framework_signals`
  - `entry_files`
  - `existing_test_entry_signals`
  - `recommended_pattern`
  - `risks`

If Python is unavailable, inspect manually using [references/project-detection.md](references/project-detection.md), but prefer the script when possible because it is more reliable and token-efficient.

## Reading guide

- Use [references/protocol.md](references/protocol.md) for the canonical interface.
- Use [references/project-detection.md](references/project-detection.md) after the inspection script to confirm fit, interpret mixed signals, and avoid forcing this skill into the wrong project type.
- Use [references/integration-patterns.md](references/integration-patterns.md) when choosing where to attach the protocol.
- Use [references/anti-patterns.md](references/anti-patterns.md) before editing so shortcuts and brittle entry mechanisms do not leak into the implementation.
- Use [references/auth-chain-checks.md](references/auth-chain-checks.md) when the app has more than one auth-related enforcement point.
- Use [references/validation-checklist.md](references/validation-checklist.md) before concluding the project is ready for downstream skills.
- Use [references/downstream-contract.md](references/downstream-contract.md) only when validation has passed and you are producing the final handoff for downstream skills.

## Project exploration order

When scanning the project, prefer this order over broad repo-wide searches:

1. app root
2. auth gate
3. screen or view switch
4. state restore
5. existing debug query or hash entry

Use broad text searches only after the likely attachment points are checked.

## Auth chain rule

If the project has any protected or authenticated area, do not assume there is a single auth gate.

Before editing auth-related entry logic, confirm whether the project enforces access through:

1. route guards or redirects
2. startup session restore or `fetchUser`-style initialization
3. page-level API calls that still require a real backend token

If more than one layer exists, treat it as an auth chain and validate the test-entry flow across the whole chain, not just the route layer.

## Validation gate

Do not consider the integration complete unless all of the following are true:

- The project can recognize `testEntry=1`
- `window.__TEST_ENTRY__` exists in dev or test mode
- `getCapabilities()` returns structured data
- `open()` can enter at least one target screen without manual UI traversal
- `reset()` can clear or neutralize the injected test state

If the project cannot safely support the full bridge, fall back to a documented partial integration and clearly state which downstream operations remain unsupported.

## Default decisions

Use these defaults unless the project strongly contradicts them:

- Prefer the script's `recommended_pattern`
- Prefer compatibility over replacement
- Prefer one or two stable screens over broad but fragile support
- Prefer `bypass` only in dev/test when no safer local auth mode exists
- Prefer a thin adapter layer over a refactor

## Downstream handoff

The final output of this skill must include a `test entry summary`.

Downstream skills should be told to:

- read the `test entry summary` first
- prefer the URL protocol for lightweight entry
- prefer `window.__TEST_ENTRY__` for complex state
- avoid reading project internals if the bridge already exposes the needed capability

If the summary is missing, the integration is incomplete.
