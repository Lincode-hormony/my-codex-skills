# Contract Consumption

Read this file before composing a launch URL.

## Rules

- Treat `test-entry-summary` as the only public contract.
- Use `supported_screens`, `supported_auth_modes`, and `supported_presets` as hard allow-lists.
- Prefer URL-based entry for lightweight launch paths.
- Use `entry_url_examples` as examples, not as the only legal format.
- Do not invent screen names or auth modes that are not in the summary.

## URL composition

- `normal launch` returns the finalizer's contract-approved URL when no `screen`, no `preset`, and no `auth` were requested. This may be a contract-preferred direct entry URL, the raw base URL, or a base URL plus contract-defined preflight query parameters.
- `launch specific screen` returns a URL with `testEntry=1` and one supported `testScreen`.
- `auth-only launch` also returns a `testEntry=1` URL so the requested auth mode is actually applied.
- If a specific screen or preset is being launched and no auth mode was specified, prefer `testAuth=bypass` when the contract supports it.
- Add `testAuth` only when needed and only if the auth mode is supported.
- Add `testPreset` only when the preset is supported.

## Failure rule

If a requested screen is missing from `supported_screens`, stop composing the URL and hand the task back to `test-init` after user confirmation.

## Return rule

- Always return the exact URL produced by `finalize_launch.py`.
- Do not strip preflight query parameters from a normal-launch URL.
- Do not replace a contract-preferred direct launch URL with the raw base URL.
