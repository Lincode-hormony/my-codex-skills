# Downstream Contract

Use this file only after validation passes and you are preparing the final handoff to downstream skills such as login-bypass, screenshot, state-debug, or verification skills.

## Required handoff artifact

Every successful integration must produce a `test entry summary`.

Treat this summary as the public contract for downstream skills. If the project later changes its internal implementation, the summary should remain stable unless the public contract also changes.

## Summary format

Produce the final summary in a structured format such as JSON or a clearly delimited Markdown block.

Start from [../assets/test-entry-summary-template.json](../assets/test-entry-summary-template.json) and fill in project-specific values.

Recommended shape:

```json
{
  "test_entry_supported": true,
  "project_type": "spa_web_game_demo",
  "protocol_version": "1",
  "entry_url_examples": [
    "/?testEntry=1&testScreen=shop&testAuth=mock-user",
    "/?testEntry=1&testScreen=reward&testPreset=reward-default"
  ],
  "bridge_available": true,
  "bridge_name": "window.__TEST_ENTRY__",
  "supported_screens": ["shop", "reward", "combat"],
  "supported_auth_modes": ["mock-user", "bypass"],
  "supported_presets": ["shop-default", "reward-default"],
  "supported_features": ["getCapabilities", "bootstrap", "open", "reset", "snapshot"],
  "recommended_entry_flow": [
    "use URL for lightweight entry",
    "call getCapabilities()",
    "call login() if needed",
    "call bootstrap() for complex state",
    "call open()",
    "call snapshot() for verification"
  ],
  "limitations": [
    "combat screen requires preset or bootstrap payload"
  ]
}
```

## Required fields

- `test_entry_supported`
- `project_type`
- `protocol_version`
- `entry_url_examples`
- `bridge_available`
- `bridge_name`
- `supported_screens`
- `supported_auth_modes`
- `supported_presets`
- `supported_features`
- `recommended_entry_flow`
- `limitations`

If a field is intentionally empty, include it with an empty list or a clear falsey value rather than omitting it.

## Downstream usage rules

Downstream skills should be instructed to use the summary in this order:

1. Check `test_entry_supported`
2. Use `entry_url_examples` for lightweight entry
3. Check `supported_features`
4. Use `bridge_name` and `getCapabilities()` if available
5. Use `login()` or URL auth parameters for auth handling
6. Use `bootstrap()` for complex state only when needed
7. Use `snapshot()` for verification before acting on the page

## Standard downstream prompt patterns

Use wording like this when handing off to other skills:

- "Read this project's `test entry summary` first and treat it as the public contract."
- "Prefer standard test-entry URL parameters over project-specific debug flags."
- "Use `window.__TEST_ENTRY__` for complex state injection instead of reading app internals."
- "Do not introduce new ad hoc debug parameters unless you also update the `test entry summary`."

## Contract stability rules

- Keep public screen names stable.
- Keep auth mode names stable.
- Keep `bridge_name` stable unless there is a strong reason to change it.
- If a capability is removed or renamed, update the summary and call out the compatibility impact.

The goal is to let downstream skills work from the summary alone for normal operations.
