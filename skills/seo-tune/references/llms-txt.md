# llms.txt + AI-crawler allowlist (GEO)

GEO = making your site discoverable and quotable by LLMs and AI agents, not just
search engines. Two pieces: a `llms.txt` map, and a robots policy that lets the AI
crawlers in.

## llms.txt

A markdown file at the site root (`SITE_URL/llms.txt`) that gives an LLM a clean
map of your site — think "sitemap for language models". Format (the emerging
convention):

```markdown
# BRAND

> One-sentence description of what this site is about.

## Guides
- [Title of guide](SITE_URL/guides/title/): one-line summary.
- [Another guide](SITE_URL/guides/another/): one-line summary.

## About
- [About](SITE_URL/about/): who's behind this.
```

Rules:
- List your REAL, important pages with a short summary each.
- Absolute URLs (`SITE_URL/...`), not relative.
- Keep it current — regenerate it when you publish.

## llms-full.txt (optional)

Same idea, but concatenates the actual text content of your key pages into one
file (`SITE_URL/llms-full.txt`) so a model can read the whole site in one fetch.
Worth it for small sites; skip if large.

## robots.txt — the AI-crawler policy is the OWNER's call (ask first)

This is an opt-in decision, not a default edit. Before writing any AI-crawler
lines, ask the site owner about three SEPARATE policies — they are not the same
knob:

1. **Search indexing** — should classic search (Yandex, Google, Bing) crawl and
   index the site at all? (Almost always yes.)
2. **AI citation** — may AI answer engines (GPTBot, OAI-SearchBot, ClaudeBot,
   PerplexityBot, YandexAdditional) fetch pages so the site can be *cited* in AI
   answers?
3. **AI training** — may the content be used to *train* models?
   `Google-Extended` / `Applebot-Extended` / `YandexAdditional` control training
   use WITHOUT affecting normal search indexing — that's the "index me in search,
   but don't train on me" knob.

Only after the owner chooses do you generate the block. Example that ALLOWS both
classic search and AI answer engines (use only if the owner opted in):

```
# robots.txt — classic search + AI answer engines (owner opted in)

User-agent: *
Allow: /

# AI answer engines (allow so your pages can be cited)
User-agent: GPTBot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: Applebot-Extended
Allow: /
User-agent: YandexAdditional
Allow: /

Sitemap: SITE_URL/sitemap.xml
```

To BLOCK a given crawler, use `Disallow: /` under that user-agent instead. Never
allow-all silently — write exactly the policy the owner chose.

## Why this matters

Search sends clicks; AI answers send *mentions*. If your robots blocks GPTBot /
ClaudeBot / PerplexityBot, it can sharply reduce the chance of being cited in
ChatGPT / Claude / Perplexity answers even when you rank #1 in Google. llms.txt +
a deliberate allowlist is how you make yourself eligible to show up there — the
owner decides whether that's what they want.
