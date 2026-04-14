---
name: test-start
description: "Builds, previews, and verifies a local build-plus-preview test environment for projects that already expose a valid `test-entry-summary` contract. Use when the user wants one verified launch URL for a formally integrated test project, wants to open a supported screen directly, or needs unsupported requests routed back to `test-init`."
---

# Test Start

Use this skill to consume an existing `test-entry-summary` contract and return one verified local URL. This skill is a contract consumer only. It must not modify the test-entry base directly.

## First Decision

Before planning a launch:

1. run `python <skill-dir>/scripts/check_summary.py [--requested-screen <screen>] [--requested-auth <mode>] [--requested-preset <preset>]`
2. choose exactly one mode:
   - `normal launch`
   - `launch specific screen`

If no valid summary exists, stop and tell the user this project must be prepared with `test-init` first. If the checker returns `next_action` other than `proceed`, stop immediately.

## Scope

This skill does:

- validate the presence of a usable build-first `test-entry-summary`
- choose one actually free local port
- plan one explicit build command and one explicit preview command
- run the build command
- start the preview server and verify that it responds
- return one contract-approved launch URL

This skill does not:

- modify the test-entry base
- add screens directly
- guess unsupported screen names
- invent ad hoc launch steps outside the public contract

## Workflow

1. Run the summary checker:
   ```bash
   python <skill-dir>/scripts/check_summary.py [--requested-screen <screen>] [--requested-auth <mode>] [--requested-preset <preset>]
   ```
2. If the checker returns `screen_match_kind=verified-alias`, prefer that canonical public screen directly.
3. If the checker returns `reason=unsupported_screen`, first consider whether there is exactly one obvious provisional candidate among the current supported screens. Only do this when the candidate is singular and high-confidence.
4. If there is no single obvious provisional candidate, stop immediately, list the supported values, and ask the user to choose exactly one next action:
   - use one existing supported screen
   - hand off to `test-init` for permanent extension
5. Run the build-preview planner:
   ```bash
   python <skill-dir>/scripts/plan_build_preview.py
   ```
6. Read [references/contract-consumption.md](references/contract-consumption.md) only after the summary gate has passed and only before composing the final URL.
7. Read [references/port-selection.md](references/port-selection.md) only if you are about to override the planner's suggested port.
8. Start the preview path with this skill's starter script:
   ```bash
   python <skill-dir>/scripts/start_preview_server.py --port <port>
   ```
9. Run the launch finalizer:
   ```bash
   python <skill-dir>/scripts/finalize_launch.py --base-url http://127.0.0.1:<port>/ [--screen <screen>] [--auth <mode>] [--preset <preset>]
   ```
10. If `finalize_launch.py` returns `next_action=offer-supported-or-test-init`, stop immediately and ask the user to choose between one existing supported screen or `test-init`.
11. If you launched a provisional candidate for a natural-language page request, present it as provisional. Only persist the alias after the user confirms it is the intended page.
12. When the user confirms a provisional candidate, record the alias:
   ```bash
   python <skill-dir>/scripts/record_verified_alias.py --alias <user-phrase> --screen <screen> --evidence <short-evidence>
   ```
13. Return exactly one verified URL and the key limitation from the summary, if relevant.

## Utility scripts

- `scripts/check_summary.py`
  Returns the summary gate decision, supported values, alias resolution, and the requested screen/auth/preset support status.

- `scripts/plan_build_preview.py`
  Reads the public contract and returns:
  - `ok`
  - `summary_path`
  - `build_command`
  - `preview_command`
  - `port`
  - `reason`

- `scripts/start_preview_server.py`
  Runs the planned build command, starts the preview server, waits for HTTP readiness, and returns:
  - `ok`
  - `pid`
  - `base_url`
  - `build_command`
  - `preview_command`
  - `stdout_log`
  - `stderr_log`
  - `status_code`
  - `content_type`
  - `diagnosis`

- `scripts/finalize_launch.py`
  Verifies the base app response and builds one URL from the public contract.

- `scripts/record_verified_alias.py`
  Records a user-confirmed alias for this project.

## Decision rules

- Treat `test-entry-summary` as the only public contract.
- Require `protocol_version=2` and `launch_mode=build-preview`.
- Use the summary's recorded build and preview commands instead of inventing launch steps.
- If the requested screen is missing from `supported_screens`, stop immediately.
- Only previously verified aliases may resolve directly without extra confirmation.
- Provisional candidate matching is allowed only when exactly one supported screen is an obvious fit.
- Do not record a new alias until the user confirms the provisional candidate matched the intended page.
- Do not guess or hardcode a URL.
- Choose an actually free local port from the current machine state. Do not assume `3000`, `4173`, or `5173`.
- The build must complete successfully before the launch is considered valid.
- A running preview process is not enough. The service must answer HTTP requests before you return a URL.
- Return one URL, not a list of speculative candidates.

## Verification gate

Do not consider the launch complete unless all of the following are true:

- the project has a valid build-first `test-entry-summary`
- the selected port is not already occupied
- the build command and preview command were planned explicitly
- the build succeeded
- the previewed service responds over HTTP
- the returned URL matches the public contract

If you could not confirm service ownership beyond basic HTTP response, say so explicitly instead of overstating certainty.
