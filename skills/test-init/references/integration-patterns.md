# Integration Patterns

Use the least invasive pattern that produces a stable contract.

## Pattern 1: Query-first

Use when the project already has query-string driven debug entry.

Approach:

- Keep the existing query parser if it is already stable.
- Add a compatibility layer that recognizes the canonical `testEntry` parameters.
- Map the canonical parameters onto the existing local debug behavior.
- Expose the standardized bridge on top of the existing logic.

Best when:

- The project already uses `?debugScreen=...` or similar.

## Pattern 2: Hash-first

Use when the project already relies on `#qa-*` or similar hashes.

Approach:

- Preserve existing hash behavior for compatibility.
- Introduce canonical URL parameters as the preferred public interface.
- Resolve hash-based presets inside the bridge rather than forcing downstream skills to know about old hashes.

Best when:

- The project has several ad hoc preview screens behind location hashes.

## Pattern 3: State-machine first

Use when a single client-side state machine drives screens or scenes.

Approach:

- Attach `open(screen)` close to the screen or scene switch logic.
- Attach `bootstrap(config)` close to the state restoration or initial state creation logic.
- Keep public screen names stable even if internal state names differ.

Best when:

- The project uses `view`, `scene`, `mode`, or equivalent state to render major screens.

## Pattern 4: Auth-gated

Use when most of the app is blocked behind login or session restoration.

Approach:

- Hook `testAuth` into the earliest safe auth gate.
- Keep the bypass dev/test-only.
- Prefer injecting a test user or restoring a test session over mutating random UI flags.

Best when:

- A login wall blocks all meaningful screens.

### Auth-chain note

Many SPA applications have more than one auth enforcement point. Do not stop at the route guard. Check for:

- route redirects
- startup auth restore such as `fetchUser`, token hydration, or session bootstrap
- page-level API calls that still require a real token after the page opens

If multiple layers exist, apply the protocol at the earliest safe point and document which layers are bypassed versus which still require a real backend session.

## Pattern 5: Storage-driven

Use when the app restores most state from browser storage.

Approach:

- Let `bootstrap()` write the minimum required storage shape.
- Reuse the normal restore path where possible.
- Use `reset()` to clear or neutralize the test-only storage footprint.

Best when:

- The app already treats browser storage as its canonical local restore layer.

## Selection rules

- Prefer compatibility over replacement.
- Prefer a thin adapter over a broad refactor.
- Prefer named presets over large opaque payloads.
- Prefer protocol normalization over accumulating one-off debug flags.

Combine patterns when needed, but keep one primary public entry surface.
