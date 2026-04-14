from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def slugify(value: str) -> str:
    lowered = value.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = lowered.strip("-")
    return lowered or "capture"


def default_output(url: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = slugify(url)
    return Path.cwd() / ".codex-artifacts" / "test-screenshot" / f"{timestamp}-{slug}.png"


def load_request_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def merge_config(args: argparse.Namespace) -> dict[str, Any]:
    request_payload: dict[str, Any] = {}
    if args.request_file:
        request_payload = load_request_file(Path(args.request_file))

    def pick(name: str, default: Any = None) -> Any:
        value = getattr(args, name)
        if value is not None:
            return value
        return request_payload.get(name, default)

    merged = {
        "url": pick("url"),
        "output": pick("output"),
        "wait_selector": pick("wait_selector"),
        "wait_expression": pick("wait_expression"),
        "timeout": int(pick("timeout", 30000)),
        "browser": pick("browser", "chromium"),
        "full_page": bool(args.full_page or request_payload.get("full_page", False)),
        "wait_images": bool(args.wait_images or request_payload.get("wait_images", False)),
        "asset_timeout": int(pick("asset_timeout", 5000)),
    }
    if not merged["url"]:
        raise ValueError("A capture URL is required")
    return merged


def runtime_dir() -> Path:
    return Path.home() / ".codex-runtime" / "test-screenshot-playwright"


def ensure_playwright_runtime() -> Path:
    runtime = runtime_dir()
    package_json = runtime / "package.json"
    package_lock = runtime / "package-lock.json"
    playwright_package = runtime / "node_modules" / "playwright" / "package.json"
    runtime.mkdir(parents=True, exist_ok=True)

    if not package_json.exists():
        package_json.write_text(
            json.dumps(
                {
                    "name": "codex-test-screenshot-runtime",
                    "private": True,
                    "type": "module",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    if playwright_package.exists():
        return runtime

    npm_executable = shutil.which("npm.cmd") or shutil.which("npm") or "npm"
    command = [
        npm_executable,
        "install",
        "playwright",
        "--no-save",
        "--silent",
        "--package-lock=false",
        "--no-fund",
        "--no-audit",
    ]
    completed = subprocess.run(
        command,
        cwd=runtime,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    if completed.returncode != 0 or not playwright_package.exists():
        diagnosis = completed.stderr.strip() or completed.stdout.strip() or "Playwright runtime installation failed"
        raise RuntimeError(diagnosis)

    if package_lock.exists():
        try:
            package_lock.unlink()
        except OSError:
            pass
    return runtime


def runner_source() -> str:
    return """import fs from 'node:fs/promises';
import { chromium, firefox, webkit } from 'playwright';

const configPath = process.argv[2];
const config = JSON.parse(await fs.readFile(configPath, 'utf8'));
const browserType = { chromium, firefox, webkit }[config.browser] || chromium;
const browser = await browserType.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await context.newPage();
const failedRequests = [];
const blockingResourceTypes = new Set(['document', 'stylesheet', 'image', 'font', 'script']);

page.on('requestfailed', request => {
  if (failedRequests.length >= 10) return;
  const failure = request.failure();
  failedRequests.push({
    url: request.url(),
    resourceType: request.resourceType(),
    errorText: failure?.errorText || 'requestfailed'
  });
});

async function waitForVisualAssets(assetTimeout) {
  if (!assetTimeout || assetTimeout <= 0) {
    return { ok: true, checkedImages: 0, unresolvedImages: [], imageFailures: [], checkedBackgrounds: 0, unresolvedBackgrounds: [] };
  }
  return await page.evaluate(async timeout => {
    const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
    const nextFrame = () => new Promise(resolve => requestAnimationFrame(() => resolve()));
    const deadline = Date.now() + timeout;
    const backgroundUrlPattern = /url\\((['"]?)(.*?)\\1\\)/g;

    if (document.fonts?.ready) {
      try {
        await document.fonts.ready;
      } catch {}
    }

    const visibleImages = () =>
      Array.from(document.images).filter(img => {
        const rect = img.getBoundingClientRect();
        const style = window.getComputedStyle(img);
        return (
          style.display !== 'none' &&
          style.visibility !== 'hidden' &&
          rect.width > 0 &&
          rect.height > 0
        );
      });

    const unresolvedImages = () =>
      visibleImages().filter(img => !img.complete || img.naturalWidth === 0);

    const visibleElements = () =>
      Array.from(document.querySelectorAll('*')).filter(element => {
        const rect = element.getBoundingClientRect();
        const style = window.getComputedStyle(element);
        return (
          style.display !== 'none' &&
          style.visibility !== 'hidden' &&
          rect.width > 0 &&
          rect.height > 0
        );
      });

    const backgroundUrls = () => {
      const urls = new Set();
      for (const element of visibleElements()) {
        const style = window.getComputedStyle(element);
        const source = `${style.backgroundImage || ''},${style.maskImage || ''}`;
        for (const match of source.matchAll(backgroundUrlPattern)) {
          const url = (match[2] || '').trim();
          if (!url || url.startsWith('data:')) continue;
          urls.add(new URL(url, window.location.href).href);
        }
      }
      return Array.from(urls);
    };

    const decodeBackgrounds = async () => {
      const urls = backgroundUrls();
      const results = await Promise.allSettled(
        urls.map(async url => {
          const image = new Image();
          image.decoding = 'async';
          image.src = url;
          try {
            await image.decode();
          } catch {
            await new Promise((resolve, reject) => {
              image.onload = () => resolve(null);
              image.onerror = () => reject(new Error(url));
            });
          }
          return url;
        })
      );
      const unresolved = [];
      for (const result of results) {
        if (result.status === 'rejected') {
          unresolved.push(String(result.reason?.message || result.reason || '<unknown-background>'));
        }
      }
      return { checked: urls.length, unresolved };
    };

    const decodePendingImages = async () => {
      const current = unresolvedImages();
      await Promise.allSettled(
        current.map(async img => {
          try {
            await img.decode();
          } catch {}
        })
      );
    };

    while (Date.now() < deadline) {
      await decodePendingImages();
      const backgrounds = await decodeBackgrounds();
      const pending = unresolvedImages();
      if (!pending.length && !backgrounds.unresolved.length) {
        await nextFrame();
        await nextFrame();
        return {
          ok: true,
          checkedImages: visibleImages().length,
          unresolvedImages: [],
          imageFailures: [],
          checkedBackgrounds: backgrounds.checked,
          unresolvedBackgrounds: []
        };
      }
      await sleep(150);
    }

    const pending = unresolvedImages();
    const backgrounds = await decodeBackgrounds();
    return {
      ok: false,
      checkedImages: visibleImages().length,
      unresolvedImages: pending.map(img => img.currentSrc || img.src || img.alt || '<unknown-image>'),
      imageFailures: pending.map(img => ({
        src: img.currentSrc || img.src || '<unknown-image>',
        complete: img.complete,
        naturalWidth: img.naturalWidth,
        naturalHeight: img.naturalHeight
      })),
      checkedBackgrounds: backgrounds.checked,
      unresolvedBackgrounds: backgrounds.unresolved
    };
  }, assetTimeout);
}

try {
  await page.goto(config.url, { waitUntil: 'domcontentloaded', timeout: config.timeout });

  if (config.wait_selector) {
    await page.waitForSelector(config.wait_selector, { timeout: config.timeout, state: 'visible' });
  }
  if (config.wait_expression) {
    await page.waitForFunction(config.wait_expression, null, { timeout: config.timeout });
  }

  await page.waitForLoadState('networkidle', { timeout: Math.min(config.asset_timeout || 0, 3000) }).catch(() => {});

  let assetWait = { ok: true, checkedImages: 0, unresolvedImages: [], imageFailures: [] };
  if (config.wait_images) {
    assetWait = await waitForVisualAssets(config.asset_timeout);
    if (!assetWait.ok) {
      throw new Error(`Visible images did not finish loading before capture: ${JSON.stringify(assetWait)}`);
    }
  }

  await page.screenshot({
    path: config.output_path,
    fullPage: Boolean(config.full_page),
    animations: 'disabled'
  });

  console.log(JSON.stringify({
    ok: true,
    asset_wait: assetWait,
    failed_requests: failedRequests,
    blocking_failed_requests: failedRequests.filter(request => blockingResourceTypes.has(request.resourceType))
  }));
  await browser.close();
} catch (error) {
  console.log(JSON.stringify({
    ok: false,
    diagnosis: error instanceof Error ? error.message : String(error),
    failed_requests: failedRequests,
    blocking_failed_requests: failedRequests.filter(request => blockingResourceTypes.has(request.resourceType))
  }));
  await browser.close();
  process.exit(1);
}
"""


def ensure_runner(runtime: Path) -> Path:
    runner_path = runtime / "capture-runner.mjs"
    desired = runner_source()
    if not runner_path.exists() or runner_path.read_text(encoding="utf-8") != desired:
        runner_path.write_text(desired, encoding="utf-8")
    return runner_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request-file")
    parser.add_argument("--url")
    parser.add_argument("--output")
    parser.add_argument("--wait-selector")
    parser.add_argument("--wait-expression")
    parser.add_argument("--timeout", type=int)
    parser.add_argument("--browser")
    parser.add_argument("--asset-timeout", type=int)
    parser.add_argument("--full-page", action="store_true")
    parser.add_argument("--wait-images", action="store_true")
    args = parser.parse_args()

    try:
        config = merge_config(args)
        output_path = (Path(config["output"]) if config["output"] else default_output(config["url"])).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        config["output_path"] = str(output_path)

        runtime = ensure_playwright_runtime()
        runner_path = ensure_runner(runtime)
        node_executable = shutil.which("node.exe") or shutil.which("node") or "node"

        with tempfile.TemporaryDirectory(prefix="codex-test-screenshot-") as temp_dir:
            config_path = Path(temp_dir) / "capture-config.json"
            config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
            completed = subprocess.run(
                [node_executable, str(runner_path), str(config_path)],
                cwd=runtime,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )

        parsed_output = None
        stdout = completed.stdout.strip()
        if stdout:
            try:
                parsed_output = json.loads(stdout.splitlines()[-1])
            except json.JSONDecodeError:
                parsed_output = None

        ok = completed.returncode == 0 and output_path.exists()
        wait_kind = "selector" if config["wait_selector"] else "expression" if config["wait_expression"] else "none"
        diagnosis = "Playwright screenshot captured"
        if not ok:
            diagnosis = (
                (parsed_output or {}).get("diagnosis")
                or completed.stderr.strip()
                or stdout
                or "Playwright screenshot failed"
            )

        result = {
            "ok": ok,
            "url": config["url"],
            "output_path": str(output_path),
            "wait_kind": wait_kind,
            "wait_images": config["wait_images"],
            "diagnosis": diagnosis,
        }
        if isinstance(parsed_output, dict):
            if "asset_wait" in parsed_output:
                result["asset_wait"] = parsed_output["asset_wait"]
            if "failed_requests" in parsed_output:
                result["failed_requests"] = parsed_output["failed_requests"]
            if "blocking_failed_requests" in parsed_output:
                result["blocking_failed_requests"] = parsed_output["blocking_failed_requests"]

        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if ok else 1
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "url": args.url,
                    "output_path": args.output,
                    "wait_kind": "selector" if args.wait_selector else "expression" if args.wait_expression else "none",
                    "wait_images": bool(args.wait_images),
                    "diagnosis": str(exc),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
