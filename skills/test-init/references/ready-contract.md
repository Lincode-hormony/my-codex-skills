# Ready Contract

## Contents

- Why this matters
- Allowed ready strategies
- Minimum data per screen
- What not to do

## Why this matters

`test-screenshot` should not guess when a page is stable enough to capture.

`test-init` must define screenshot readiness at integration time for each screenshot-capable screen.

## Allowed ready strategies

Use one of these strategies:

1. bridge method
   Example: `window.__TEST_ENTRY__.isReady('pantheon-shop')`

2. stable selector plus state
   Example: root selector exists and loading overlay is absent

3. explicit app-level flag
   Example: `window.__APP_READY_FLAGS__.pantheonShop === true`

Use the narrowest stable signal the app can provide.

## Minimum data per screen

For each screenshot-capable screen, record:

- `ready_strategy.kind`
- the selector, flag, or method used
- any timeout guidance if the screen needs more than the normal ready window
- whether screenshot capture is officially supported

If a screen has no trustworthy ready signal, do not mark it screenshot-capable.

## What not to do

Do not define readiness as:

- raw page load event
- arbitrary fixed sleep
- generic network idle alone
- route change alone

These are not reliable enough for a public screenshot contract.
