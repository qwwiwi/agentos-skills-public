---
name: seo-tune
description: "Audit and tune ANY existing site (static HTML, Astro, Next.js, WordPress export...) for search + AI discovery: SEO (Yandex & Google), AEO (AI answer engines), GEO (LLM/agent discovery). The agent checks robots.txt, sitemap.xml, canonical, meta/OG tags, JSON-LD, llms.txt and IndexNow, then generates whatever is missing. Use when the user says: optimize my site for search / SEO / чтобы находили в поиске / хочу в Яндекс и Google / AI-ответы. Tunes an existing site — it does not build one."
---

# SEO tune — make an existing site findable by search AND by AI

Three layers, one pass:

- **SEO** (classic search — Yandex, Google): robots.txt, sitemap.xml, canonical
  URLs, a real `<title>` + meta description, Open Graph / Twitter cards.
- **AEO** (AI answer engines — so your page is *quotable*): structured data
  (JSON-LD), FAQ blocks with direct question→answer pairs.
- **GEO** (LLM / agent discovery): `llms.txt`, an AI-friendly robots allowlist,
  and IndexNow so new pages get picked up fast.

This skill **tunes a site that already exists**. It doesn't generate a blog from
scratch (that's a bigger, separate tool). Point it at a folder of built HTML, or a
running site, and it fills the gaps.

## Step 0 — ask for the site's basics (never hardcode)

Before touching anything, get these from the user and keep them in a scratch note
(you'll reuse them). Nothing here is baked into the skill — it's all theirs:

- `SITE_URL` — the canonical origin, e.g. `https://example.com`
- `BRAND` — the site / author name
- `LANG` — primary language (e.g. `ru`, `en`)
- Analytics IDs, IF they use them (Yandex Metrika counter, GA4 id) — optional
- IndexNow key — you'll generate one with them in `references/indexnow.md`

## Step 1 — audit (report before you change anything)

Walk the site (the built HTML files, or fetch the live pages) and check each item.
Report a checklist `[есть]/[нет]` first, THEN offer to fix:

| Layer | Check | Where |
|---|---|---|
| SEO | `robots.txt` exists and points to the sitemap | `/robots.txt` |
| SEO | `sitemap.xml` lists every real page, with `<lastmod>` | `/sitemap.xml` |
| SEO | every page has a unique `<title>` and `<meta name="description">` | `<head>` |
| SEO | every page has `<link rel="canonical">` | `<head>` |
| SEO | Open Graph (`og:title/description/image/url`) + `twitter:card` | `<head>` |
| AEO | article pages carry `Article`/`BlogPosting` JSON-LD | `references/jsonld-recipes.md` |
| AEO | pages that answer questions carry `FAQPage`/`HowTo` JSON-LD | same |
| AEO | site-level `Organization` + `WebSite` JSON-LD on the home page | same |
| GEO | `llms.txt` (and optionally `llms-full.txt`) exists | `references/llms-txt.md` |
| GEO | robots.txt allows the major AI crawlers (or intentionally blocks them) | `references/llms-txt.md` |
| GEO | IndexNow key file is published and pages get pinged on publish | `references/indexnow.md` |

## Step 2 — generate what's missing

For each gap, use the recipe file, filling in the user's real `SITE_URL`/`BRAND`:

- **robots.txt / sitemap.xml** — generate from the list of real pages. `sitemap.xml`
  needs a stable `<lastmod>` (use the file's git commit date or mtime, not "now" on
  every build, or search engines learn to ignore it).
- **`<head>` tags** — unique title + 140–160-char description per page, canonical =
  `SITE_URL` + path, OG image (per-page if you have one, else a site default).
- **JSON-LD** — `references/jsonld-recipes.md` (Article, FAQPage, HowTo,
  BreadcrumbList, Organization, WebSite). One `<script type="application/ld+json">`
  per block in `<head>`.
- **llms.txt** — `references/llms-txt.md`.
- **IndexNow** — `references/indexnow.md` (generate the key, publish the key file,
  ping Yandex + Bing on every publish).

## Rules

- **Truthful metadata only.** Description must match the page; JSON-LD fields must
  match visible content. Fake/mismatched structured data gets a page demoted, not
  promoted.
- **The user's own IDs/keys/domain — always.** Never invent analytics IDs or reuse
  someone else's IndexNow key. If they don't use analytics, leave it out.
- **Don't break what works.** Read a page's existing `<head>` before editing; add
  missing tags, don't duplicate ones already there.
- One canonical origin. Pick `https://` + one host (www or bare, not both) and be
  consistent across canonical, sitemap and OG.

## Files

- `references/jsonld-recipes.md` — copy-paste JSON-LD for the common page types.
- `references/llms-txt.md` — llms.txt + the AI-crawler allowlist (GEO).
- `references/indexnow.md` — IndexNow key + ping (fast indexing on Yandex & Bing).
