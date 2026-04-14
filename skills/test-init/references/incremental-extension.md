# Incremental Extension

Read this file only when the project already has a valid `test-entry-summary` and the task is to add or permanently widen support.

## Goal

Extend the existing test-entry base without breaking the public contract that downstream skills already use.

## When to use this path

- a requested screen is not listed in `supported_screens`
- a needed auth mode or feature is missing from the summary
- the existing bridge is valid, but coverage is too narrow for the new task

Do not use this path when the summary is missing, invalid, or clearly out of sync with the implementation. In those cases, fall back to initial integration or repair the base first.

## Extension workflow

1. Read the current `test-entry-summary`.
2. Confirm the requested screen or capability is truly missing.
3. Identify the existing attachment points for:
   - URL parsing
   - `getCapabilities()`
   - `open()`
   - auth handling
   - reset or snapshot logic
4. Add the smallest stable implementation that exposes the new screen through the existing protocol.
5. Keep old screen names and auth mode names stable unless there is a documented compatibility break.
6. Update the summary in the same change.
7. Revalidate both the previous public contract and the new addition.

## Rules

- Do not create a second bridge name.
- Do not introduce one-off debug flags instead of updating the public protocol.
- Do not advertise a screen in `supported_screens` unless `open()` or the documented URL flow can really reach it.
- Do not remove existing public fields from the summary unless the task explicitly requires a compatibility break.

## Minimum validation for an added screen

- the new screen can be entered through the public protocol
- the screen name appears in `supported_screens`
- at least one `entry_url_examples` item reflects the new support when URL entry is applicable
- existing supported screens still work
- any new limitation is written into `limitations`
