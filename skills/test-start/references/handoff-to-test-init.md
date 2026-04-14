# Handoff To Test Init

Read this file when the user asks for a page that is not covered by the current public contract.

## Trigger

Use this handoff when:

- the requested screen is missing from `supported_screens`
- the requested auth mode is unsupported
- the requested preset is unsupported
- the summary is missing or invalid

## Handoff rule

This skill must not patch the test-entry base directly.

Instead:

1. stop immediately when the request is outside the current contract
2. list the currently supported screens
3. ask the user to choose exactly one next action:
   - use one existing supported screen
   - extend the test base permanently with `test-init`
4. if they choose `test-init`, hand off immediately
5. resume the launch flow only after `test-init` has updated the project summary
