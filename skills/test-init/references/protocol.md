# Test-Entry Protocol

This file defines the canonical contract for projects integrated by `integrating-web-game-test-entry`.

## Scope

The protocol is for SPA-style web game demo projects that need deterministic local entry into application states such as login-bypassed screens, isolated UI states, or complex in-run scenes.

The protocol has two layers:

1. URL parameters for discovery and lightweight mode selection
2. `window.__TEST_ENTRY__` for complex state injection and downstream tool access

## URL protocol

Use these parameter names unless there is a compatibility constraint:

- `testEntry=1`
- `testScreen=<screen>`
- `testAuth=<none|bypass|mock-user|session>`
- `testLocale=<locale>`
- `testPreset=<preset-name>`
- `testPayload=<payload-key-or-encoded-json>`

### Rules

- `testEntry=1` is the explicit switch that enables the protocol.
- `testScreen` selects a named target screen or scene.
- `testAuth` selects a dev/test-only auth behavior.
- `testLocale` is optional and should stay lightweight.
- `testPreset` should be preferred over large inline payloads.
- `testPayload` is for lightweight references or small overrides, not for arbitrarily large state dumps.

### Example URLs

```text
/?testEntry=1&testScreen=shop&testAuth=mock-user
/?testEntry=1&testScreen=reward&testPreset=act1-victory
/?testEntry=1&testScreen=combat&testAuth=bypass&testLocale=zh
```

## Global bridge

Expose this object in dev or test environments only:

```js
window.__TEST_ENTRY__ = {
  version: "1",
  supported: true,
  getCapabilities(),
  bootstrap(config),
  open(screen, options),
  login(mode, options),
  reset(),
  snapshot(),
};
```

### Method requirements

- `getCapabilities()`
  Returns a structured capability object.
- `bootstrap(config)`
  Applies complex test data such as user state, scene state, inventory, rewards, or map state.
- `open(screen, options)`
  Enters a supported target screen directly.
- `login(mode, options)`
  Applies a supported auth mode without relying on manual UI login.
- `reset()`
  Clears or neutralizes test-only state.
- `snapshot()`
  Returns a stable summary of the current meaningful state for downstream verification.

## Capability schema

Return a plain object with these fields:

```js
{
  version: "1",
  screens: ["menu", "map", "combat", "shop", "reward", "event"],
  authModes: ["none", "bypass", "mock-user", "session"],
  presets: ["shop-default", "reward-default"],
  features: ["bootstrap", "open", "reset", "snapshot"]
}
```

### Rules

- `screens` lists stable public names, not internal component names.
- `authModes` only lists modes that actually work in the current project.
- `presets` should only contain named states that are intentionally maintained.
- `features` should reflect real support, not aspirational support.

## Auth modes

Recommended meanings:

- `none`
  Do not alter auth behavior.
- `bypass`
  Skip local auth gating in dev or test only.
- `mock-user`
  Inject a local test user and any minimum related state.
- `session`
  Restore a prepared local session or persisted auth state.

### Safety requirements

- Never enable these modes in production builds.
- Never embed real credentials or sensitive tokens in source-controlled defaults.
- Prefer `mock-user` or `session` over broad bypasses when feasible.

## Preset and payload model

Recommended precedence:

`payload overrides preset overrides project defaults`

Use named presets for common, stable states:

- `shop-default`
- `reward-default`
- `combat-basic`

Use payloads for local overrides such as:

- selected hero
- currency counts
- reward contents
- localized text mode
- event identity

## Downstream contract

Downstream skills should prefer the protocol in this order:

1. URL protocol for lightweight entry
2. `window.__TEST_ENTRY__.getCapabilities()`
3. `window.__TEST_ENTRY__.login()` and `open()`
4. `window.__TEST_ENTRY__.bootstrap()` for complex state
5. `window.__TEST_ENTRY__.snapshot()` for verification

Downstream skills should not depend on internal React state, random debug globals, or page-specific DOM wiring if the bridge exists.

For the required handoff artifact and downstream calling conventions, see [downstream-contract.md](downstream-contract.md).
