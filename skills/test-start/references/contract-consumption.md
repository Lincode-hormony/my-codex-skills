# Contract Consumption

Read this file before composing a launch URL.

## Rules

- Treat `test-entry-summary` as the only public contract.
- Require `protocol_version=2` and `launch_mode=build-preview`.
- Use `commands.build_test_entry` and `commands.preview_test_entry` as the only allowed launch commands.
- Use `supported_screens`, `supported_auth_modes`, and `supported_presets` as hard allow-lists.
- Prefer URL-based entry for lightweight launch paths.
- Use `entry_url_examples` as contract examples, not as permission to invent neighboring URLs.

## URL composition

- `normal launch` returns one contract-approved URL when no `screen`, `preset`, or `auth` was requested.
- `launch specific screen` returns a URL with `testEntry=1` and one supported `testScreen`.
- `auth-only launch` also returns a `testEntry=1` URL so the requested auth mode is actually applied.
- If a specific screen or preset is being launched and no auth mode was specified, prefer `testAuth=bypass` when the contract supports it.
- Add `testAuth` only when needed and only if the auth mode is supported.
- Add `testPreset` only when the preset is supported.

## Failure rule

If a requested screen is missing from `supported_screens`, stop composing the URL and hand the task back to `test-init` after user confirmation.

## Return rule

- Always return the exact URL produced by `finalize_launch.py`.
- Do not replace a contract-backed example URL with the raw base URL unless the summary does not provide a better entry.
- Do not add ad hoc query parameters outside the public contract.
