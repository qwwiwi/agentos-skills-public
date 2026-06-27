// rasterize an SVG logo to PNG on a dark bg via Playwright. Usage: node rasterize-logo.mjs in.svg out.png [size]
import { writeFileSync, existsSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createRequire } from "node:module";
const [svg, out, sizeArg] = process.argv.slice(2);
const size = parseInt(sizeArg || "600", 10);
const html = `<!doctype html><meta charset=utf-8><style>html,body{margin:0;width:${size}px;height:${size}px;background:#1a1714;display:flex;align-items:center;justify-content:center}img{width:64%;height:64%;object-fit:contain}</style><img src="file://${svg}">`;
const tmp = join(tmpdir(), "rast-" + Date.now() + ".html");
writeFileSync(tmp, html);
const require = createRequire(import.meta.url);
let chromium; for (const p of ["playwright", "/opt/homebrew/lib/node_modules/playwright"]) { try { ({ chromium } = require(p)); break; } catch (_) {} }
const fs = require("node:fs"); const base = "/Users/jasonqwwen/Library/Caches/ms-playwright"; let SHELL;
try { for (const d of fs.readdirSync(base)) if (d.startsWith("chromium_headless_shell")) SHELL = `${base}/${d}/chrome-headless-shell-mac-arm64/chrome-headless-shell`; } catch (_) {}
const b = await chromium.launch(SHELL && existsSync(SHELL) ? { executablePath: SHELL } : {});
const ctx = await b.newContext({ viewport: { width: size, height: size }, deviceScaleFactor: 1 });
const pg = await ctx.newPage(); await pg.goto("file://" + tmp, { waitUntil: "networkidle" }); await pg.waitForTimeout(400);
await pg.screenshot({ path: out }); await b.close(); try { rmSync(tmp); } catch (_) {}
console.log(out);
