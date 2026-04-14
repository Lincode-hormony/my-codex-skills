# Build-First Protocol

## Contents

- Required public contract
- Launch model
- Bridge model
- Screen model
- Ready model
- Output contract

## Required public contract

`test-init` must produce one persistent `test-entry-summary` that downstream skills can consume without re-reading implementation code.

The contract must describe:

- how to build the test artifact
- how to preview the test artifact
- how to enter supported screens
- how to detect screenshot readiness
- what limitations remain

## Launch model

Record one explicit test build command and one explicit preview command.

Examples:

- `npm run build:test-entry`
- `npm run preview:test-entry`
- `pnpm build:test-entry`
- `vite build --mode test-entry`

The summary may store equivalent commands when a project uses another package manager or wrapper, but it must always expose one build path and one preview path.

## Bridge model

Prefer `window.__TEST_ENTRY__` unless the project already has a stable public bridge name.

The bridge should expose stable methods where supported:

- `getCapabilities()`
- `open()`
- `reset()`
- `snapshot()` or equivalent screenshot helper

Do not expose internal-only helpers in the public contract.

## Screen model

Each supported screen must have:

- one stable public name
- one supported entry path
- any required auth or preset metadata
- one ready strategy if screenshots are supported

Do not use user-facing copy or temporary labels as the public screen name.

## Ready model

Do not treat `200 OK` or route arrival as screenshot readiness.

A screen is screenshot-capable only when the contract defines how readiness is determined.

Valid ready strategies include:

- bridge method
- stable selector plus state check
- explicit app-level ready flag

## Output contract

The resulting `test-entry-summary` should make downstream behavior obvious:

- `test-start` should know how to launch without guessing
- `test-screenshot` should know when to capture without timing heuristics

If the project cannot yet support this model, do not mark the integration complete.
