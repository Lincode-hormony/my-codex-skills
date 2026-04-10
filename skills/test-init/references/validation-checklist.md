# Validation Checklist

Use this checklist before declaring the integration ready for downstream skills.

The expected flow is:

1. classify
2. integrate
3. validate
4. hand off

Do not produce the final `test entry summary` before validation is complete.

## Discovery checks

- The project was correctly identified as a SPA-style web game demo or a close equivalent.
- Existing debug or preview entry points were inventoried before new ones were added.
- The chosen integration pattern matches the project's architecture.

## Protocol checks

- `testEntry=1` activates protocol-aware behavior.
- `window.__TEST_ENTRY__` exists in dev or test mode.
- `window.__TEST_ENTRY__.getCapabilities()` returns a plain structured object.
- At least one target screen can be opened with `open()`.
- At least one auth mode works through `login()` or URL parameters.
- `reset()` can clear or neutralize test-only state.
- `snapshot()` returns meaningful state for downstream verification.

## Safety checks

- The protocol is disabled or inert in production.
- No real credentials or sensitive tokens were committed.
- The integration does not require brittle click-through flows.
- Existing user-facing behavior remains unchanged outside test mode.

## Auth-chain checks

If the project has authenticated routes or authenticated API access, verify all applicable layers:

- route guards do not immediately redirect away from an active test entry
- startup auth restore does not silently clear the injected test state
- page-level API behavior is documented when a real backend token is still required

If the protocol only bypasses the client-side route guard, that limitation must appear in the final `test entry summary`.

## Downstream compatibility checks

- A login-bypass skill can use the exposed auth mode without reading project internals.
- A screenshot skill can enter a target screen without manual UI traversal.
- Downstream skills can rely on stable public screen names and capability metadata.

## Minimum pass bar

The integration is minimally usable only if all of the following are true:

- one or more screen names are supported
- one or more auth modes are supported
- `getCapabilities()` works
- `open()` works
- `reset()` works

If `snapshot()` is missing, document that limitation explicitly because it weakens downstream validation.
