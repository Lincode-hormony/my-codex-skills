---
name: test-screenshot
description: "Captures and returns one Playwright screenshot for a page backed by a valid build-plus-preview `test-entry-summary` contract. Use when a supported test screen needs a current screenshot, especially after `test-start` produced a verified URL, and require a screen ready contract instead of timing guesses."
---

# Test Screenshot

Use this skill to return one current screenshot from a contract-backed page. Consume `test-entry-summary` first. Do not modify the test base directly.

## First Decision

Before planning a capture:

1. run `python <skill-dir>/scripts/check_summary.py [--requested-screen <screen>] [--requested-auth <mode>] [--requested-preset <preset>]`
2. choose exactly one mode:
   - `capture provided url`
   - `capture supported screen`

If no valid summary exists, stop and tell the user to prepare the project with `test-init` first. If the checker returns `next_action` other than `proceed`, stop immediately.

## Scope

This skill does:

- validate that the project exposes a usable build-first `test-entry-summary`
- reuse an existing URL or call `test-start` when a base URL is missing
- build one contract-allowed target URL
- require a ready strategy for screenshot-capable contract screens
- capture one Playwright screenshot
- return the image by calling `view_image`

This skill does not:

- modify the test-entry base
- add screens directly
- invent unsupported screen names or query parameters
- fall back to blind sleeps as the primary readiness model

## Workflow

Copy this checklist into working notes and keep the order:

```text
Test Screenshot Progress:
- [ ] Step 1: Run summary check
- [ ] Step 2: Resolve capture mode and verified screen name
- [ ] Step 3: Obtain one verified base URL
- [ ] Step 4: Prepare one capture-request file
- [ ] Step 5: Run capture wrapper
- [ ] Step 6: View image and report limitations
```

1. Run the summary checker:
   ```bash
   python <skill-dir>/scripts/check_summary.py [--requested-screen <screen>] [--requested-auth <mode>] [--requested-preset <preset>]
   ```
2. If the checker returns `reason=unsupported_screen`, `unsupported_auth`, `unsupported_preset`, or `screen_not_capture_ready`, stop immediately, list the supported values, and ask the user to choose exactly one next action:
   - capture one existing supported screen
   - hand off to `test-init` for permanent extension
3. If the user named a page rather than a stable public screen, normalize it to one stable screen name. Do not guess between multiple plausible names.
4. If the user already provided a reachable full URL, use it directly as the capture target.
5. Otherwise, if the user provided only a base URL or only a target screen, use `test-start` to produce one verified URL before continuing.
6. If a specific screen, auth mode, or preset still needs to be applied to a base URL, run:
   ```bash
   python <skill-dir>/scripts/prepare_capture_target.py --base-url http://127.0.0.1:<port>/ [--screen <screen>] [--auth <mode>] [--preset <preset>] [--capture-request-file <json-path>]
   ```
7. If `prepare_capture_target.py` returns `next_action` other than `proceed`, stop immediately.
8. Treat the capture-request file as the default execution path. Do not hand-rewrite the selector or URL through multiple shell-quoting variants unless the request file path is genuinely unavailable.
9. Run the Playwright capture wrapper:
   ```bash
   python <skill-dir>/scripts/capture_playwright.py --request-file <json-path> [--output <png-path>] [--full-page]
   ```
10. The capture wrapper should wait for the contract-defined ready signal first, then wait for visible image, background-image, and font assets to settle before the screenshot is written.
11. If the first capture fails because the page is not ready, retry once with the exact same capture-request file or an updated file produced by `prepare_capture_target.py`. Do not invent a new wait model.
12. If the capture fails because visible assets never finish loading, say so directly and surface the failed-request diagnosis instead of silently returning a partial image.
13. Call `view_image` on the resulting PNG file.
14. Return the screenshot path, the captured URL, and the most relevant limitation from the summary when it matters for interpretation.

## Utility scripts

- `scripts/check_summary.py`
  Returns the summary gate decision, supported values, alias resolution, and whether the requested screen is screenshot-ready.

- `scripts/prepare_capture_target.py`
  Verifies the base URL, builds one contract-allowed screenshot URL, returns the ready strategy for the selected screen, and can write a capture-request JSON file for the wrapper.

- `scripts/capture_playwright.py`
  Opens the page with Playwright, waits on one contract-defined readiness signal, waits for visible image, background-image, and font assets when requested, captures one PNG, and returns:
  - `ok`
  - `url`
  - `output_path`
  - `wait_kind`
  - `wait_images`
  - `diagnosis`

Dependency note:

- The wrapper uses a persistent runtime under `~/.codex-runtime/test-screenshot-playwright`.
- If `playwright` is missing there, the script installs it automatically before capture.
- If runtime installation is blocked, stop and report that blocker directly instead of falling back to a different capture stack.

## Decision rules

- Treat `test-entry-summary` as the only public contract.
- Require `protocol_version=2` and `launch_mode=build-preview`.
- If the user did not provide a reachable URL, use `test-start` instead of inventing launch steps here.
- If the requested screen is not in `supported_screens`, stop immediately.
- If the requested screen is not marked screenshot-ready, stop immediately.
- Never use UI traversal from a different supported screen to simulate an unsupported target page.
- Do not write temporary DOM-driving scripts to bypass the public contract.
- Prefer the screen's declared ready strategy over fixed sleeps.
- Prefer the wrapper's request-file path as the default path, not just when selector syntax is complex.
- Return one screenshot image, not a gallery of speculative captures.

## Verification gate

Do not consider the capture complete unless all of the following are true:

- the project has a valid build-first `test-entry-summary`
- the capture target URL is reachable
- the capture URL matches the public contract when a contract-backed screen is requested
- a contract-defined ready strategy was used for screenshot-capable screens
- visible image and font assets were given a chance to settle before capture when the wrapper requested it
- Playwright wrote a PNG file successfully
- `view_image` was called on the final PNG

If the capture succeeded but the page may still reflect a partial mock state or test-only limitation, say so explicitly instead of overstating certainty.
