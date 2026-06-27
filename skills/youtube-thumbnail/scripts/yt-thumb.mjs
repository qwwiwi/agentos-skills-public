#!/usr/bin/env node
// yt-thumb.mjs — render a 1280x720 YouTube thumbnail, Claude Code palette.
// Layers: scene bg + face cutout (right) + punch text (left) + Claude Code logo badge.
//
// Usage:
//   node yt-thumb.mjs --scene scene.png --face cutout.png --logo claude-code.svg \
//     --eyebrow "CLAUDE CODE · ИИ-АГЕНТЫ" --l1 "1 МЛН ₽" --l2 "→ $900" \
//     --out out.png [--faceside right|left]
//
// --l2 is rendered in the clay-orange accent (#D97757). Cyrillic OK.

import { readFileSync, writeFileSync, existsSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createRequire } from "node:module";

const arg = (n, d = "") => { const i = process.argv.indexOf("--" + n); return i > -1 && process.argv[i + 1] ? process.argv[i + 1] : d; };
const scene = arg("scene"), face = arg("face"), logo = arg("logo");
const eyebrow = arg("eyebrow"), l1 = arg("l1"), l2 = arg("l2");
const out = arg("out", "/tmp/yt-thumb.png");
const faceside = arg("faceside", "right");
const fs1 = arg("fs", "150");
// font options (all Cyrillic-capable, thumbnail-strong)
const FONTS = {
  intertight: { q: "Inter+Tight:wght@800;900", fam: "'Inter Tight'" },
  montserrat: { q: "Montserrat:wght@900", fam: "'Montserrat'" },
  oswald: { q: "Oswald:wght@600;700", fam: "'Oswald'" },
  russo: { q: "Russo+One", fam: "'Russo One'" },
  unbounded: { q: "Unbounded:wght@700;800", fam: "'Unbounded'" },
  rubik: { q: "Rubik:wght@800;900", fam: "'Rubik'" },
  manrope: { q: "Manrope:wght@800", fam: "'Manrope'" },
  // serif — Anthropic/Copernicus-style headline lookalikes (Cyrillic-capable, free)
  sourceserif: { q: "Source+Serif+4:opsz,wght@8..60,600;8..60,700;8..60,900", fam: "'Source Serif 4'" },
  spectral: { q: "Spectral:wght@700;800", fam: "'Spectral'" },
  ptserif: { q: "PT+Serif:wght@700", fam: "'PT Serif'" },
  playfair: { q: "Playfair+Display:wght@800;900", fam: "'Playfair Display'" },
};
const font = FONTS[arg("font", "intertight")] || FONTS.intertight;
const fontfile = arg("fontfile", ""); // local .ttf/.otf for headline (premium fonts)
const useLocal = fontfile && existsSync(fontfile);
const headFam = useLocal ? "'CustomHead'" : font.fam;
const faceRule = useLocal ? `@font-face{font-family:'CustomHead';src:url('file://${fontfile}')}` : "";
if (!scene || !existsSync(scene)) { console.error("ERR --scene missing/not found:", scene); process.exit(1); }
if (face && !existsSync(face)) { console.error("ERR --face given but not found:", face); process.exit(1); }

const ORANGE = "#D97757", CREAM = "#F3EEE3", INK = "#0A0806";
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const logoHtml = logo && existsSync(logo) ? `<img class="logo" src="file://${logo}">` : "";
const faceRight = faceside === "right";
// text-side scrim darkens the side under the text
const scrimDir = faceRight ? "to right" : "to left";
const faceCss = faceRight ? "right:-1%;" : "left:-1%; transform:scaleX(1);";
const textCss = faceRight ? "left:64px; text-align:left; align-items:flex-start;" : "right:64px; text-align:right; align-items:flex-end;";

const html = `<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=${font.q}&family=JetBrains+Mono:wght@600;700&display=swap" rel="stylesheet">
<style>
  ${faceRule}
  *{margin:0;padding:0;box-sizing:border-box}
  html,body{width:1280px;height:720px;overflow:hidden;background:${INK};font-family:'Inter Tight',sans-serif}
  .stage{position:relative;width:1280px;height:720px;overflow:hidden}
  .bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
  .scrim{position:absolute;inset:0;background:linear-gradient(${scrimDir}, rgba(10,8,6,.94) 0%, rgba(10,8,6,.82) 30%, rgba(10,8,6,.35) 52%, rgba(10,8,6,0) 66%)}
  .vign{position:absolute;inset:0;box-shadow:inset 0 0 220px 60px rgba(0,0,0,.55)}
  .face{position:absolute;bottom:0;${faceCss}height:104%;filter:drop-shadow(0 18px 40px rgba(0,0,0,.55))}
  .text{position:absolute;top:0;bottom:0;${textCss}display:flex;flex-direction:column;justify-content:center;max-width:66%}
  .eyebrow{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:28px;letter-spacing:.16em;color:${ORANGE};text-transform:uppercase;margin-bottom:18px}
  .l1{font-family:${headFam},sans-serif;font-weight:900;font-size:${fs1}px;line-height:.92;letter-spacing:-.02em;color:${CREAM};text-shadow:0 6px 30px rgba(0,0,0,.6)}
  .l2{font-family:${headFam},sans-serif;font-weight:900;font-size:${fs1}px;line-height:.96;letter-spacing:-.02em;color:${ORANGE};text-shadow:0 6px 30px rgba(0,0,0,.6)}
  .logo{position:absolute;top:40px;${faceRight ? "left:56px" : "right:56px"};height:64px;filter:drop-shadow(0 2px 10px rgba(0,0,0,.5))}
</style></head>
<body><div class="stage">
  <img class="bg" src="file://${scene}">
  <div class="scrim"></div>
  ${face ? `<img class="face" src="file://${face}">` : ""}
  <div class="vign"></div>
  ${logoHtml}
  <div class="text">
    ${eyebrow ? `<div class="eyebrow">${esc(eyebrow)}</div>` : ""}
    ${l1 ? `<div class="l1">${esc(l1)}</div>` : ""}
    ${l2 ? `<div class="l2">${esc(l2)}</div>` : ""}
  </div>
</div></body></html>`;

const tmpHtml = join(tmpdir(), "yt-thumb-" + Date.now() + ".html");
writeFileSync(tmpHtml, html);

const require = createRequire(import.meta.url);
let chromium;
for (const p of ["playwright", "/opt/homebrew/lib/node_modules/playwright"]) { try { ({ chromium } = require(p)); break; } catch (_) {} }
if (!chromium) { console.error("ERR: playwright not found"); process.exit(1); }
const fs = require("node:fs");
const glob = "/Users/jasonqwwen/Library/Caches/ms-playwright";
let SHELL = process.env.SHELL_CHROME;
if (!SHELL) { try { for (const d of fs.readdirSync(glob)) if (d.startsWith("chromium_headless_shell")) { SHELL = `${glob}/${d}/chrome-headless-shell-mac-arm64/chrome-headless-shell"`.replace(/"$/, ""); } } catch (_) {} }

(async () => {
  const b = await chromium.launch(SHELL && existsSync(SHELL) ? { executablePath: SHELL } : {});
  const ctx = await b.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5 }); // -> 1920x1080 output
  const p = await ctx.newPage();
  await p.goto("file://" + tmpHtml, { waitUntil: "networkidle" });
  await p.waitForTimeout(800);
  await p.screenshot({ path: out });
  await b.close();
  try { rmSync(tmpHtml); } catch (_) {}
  console.log(out);
})().catch((e) => { console.error("ERR", e.message); process.exit(1); });
