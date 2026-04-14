# Build-First Integration Patterns

## Contents

- Choose the least invasive pattern
- Pattern A: environment-gated bridge
- Pattern B: test build mode
- Pattern C: dedicated test bootstrap module
- Command patterns

## Choose the least invasive pattern

Prefer the smallest change that produces a stable test build and preview flow.

Selection order:

1. reuse an existing environment flag or test mode if it already fits the public contract
2. add a dedicated test-entry environment flag
3. add a dedicated test bootstrap module only if the existing entry path is too entangled

## Pattern A: environment-gated bridge

Use when the app already has a clean bootstrap path and only needs a controlled public bridge.

Typical shape:

- parse `testEntry` query parameters during app bootstrap
- enable the bridge only when the test build flag is enabled
- keep the bridge stable across screens

This is usually the simplest pattern.

## Pattern B: test build mode

Use when the project already supports mode-specific build configuration.

Typical shape:

- `vite build --mode test-entry`
- `.env.test-entry`
- test-only flags for bridge exposure and state injection

Prefer this when the framework already treats modes as first-class.

## Pattern C: dedicated test bootstrap module

Use when the main entry is hard to patch safely.

Typical shape:

- keep the normal app bootstrap intact
- add a small test bootstrap that mounts the app with the bridge and test parameter handling
- reuse shared route and store setup instead of forking app logic

Avoid duplicating the whole application entry path.

## Command patterns

Record commands that downstream skills can run without interpretation.

Good:

- `npm run build:test-entry`
- `npm run preview:test-entry`

Acceptable:

- `pnpm vite build --mode test-entry`
- `pnpm vite preview --mode test-entry --host 127.0.0.1 --port 4173`

Avoid summary entries that only describe intent, such as `build the app in test mode`.
