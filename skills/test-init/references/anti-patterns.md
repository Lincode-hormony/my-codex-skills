# Anti-Patterns

Avoid these patterns when integrating the protocol.

Read this file before editing implementation code. It is not optional once you move from diagnosis into integration.

- Do not replace a stable existing debug entry with a brand-new incompatible one unless compatibility is impossible.
- Do not use recorded click flows as the primary entry mechanism.
- Do not expose login bypass behavior in production.
- Do not push large, deeply nested business state directly through URL parameters.
- Do not force downstream skills to read app internals if the bridge can expose the state cleanly.
- Do not turn this skill into a screenshot runner, visual-regression suite, or dev-server manager.
- Do not do broad architecture refactors just to add the protocol.
- Do not advertise unsupported screens, presets, or auth modes in `getCapabilities()`.
- Do not leave partial integrations undocumented. State clearly what works and what does not.
