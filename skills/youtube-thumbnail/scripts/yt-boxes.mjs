#!/usr/bin/env node
// yt-boxes.mjs — "AI LABS" thumbnail style: solid dark bg + bold sans + highlight boxes
// + optional real face cutout (right) + small brand icon. Perfect Cyrillic (text is ours).
//
// Markup inside --l1/--l2:
//   [[word]] -> YELLOW box, black text   (the marker hook)
//   <<word>> -> WHITE box, black text
//   plain    -> white text on the dark bg
//
// Usage:
//   node yt-boxes.mjs --l1 "[[АГЕНТЫ]]" --l2 "ДЛЯ БИЗНЕСА" --eyebrow "CLAUDE CODE" \
//     --face cutout.png --icon claude-code.svg --font inter --out out.png [--bg "#0A0A0A"]
//   --fontfile path.ttf overrides --font (local premium font).

import { readFileSync, writeFileSync, existsSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createRequire } from "node:module";

const arg = (n, d = "") => { const i = process.argv.indexOf("--" + n); return i > -1 && process.argv[i + 1] ? process.argv[i + 1] : d; };
const l1 = arg("l1"), l2 = arg("l2"), eyebrow = arg("eyebrow");
const face = arg("face"), icon = arg("icon"), out = arg("out", "/tmp/yt-boxes.png");
const bg = arg("bg", "#0A0A0A");
const fs1 = arg("fs", "128");
const faceside = arg("faceside", "right");
const YELLOW = "#EEFF00", WHITE = "#FFFFFF", BLACK = "#0A0A0A", ORANGE = "#D97757";
const FONTS = {
  inter: { q: "Inter:wght@800;900", fam: "'Inter'" },
  montserrat: { q: "Montserrat:wght@900", fam: "'Montserrat'" },
  hanken: { q: "Hanken+Grotesk:wght@800;900", fam: "'Hanken Grotesk'" },
  manrope: { q: "Manrope:wght@800", fam: "'Manrope'" },
};
const font = FONTS[arg("font", "inter")] || FONTS.inter;
const fontfile = arg("fontfile", "");
const useLocal = fontfile && existsSync(fontfile);
const headFam = useLocal ? "'CustomHead'" : font.fam;
const faceRule = useLocal ? `@font-face{font-family:'CustomHead';src:url('file://${fontfile}')}` : "";

if (face && !existsSync(face)) { console.error("ERR --face not found:", face); process.exit(1); }

const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
// parse markup -> spans. Process [[..]] and <<..>> then plain words.
function renderLine(line) {
  if (!line) return "";
  const tokens = [];
  const re = /\[\[(.+?)\]\]|<<(.+?)>>|([^\[\]<>]+)/g;
  let m;
  while ((m = re.exec(line)) !== null) {
    if (m[1] !== undefined) tokens.push(`<span class="box yellow">${esc(m[1])}</span>`);
    else if (m[2] !== undefined) tokens.push(`<span class="box white">${esc(m[2])}</span>`);
    else {
      // plain run -> split into words, keep spaces
      for (const w of m[3].split(/(\s+)/)) {
        if (/^\s+$/.test(w)) tokens.push(`<span class="sp"> </span>`);
        else if (w) tokens.push(`<span class="plain">${esc(w)}</span>`);
      }
    }
  }
  return `<div class="line">${tokens.join("")}</div>`;
}

const faceRight = faceside === "right";
const html = `<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=${font.q}&family=JetBrains+Mono:wght@700&display=swap" rel="stylesheet">
<style>
  ${faceRule}
  *{margin:0;padding:0;box-sizing:border-box}
  html,body{width:1280px;height:720px;overflow:hidden;background:${bg};font-family:${headFam},sans-serif}
  .stage{position:relative;width:1280px;height:720px;overflow:hidden;background:${bg}}
  .face{position:absolute;bottom:0;${faceRight ? "right:-1%" : "left:-1%"};height:104%;filter:drop-shadow(0 14px 36px rgba(0,0,0,.6))}
  .wrap{position:absolute;top:0;bottom:0;${faceRight ? "left:64px" : "right:64px"};width:64%;display:flex;flex-direction:column;justify-content:center;align-items:${faceRight ? "flex-start" : "flex-end"}}
  .eyebrow{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:28px;letter-spacing:.16em;color:${ORANGE};text-transform:uppercase;margin-bottom:22px;display:flex;align-items:center;gap:14px}
  .eyebrow img{height:40px}
  .line{display:flex;flex-wrap:wrap;align-items:center;font-weight:900;font-size:${fs1}px;line-height:1.08;letter-spacing:-.02em;color:#fff}
  .line + .line{margin-top:14px}
  .plain{color:#fff}
  .sp{width:.28em}
  .box{color:${BLACK};padding:.02em .16em .08em;border-radius:.1em;display:inline-block}
  .box.yellow{background:${YELLOW}}
  .box.white{background:${WHITE}}
</style></head>
<body><div class="stage">
  ${face ? `<img class="face" src="file://${face}">` : ""}
  <div class="wrap">
    ${eyebrow ? `<div class="eyebrow">${icon && existsSync(icon) ? `<img src="file://${icon}">` : ""}${esc(eyebrow)}</div>` : ""}
    ${renderLine(l1)}
    ${renderLine(l2)}
  </div>
</div></body></html>`;

const tmpHtml = join(tmpdir(), "yt-boxes-" + Date.now() + ".html");
writeFileSync(tmpHtml, html);
const require = createRequire(import.meta.url);
let chromium;
for (const p of ["playwright", "/opt/homebrew/lib/node_modules/playwright"]) { try { ({ chromium } = require(p)); break; } catch (_) {} }
if (!chromium) { console.error("ERR: playwright not found"); process.exit(1); }
const nfs = require("node:fs"); const base = "/Users/jasonqwwen/Library/Caches/ms-playwright"; let SHELL = process.env.SHELL_CHROME;
if (!SHELL) { try { for (const d of nfs.readdirSync(base)) if (d.startsWith("chromium_headless_shell")) SHELL = `${base}/${d}/chrome-headless-shell-mac-arm64/chrome-headless-shell`; } catch (_) {} }
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
