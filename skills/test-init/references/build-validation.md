# Build Validation

## Contents

- Required validation
- Minimum runtime checks
- Incremental extension checks
- Reporting rule

## Required validation

A successful static build is necessary but not sufficient.

Validate the contract against the built preview path whenever possible.

## Minimum runtime checks

Confirm all of the following on the test build path:

- the preview service responds
- `testEntry=1` is recognized
- the public bridge exists
- `getCapabilities()` matches the summary
- at least one supported screen can be entered through the public contract
- at least one ready strategy succeeds for a screenshot-capable screen

When a preview URL exists, run the validator with `--base-url` as the default path so the runtime check covers one real screenshot-capable screen instead of stopping at HTTP reachability.

Add `--ready-screen` only when you need to override the validator's automatic screen choice.

## Incremental extension checks

After adding a new screen or ready strategy:

- revalidate the new screen first
- revalidate one stable existing anchor screen
- confirm the summary still matches runtime behavior
- do not widen validation scope unless the narrow validator loop reveals a compatibility break

## Reporting rule

If build-preview runtime validation was skipped or partially blocked, say so directly in the final handoff.

Do not describe the integration as complete when only static checks were performed.
