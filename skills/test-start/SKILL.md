---
name: test-start
description: "Launches and verifies a local dev server for projects that already expose a valid `test-entry-summary` contract. Use when the user wants to start the current project's test-entry environment, return a normal base URL, open a supported screen directly, avoid occupied ports, or route missing-screen requests back to `test-init` for permanent extension."
---

# Test Start

Use this skill to consume an existing `test-entry-summary` contract and return one verified local URL. This skill is a contract consumer only. It must not modify the test-entry base directly.

## First Decision

Before planning a server launch:

1. keep the shell working directory at the target project root; invoke the bundled checker by resolving the script path from this skill directory, for example `python <skill-dir>/scripts/check_summary.py [--requested-screen <screen>] [--requested-auth <mode>] [--requested-preset <preset>]`
2. choose exactly one mode:
   - `normal launch`
   - `launch specific screen`

If no valid summary exists, stop the launch flow and tell the user this project must be prepared with `test-init` first.
If the checker returns `next_action` other than `proceed`, stop immediately. Do not read extra references, do not compose a URL, and do not invent a workaround.

## Scope

This skill does:

- validate the presence of a usable `test-entry-summary`
- choose an actually free local port
- build one explicit dev-server command
- start the planned server with platform-safe executable handling
- verify that the resulting service responds
- return one contract-approved launch URL, which may be a base URL or a direct test-entry URL

This skill does not:

- modify the test-entry base
- add screens directly
- guess unsupported screen names
- trust an occupied port without verification

## Workflow

1. Run the summary checker from this skill directory:
   ```bash
   # keep the current working directory at the project root
   python <skill-dir>/scripts/check_summary.py [--requested-screen <screen>] [--requested-auth <mode>] [--requested-preset <preset>]
   ```
2. If the checker returns `screen_match_kind=verified-alias`, prefer that canonical public screen directly. This means the alias was previously validated and recorded for this project.
3. If the checker returns `reason=unsupported_screen`, first consider whether there is exactly one obvious provisional candidate among the current supported screens. Only do this when the candidate is singular and high-confidence. Treat that candidate as provisional only; do not record a new alias yet.
4. If there is no single obvious provisional candidate, stop immediately, list the supported values, and ask the user to choose exactly one next action:
   - use one existing supported screen
   - hand off to `test-init` for permanent extension
5. If the user asked for a specific page, normalize it to one stable public screen name. Do not guess between multiple plausible screen names.
6. Run the dev-server planner from this skill directory:
   ```bash
   # keep the current working directory at the project root
   python <skill-dir>/scripts/plan_dev_server.py
   ```
7. Read [references/contract-consumption.md](references/contract-consumption.md) only after the summary gate has passed and only before composing the final URL.
8. Read [references/port-selection.md](references/port-selection.md) only if you are about to override the planner's suggestion or reuse an existing port.
9. Start the planned server with this skill's starter script instead of ad hoc shell composition:
   ```bash
   # keep the current working directory at the project root
   python <skill-dir>/scripts/start_dev_server.py --port <port>
   ```
   Use the planner's port. Do not replace this with a handwritten `Start-Process`, `npm run dev`, or `Invoke-WebRequest` chain.
10. Run the launch finalizer from this skill directory:
   ```bash
   # keep the current working directory at the project root
   python <skill-dir>/scripts/finalize_launch.py --base-url http://127.0.0.1:<port>/ [--screen <screen>] [--auth <mode>] [--preset <preset>]
   ```
   If the request is auth-only, still pass `--auth`; the finalizer must return a contract URL with `testEntry=1` instead of collapsing back to the raw base URL.
   If the request targets a specific screen or preset and no auth mode was specified, prefer the contract-supported `bypass` mode automatically when available instead of forcing the user through login first.
   If the summary defines a contract-preferred direct launch for first-screen entry, use the finalizer's returned URL for normal launch as well. Do not force the user through the raw homepage when the contract already provides a faster direct entry path.
11. If `finalize_launch.py` returns `next_action=offer-supported-or-test-init`, stop immediately and ask the user to choose between one existing supported screen or `test-init`. Do not inspect implementation code. Do not invent a substitute flow.
12. If the first finalization attempt fails or times out for a normal contract-allowed request, retry once with contract-allowed screen, auth, or preset values. Do not inspect or modify implementation code, and do not invent new parameters.
13. If `finalize_launch.py` returns `preflight_actions`, consume them exactly as the finalizer returned them. For `normal launch`, treat the finalizer's `url` as the contract-approved launch URL even when it includes preflight query parameters. Do not downgrade it back to the raw base URL, and do not replace it with ad hoc advice.
14. Do not describe a contract preflight as a proven fix unless this exact launch path was runtime-validated in the current project. If validation has not confirmed the mitigation, present it only as a contract-defined preparation step or limitation.
15. If you launched a provisional candidate for a natural-language page request, present it as provisional. Only persist the alias after the user confirms it is the intended page.
16. When the user confirms a provisional candidate, record the alias:
   ```bash
   # keep the current working directory at the project root
   python <skill-dir>/scripts/record_verified_alias.py --alias <user-phrase> --screen <screen> --evidence <short-evidence>
   ```
17. Return exactly one verified URL and the key limitation from the summary, if relevant.

## Utility scripts

- `scripts/check_summary.py`
  Checks common summary locations in the current project and returns:
  - `exists`
  - `path`
  - `valid`
  - `missing_required_fields`
  - `supported_screens`
  - `supported_auth_modes`
  - `supported_presets`
  - `requested_screen`
  - `normalized_screen`
  - `screen_match_kind`
  - `verified_alias_file`
  - `requested_screen_supported`
  - `next_action`
  - `reason`

- `scripts/plan_dev_server.py`
  Reads the local project manifest and returns:
  - `ok`
  - `package_manager`
  - `dev_script`
  - `port`
  - `launcher`
  - `arguments`
  - `command`
  - `reason`

- `scripts/start_dev_server.py`
  Starts the planned dev server with platform-safe executable handling and waits for HTTP readiness. It returns:
  - `ok`
  - `pid`
  - `base_url`
  - `launcher`
  - `arguments`
  - `stdout_log`
  - `stderr_log`
  - `status_code`
  - `content_type`
  - `diagnosis`

- `scripts/finalize_launch.py`
  Verifies the base app response and builds one URL from the public contract. It returns:
  - `ok`
  - `status_code`
  - `content_type`
  - `mode`
  - `url`
  - `diagnosis`
  - `next_action`
  - `preflight_actions`
  - `supported_screens`
  For `normal launch`, the returned `url` may already be a contract-preferred direct entry URL or may include contract-defined preflight query parameters. That returned URL is the one you must give the user.

- `scripts/record_verified_alias.py`
  Records a user-confirmed alias for this project and returns:
  - `ok`
  - `path`
  - `alias`
  - `screen`
  - `diagnosis`

## Decision rules

- Treat `test-entry-summary` as the only public contract.
- If the contract defines a preferred direct launch for first-screen entry, return that URL for normal launch instead of forcing the raw homepage.
- Honor contract-auth requests even without a screen or preset. If `auth` was requested and supported, return a `testEntry=1` URL instead of the raw base URL.
- For direct screen or preset launches, if the contract supports `bypass` and the user did not explicitly request another auth mode, default to `testAuth=bypass`.
- If the summary is missing or invalid, do not launch. Tell the user to use `test-init`.
- If the requested screen is missing from `supported_screens`, stop immediately.
- In that case, return the supported screens and ask the user to choose exactly one next action:
  - use one existing supported screen
  - route the task to `test-init` for permanent extension
- Only previously verified aliases may resolve directly without extra confirmation.
- Provisional candidate matching is allowed only when exactly one supported screen is an obvious fit.
- Do not record a new alias until the user confirms the provisional candidate matched the intended page.
- Do not perform broad semantic exploration across multiple supported screens. Either use one provisional candidate or ask the user.
- Do not guess or hardcode a URL.
- Do not use UI traversal, temporary scripts, or side-channel launch logic to simulate an unsupported screen.
- Resolve bundled scripts and references from this skill's own directory first.
- Resolve bundled script paths from this skill's own directory, but keep the command working directory at the target project root so the scripts inspect the repository instead of the skill folder.
- If a bundled script or reference path fails, re-check the skill-local path first. Do not broad-search the repository before confirming the skill-local resource is truly unavailable.
- Prefer one explicit dev-server command over multiple fallback commands.
- Choose an actually free local port from the current machine state. Do not assume `3000` or `5173`.
- On Windows, rely on the starter script to resolve `npm.cmd` / `yarn.cmd` / `pnpm.cmd`. Do not call `npm` directly with `Start-Process`.
- A running process is not enough. The service must answer HTTP requests before you return a URL.
- Do not return a URL only because a process exists or a port is listening.
- Return one URL, not a list of speculative candidates.
- If the contract publishes normal-launch preflight steps, surface them exactly as returned before the URL.
- If `finalize_launch.py` returns a normal-launch URL with contract-defined preflight query parameters or a contract-preferred direct entry, return that URL exactly. Do not strip the query string and do not substitute the raw base URL.
- Do not overclaim a normal-launch preflight mitigation. If you did not runtime-validate that the mitigation removes the observed slowdown, say that it is a contract-defined preparation step rather than a confirmed performance fix.
- Prefer script output over extra file reads. If `check_summary.py` or `finalize_launch.py` already returned the needed gate decision, do not read more references just to restate it.
- Prefer `start_dev_server.py` output over handwritten recovery probes. Do not manually fall back to frontmost `npm run dev`, ad hoc `Invoke-WebRequest`, or repeated shell variants unless the starter script itself failed and you are explicitly diagnosing that script.

## Verification gate

Do not consider the launch complete unless all of the following are true:

- the project has a valid `test-entry-summary`
- the selected port is not already occupied
- the server command was planned explicitly
- the launched service responds over HTTP
- the returned URL matches the public contract

If you could not confirm service ownership beyond basic HTTP response, say so explicitly instead of overstating certainty.

## Downstream handoff

When this skill succeeds, downstream tools should be able to start from the returned URL alone for normal operations.

Tell downstream tools to:

- read `test-entry-summary` first when they need capability details
- prefer URL entry for lightweight navigation
- prefer `window.__TEST_ENTRY__` only for complex state
- avoid adding ad hoc debug parameters
