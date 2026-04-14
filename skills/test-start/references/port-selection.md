# Port Selection

Read this file before overriding the planner's suggested port.

## Rules

- Use the current machine state, not assumptions, to choose a port.
- Prefer an actually free port over a popular default that is already occupied.
- Do not reuse an occupied port unless you have already verified it belongs to the current project.
- Do not probe other projects by trial-and-error browser navigation.

## Default behavior

- Let the planner choose from common local dev ranges.
- Prefer one stable localhost host value such as `127.0.0.1`.
- Keep the selected port explicit in the server command.

## Failure rule

If the planned port becomes occupied before launch, rerun the planner instead of improvising another command.
