# Contract Update Rules

Use this file after implementation changes and before final handoff.

The `test-entry-summary` is the single public contract for downstream skills. Update it whenever the real supported surface changes.

## Always keep these fields in sync

- `entry_url_examples`
- `supported_screens`
- `supported_auth_modes`
- `supported_presets`
- `supported_features`
- `recommended_entry_flow`
- `limitations`

## Update rules

- If you add a stable screen, add it to `supported_screens`.
- If the screen is reachable through URL entry, add or refresh an example in `entry_url_examples`.
- If you add or remove a callable bridge method, update `supported_features`.
- If auth support changes, update `supported_auth_modes`.
- If presets change, update `supported_presets`.
- If a behavior only partially works, put that limitation in `limitations` instead of overstating support.

## Stability rules

- Keep public screen names stable.
- Keep auth mode names stable.
- Keep `bridge_name` stable unless there is a strong reason to break compatibility.
- Prefer additive changes over renames.

## Final check

Before handing off, compare the summary against the actual implementation:

1. `getCapabilities()` output
2. supported URL entry points
3. real `open()` behavior
4. real auth limitations

If the summary and implementation disagree, fix the summary before concluding.
