# Project Detection

Use this file after running `scripts/inspect_project.py` and before integrating code when you need to confirm project fit, interpret mixed signals, or decide whether to stop.

## Positive signals

A project is likely a good fit when several of these are true:

- It has a `package.json` and a modern frontend toolchain such as Vite, React, Vue, or similar.
- It has a SPA entry such as `src/main.*`, `src/App.*`, or a similar client root.
- It behaves like an application, not a document site.
- It contains screen, scene, mode, or view switching that resembles a game flow.
- It uses local state, browser storage, query params, or hash state to control major UI states.
- It already has debug flags, dev entry points, or Playwright/Cypress scripts.

## Existing test-entry signals

Treat these as reusable signals before introducing new ones:

- query-string debug parameters
- hash-based preview or QA routes
- `data-testid` markers
- local storage or session storage debug bootstrapping
- mock-user or dev-only login bypass logic
- dev-only screen or scene presets
- Playwright or Cypress scripts that already open a specific page state

## Rejection criteria

This skill is usually the wrong fit when any of these are true:

- The project is a native game engine project such as Unity, Unreal, or Godot.
- The project is a packaged build artifact with no editable source.
- The project is mostly SSR with minimal client-controlled state.
- The team cannot allow dev or test-only entry logic in the client app.
- The only feasible path is click-recording against a brittle UI flow.

## Detection output

When inspecting a project, summarize:

- project type
- confidence
- framework signals
- state-entry signals
- existing test-entry signals
- recommended integration pattern
- major risks

If the fit is weak, say so early and stop before forcing the protocol into the wrong architecture.

## How to use this with the inspection script

Use the script result as the first-pass classifier, then use this file to interpret the result:

- If `project_type` is `spa_web_game_demo` and confidence is high, continue.
- If confidence is medium, inspect the app root and state-management path before editing.
- If the script reports mixed or weak signals, do not force the protocol in. Re-check whether the app really exposes client-side state control and reusable entry points.
