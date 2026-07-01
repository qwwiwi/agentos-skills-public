#!/usr/bin/env node
// render.mjs — render Instagram carousel slides (HTML -> PNG) via Playwright chromium.
//
// Usage:
//   node render.mjs <slides_dir> <out_dir>
//
// For each slide_*.html in <slides_dir> (sorted), opens it at 1080x1350,
// waits for web fonts, and screenshots it to <out_dir>/<basename>.png.

import { readdirSync, mkdirSync, existsSync } from "node:fs";
import { join, basename } from "node:path";
import { pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const [slidesDir, outDir] = process.argv.slice(2);
if (!slidesDir || !outDir) {
  console.error("Usage: node render.mjs <slides_dir> <out_dir>");
  process.exit(1);
}
if (!existsSync(slidesDir)) {
  console.error("ERR slides dir not found:", slidesDir);
  process.exit(1);
}

// Load Playwright; give a clear install hint if it is missing.
const require = createRequire(import.meta.url);
let chromium;
try {
  ({ chromium } = require("playwright"));
} catch (_) {
  console.error("ERR: playwright not installed. Run:");
  console.error("  npm i playwright && npx playwright install chromium");
  process.exit(1);
}

// Collect slide_*.html, sorted so slide_01 renders before slide_02, etc.
const slides = readdirSync(slidesDir)
  .filter((f) => /^slide_.*\.html$/.test(f))
  .sort();
if (slides.length === 0) {
  console.error("ERR no slide_*.html files in", slidesDir);
  process.exit(1);
}

mkdirSync(outDir, { recursive: true });

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({
    viewport: { width: 1080, height: 1350 },
    deviceScaleFactor: 1, // exact 1080x1350 output, no upscaling
  });
  const page = await ctx.newPage();

  for (const file of slides) {
    const url = pathToFileURL(join(slidesDir, file)).href;
    const out = join(outDir, basename(file, ".html") + ".png");
    await page.goto(url, { waitUntil: "networkidle" });
    await page.evaluate(() => document.fonts.ready); // wait for web fonts
    await page.waitForTimeout(300); // short settle for layout/paint
    await page.screenshot({ path: out });
    console.log(out);
  }

  await browser.close();
})().catch((e) => {
  console.error("ERR", e.message);
  process.exit(1);
});
