# Downstream Contract

Use this file only after validation passes and you are preparing the final handoff to downstream skills.

## Required handoff artifact

Every successful integration must produce a `test-entry-summary.json`.

Treat this summary as the only public contract for downstream skills. If the implementation later changes, the summary should remain stable unless the public contract changes.

## Summary format

Start from [../assets/test-entry-summary-template.json](../assets/test-entry-summary-template.json) and fill in project-specific values.

Recommended shape:

```json
{
  "test_entry_supported": true,
  "project_type": "spa_web_app",
  "protocol_version": "2",
  "launch_mode": "build-preview",
  "commands": {
    "build_test_entry": "npm run build:test-entry",
    "preview_test_entry": "npm run preview:test-entry"
  },
  "entry_url_examples": [
    "/?testEntry=1&testScreen=shop&testAuth=bypass",
    "/?testEntry=1&testScreen=reward&testPreset=reward-default"
  ],
  "bridge_available": true,
  "bridge_name": "window.__TEST_ENTRY__",
  "supported_screens": [
    {
      "name": "shop",
      "entry": "url+bridge",
      "screenshot_ready": true,
      "ready_strategy": {
        "kind": "bridge-method",
        "method": "isReady"
      }
    }
  ],
  "supported_auth_modes": ["bypass"],
  "supported_presets": ["reward-default"],
  "supported_features": ["getCapabilities", "open", "reset", "snapshot"],
  "recommended_entry_flow": [
    "run the recorded test build command",
    "run the recorded preview command",
    "use URL entry for lightweight navigation",
    "call getCapabilities()",
    "call open()",
    "wait for the screen ready contract",
    "call snapshot() for verification when available"
  ],
  "test_series_readiness": {
    "level": "runtime-validated",
    "benchmark": [
      "runtime-validated: at least one screenshot-capable screen was verified in build-preview runtime",
      "static-only: only static contract validation has completed so far"
    ],
    "impact": [
      "Use runtime validation and each screen's ready contract as the source of truth for screenshot suitability."
    ]
  },
  "limitations": [
    "combat requires a preset and is not marked screenshot-ready yet"
  ],
  "validation": {
    "runtime_verified_in_build_preview": true
  }
}
```

## Required fields

- `test_entry_supported`
- `project_type`
- `protocol_version`
- `launch_mode`
- `commands`
- `entry_url_examples`
- `bridge_available`
- `bridge_name`
- `supported_screens`
- `supported_auth_modes`
- `supported_presets`
- `supported_features`
- `recommended_entry_flow`
- `test_series_readiness`
- `limitations`
- `validation`

If a field is intentionally empty, include it with an empty list or a clear falsey value rather than omitting it.

## Downstream usage rules

Downstream skills should use the summary in this order:

1. Check `test_entry_supported`
2. Check `protocol_version` and `launch_mode`
3. Run `commands.build_test_entry`
4. Run `commands.preview_test_entry`
5. Use `entry_url_examples` for lightweight entry
6. Check `supported_features`
7. Use `bridge_name` and `getCapabilities()` if available
8. Use each screen's `ready_strategy` instead of timing guesses
9. Read `test_series_readiness` to see whether screenshot suitability was runtime-verified or only statically checked

## Standard downstream prompt patterns

Use wording like this when handing off to other skills:

- "Read this project's `test-entry-summary.json` first and treat it as the public contract."
- "Use the recorded build and preview commands instead of guessing launch steps."
- "Use `window.__TEST_ENTRY__` for complex state injection instead of reading app internals."
- "Use each screen's ready contract instead of fixed sleeps."

## Contract stability rules

- Keep public screen names stable.
- Keep launch command semantics stable.
- Keep `bridge_name` stable unless there is a strong reason to change it.
- If a capability is removed or renamed, update the summary and call out the compatibility impact.

The goal is to let downstream skills work from the summary alone for normal operations.
