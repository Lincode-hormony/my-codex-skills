# Validation Checklist

Use this checklist before declaring the integration ready for downstream skills.

The expected flow is:

1. classify
2. integrate
3. validate
4. hand off

Do not produce the final `test-entry-summary` before validation is complete.

## Discovery checks

- The project was correctly identified as a client-rendered web app or a close equivalent.
- Existing debug or preview entry points were inventoried before new ones were added.
- The chosen integration pattern matches the project's architecture.
- The inspection result for build-preview capability and reusable entry signals was captured before implementation decisions were finalized.
- For incremental work, the read scope stayed bounded to the bridge, screen registry, target screen logic, and summary unless that bounded read failed.

## Protocol checks

- `testEntry=1` activates protocol-aware behavior in the test build path.
- `window.__TEST_ENTRY__` or the chosen public bridge exists in the previewed test runtime.
- `getCapabilities()` returns a plain structured object.
- At least one target screen can be opened with `open()`.
- `reset()` can clear or neutralize test-only state where supported.
- `snapshot()` returns meaningful state for downstream verification when the project claims it.
- The summary records explicit build and preview commands.
- At least one screenshot-capable screen has a declared ready strategy.

## Safety checks

- The protocol is disabled or inert outside the intended test build path.
- No real credentials or sensitive tokens were committed.
- The integration does not require brittle click-through flows.
- Existing user-facing behavior remains unchanged outside test mode.

## Auth-chain checks

If the project has authenticated routes or authenticated API access, verify all applicable layers:

- route guards do not immediately redirect away from an active test entry
- startup auth restore does not silently clear the injected test state
- page-level API behavior is documented when a real backend token is still required

If the protocol only bypasses the client-side route guard, that limitation must appear in the final summary.

## Downstream compatibility checks

- A launch skill can use the recorded build and preview commands without reading project internals.
- A screenshot skill can enter a target screen without manual UI traversal.
- A screenshot skill can use the ready contract instead of fixed sleeps.
- Downstream skills can rely on stable public screen names and capability metadata.
- The final handoff says whether build-preview runtime validation confirmed screenshot suitability or only static checks completed.
- For incremental work, the validator covered the new screen and one anchor screen instead of re-running a broad sweep.

## Minimum pass bar

The integration is minimally usable only if all of the following are true:

- one or more screen names are supported
- the summary records explicit build and preview commands
- `getCapabilities()` works
- `open()` works
- `reset()` works where the project claims reset support
- at least one screen is marked screenshot-capable with a real ready strategy

If `snapshot()` is missing, document that limitation explicitly because it weakens downstream validation.

## Default validator path

When a preview URL exists, treat `python <skill-dir>/scripts/validate_build_contract.py --base-url <preview-url>` as the default path instead of an optional extra check.

- Let the validator choose the first screenshot-capable screen automatically unless you need to override it.
- Do not replace validator output with ad hoc DOM dumps if the validator can still run.
- If runtime validation is blocked, record the blocker explicitly and fall back to static validation only after saying why.
