# Auth Chain Checks

Use this file when a project has protected routes, login gating, token restore, or authenticated page APIs.

## Why this matters

In many SPA applications, auth is enforced in more than one place. A test entry can appear to work at the URL or route level, then fail later when startup auth restore clears the injected state or when the page immediately calls APIs that still expect a real backend token.

Do not treat auth as a single switch unless the code actually behaves that way.

## Check these layers

### 1. Route layer

Look for:

- protected route wrappers
- redirects to `/login`
- route guards based on `user`, `token`, or `initialized`

Question:

- Will test-entry auth still be considered valid by the route layer after the app mounts?

### 2. Startup auth layer

Look for:

- `fetchUser()`
- token hydration
- session restore
- auth store initialization
- `useEffect` blocks that clear auth on missing tokens

Questions:

- Does startup auth overwrite the injected test state?
- Does the app clear the mock or bypass state after mount?
- Does the app assume a real token even when the route layer is bypassed?

### 3. Page API layer

Look for:

- immediate page data fetches
- shared API clients that require a token
- protected loader hooks
- server-side permission checks surfaced through frontend APIs

Questions:

- Can the page open but still fail because API data needs a real backend session?
- Should the summary explicitly say that the page is reachable but not fully functional under mock auth?

## Implementation guidance

- Apply the protocol at the earliest safe auth point.
- Prefer preserving compatibility with the app's existing auth model.
- If only the client-side gate can be bypassed, document that clearly instead of pretending the page is fully testable.
- If the app has multiple auth layers, validate each one before concluding that login bypass works.

## Handoff requirement

If any auth-layer limitation remains, include it in the final `test entry summary` under `limitations`.
