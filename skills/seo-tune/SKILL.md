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
- **GEO** (LLM / agent discovery): a deliberate AI-crawler robots policy, IndexNow so
  new pages get picked up fast, and (optional, experimental) `llms.txt`.

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

## Step 1 — audit (report, then STOP)

Walk the site (the built HTML files, or fetch the live pages) and check each item.
Report a checklist `[есть]/[нет]` first, then **STOP and wait for the owner's explicit
approval before you change anything.** Do not proceed to Step 2 until they say go.

Presence is not enough — check that each page is **effectively indexable** and that its
canonical is **correct**, or the audit will "pass" a site that is actually invisible to
search or silently collapsing into one URL. A `Disallow: /`, an all-`noindex` site, or a
site where every page canonicals to the homepage must **FAIL** this audit, not pass it.

| Layer | Check | Where |
|---|---|---|
| SEO | `robots.txt` exists, points to the sitemap, and does NOT block indexing (see effective indexability) | `/robots.txt` |
| SEO | `sitemap.xml` lists only the desired indexable canonical URLs, absolute `<loc>` | `/sitemap.xml` |
| SEO | every page has a unique, real `<title>` and `<meta name="description">` | `<head>` |
| SEO | every page has exactly ONE absolute, correct `<link rel="canonical">` (see canonical correctness) | `<head>` |
| SEO | Open Graph (`og:title` + `og:type` + `og:image` + `og:url`; `og:image:alt` when an image is set) + `twitter:card` | `<head>` |
| AEO | article pages carry `Article`/`BlogPosting` JSON-LD | `references/jsonld-recipes.md` |
| AEO | Q&A / how-to pages carry `FAQPage`/`HowTo` JSON-LD (AEO / AI engines only — no Google rich result) | same |
| AEO | home page carries the truthful site-subject type (`Organization`/`Person`/`LocalBusiness`/…) + `WebSite` JSON-LD | same |
| GEO | `llms.txt` exists (optional, experimental — see note) | `references/llms-txt.md` |
| GEO | robots.txt reflects the owner's chosen AI-crawler policy (allow OR intentionally block) | `references/llms-txt.md` |
| GEO | IndexNow key file is published and pages get pinged on publish | `references/indexnow.md` |

### Effective indexability (presence ≠ indexable — do not skip)

A file that merely exists can still be fully blocked. For each page, verify it is
**actually indexable**:

- **robots.txt rules that apply to the REAL crawler.** `robots.txt` is
  most-specific-group-wins (RFC 9309): work out the group Googlebot / YandexBot actually
  match, not just the `*` group. `Disallow: /` — under `*` OR under the engine's own
  user-agent — means the site is blocked. FAIL it.
- **HTML `noindex`:** `<meta name="robots" content="noindex">` (or a `googlebot` /
  `yandex`-specific meta) removes the page from the index even if robots.txt allows
  crawling.
- **HTTP `noindex`:** an `X-Robots-Tag: noindex` response header does the same,
  invisibly. Check the response headers, not just the HTML.
- **Final HTTP status:** the URL must return a final `200` — not a redirect chain, a
  `4xx/5xx`, or a login / paywall. A canonical or sitemap URL that 301s or 404s is a bug.
- **Rendered content:** the main content must actually be present after render. For a
  JS-heavy site, an empty HTML shell that never hydrates has nothing to index — confirm
  the real content is in what a crawler receives.

Sources: [Google robots meta / noindex](https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag),
[Yandex robots.txt](https://yandex.com/support/webmaster/en/controlling-robot/robots-txt).

### Canonical correctness (presence ≠ correct)

`<link rel="canonical">` is a strong consolidation signal — a wrong one can collapse a
whole multi-page site into a single URL. For each page verify:

- **Exactly one** canonical, and it is an **absolute** URL on your one chosen origin.
- The canonical URL is itself **indexable** (returns 200, not `noindex`, not redirected).
- It **matches this page's content** — a page's canonical should point to itself (or a
  genuine duplicate), never to an unrelated page.
- **BUG to flag:** every page carrying the SAME canonical (typically → the homepage).
  This tells search engines every page IS the homepage and de-indexes the rest. This is
  exactly the kind of existing tag that must be FIXED, not preserved — "don't break what
  works" does not apply to a page-collapsing canonical.
- **Built-file → public-URL mapping:** do not mechanically append the file path to
  `SITE_URL`. `/about/index.html` on disk is usually the public `/about/`; handle
  trailing slashes, query parameters, localized (i18n / hreflang) variants and redirected
  URLs deliberately, not by string concatenation.

Sources: [Google canonicalization](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls),
[Yandex canonical](https://yandex.com/support/webmaster/en/robot-workings/canonical).

## Step 2 — generate what's missing (only after approval)

For each gap, use the recipe file, filling in the user's real `SITE_URL`/`BRAND`:

- **robots.txt / sitemap.xml** — generate the sitemap from only the desired indexable
  canonical URLs (see the sitemap rules + template below). `<lastmod>` is optional and
  should reflect a real content change; a build mtime that bumps on every deploy is as
  misleading as `now`, so omit it rather than fake it.
- **`<head>` tags** — unique real title + a description that summarizes the page (aim
  ~140–160 chars as an editorial heuristic — there is no fixed Google limit and the
  snippet is trimmed per device/query). Canonical = the page's real public URL on your
  one origin (mind the built-file mapping caveat above). OG image per-page if you have
  one, else a site default.
- **JSON-LD** — `references/jsonld-recipes.md`. Pick the TRUTHFUL subject type for the
  home page (`Organization` only if the site is an organization; `Person` for a personal
  site; `LocalBusiness`/`OnlineStore` where those fit). One
  `<script type="application/ld+json">` per block in `<head>`.
- **llms.txt** — `references/llms-txt.md` (optional, experimental).
- **IndexNow** — `references/indexnow.md` (generate the key, publish the key file, ping
  once on every publish — one endpoint fans out to the others).

## sitemap.xml — generation rules + template

Include **only the URLs you want indexed**: the canonical, indexable pages. Exclude
redirects, `noindex` pages, duplicates, 404s, login and purely technical pages.

- Absolute `<loc>` URLs on your one chosen origin, canonical-consistent (the same URL you
  set as `<link rel="canonical">`).
- UTF-8 encoding, an XML declaration, the sitemap namespace, and XML-escaped entities
  (`&` → `&amp;`, `<` → `&lt;`, …).
- Max **50,000 URLs / 50 MB** per file; beyond that, split into multiple sitemaps and add
  a sitemap index.
- `<lastmod>` is **optional**; if present, use a W3C-datetime value that reflects a real
  content change (not `now`, not a deploy mtime).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/</loc>
    <lastmod>2026-07-05</lastmod>
  </url>
  <url>
    <loc>https://example.com/blog/first-post/</loc>
    <lastmod>2026-07-05</lastmod>
  </url>
</urlset>
```

Sources: [Google build a sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap),
[Yandex sitemap format](https://yandex.com/support/webmaster/en/controlling-robot/sitemap).

## Rules

- **Truthful metadata only.** Description must match the page; JSON-LD fields must match
  visible content. Mismatched / misleading structured data can lose a page its
  rich-result eligibility or trigger a structured-data manual action — but Google states
  this does not change normal web ranking, and Yandex simply ignores markup it can't
  trust rather than penalizing it. So mark up honestly for eligibility; there is no
  "ranking penalty" for a bad block, only lost eligibility.
  [Google structured-data policies](https://developers.google.com/search/docs/appearance/structured-data/sd-policies).
- **The user's own IDs/keys/domain — always.** Never invent analytics IDs or reuse
  someone else's IndexNow key. If they don't use analytics, leave it out.
- **Don't break what works.** Read a page's existing `<head>` before editing; add missing
  tags, don't duplicate ones already there. **Exception:** an actively harmful existing
  tag — a page-collapsing canonical, a stray `noindex`, a `Disallow: /` — is a bug to fix,
  not "what works" to preserve.
- One canonical origin. Pick `https://` + one host (www or bare, not both) and be
  consistent across canonical, sitemap and OG.

## Files

- `references/jsonld-recipes.md` — copy-paste JSON-LD for the common page types.
- `references/llms-txt.md` — llms.txt + the AI-crawler allowlist (GEO).
- `references/indexnow.md` — IndexNow key + ping (fast indexing on Yandex & Bing).
