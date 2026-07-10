# llms.txt + AI-crawler policy (GEO)

GEO = making your site discoverable and quotable by LLMs and AI agents, not just
search engines. Two pieces: an optional `llms.txt` map, and a robots policy that
reflects the owner's choice about AI crawlers.

## llms.txt (optional, experimental)

A markdown file at the site root (`SITE_URL/llms.txt`) that gives an LLM a clean
map of your site — think "sitemap for language models". Format (the community
[proposal](https://llmstxt.org/)):

**Reality check before you promise anything:** `llms.txt` is an experimental,
voluntary artifact. It only does anything for systems that choose to read it — no
major engine is committed to it, and Google has stated it **ignores `llms.txt`
entirely** (it neither helps nor hurts Search or AI visibility).
[Google AI-features / crawling guidance](https://developers.google.com/search/docs/crawling-indexing/overview-google-crawlers).
So offer it as an optional extra for AI systems that opt in to reading it — never as a
way to "become eligible" in search or AI answers.

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

## llms-full.txt (optional, ecosystem extension)

Same idea, but concatenates the actual text content of your key pages into one file
(`SITE_URL/llms-full.txt`) so a model can read the whole site in one fetch. Note this
is an ecosystem **extension**, not part of the core `llms.txt` proposal. Worth it for
small sites; skip if large.

## robots.txt — the AI-crawler policy is the OWNER's call (ask first)

This is an opt-in decision, not a default edit. Before writing any AI-crawler lines, ask
the site owner about three SEPARATE questions — they are not the same knob:

1. **Search indexing** — should classic search (Yandex, Google, Bing) crawl and index the
   site at all? (Almost always yes.)
2. **AI citation** — may AI answer engines fetch pages so the site can be *cited* in AI
   answers?
3. **AI training** — may the content be used to *train* models?

### Which token does what (get this right — the categories are easy to mix up)

These are three DIFFERENT kinds of user-agent. Allowing or blocking the wrong one silently
breaks the owner's choice:

| Token | What it is | Category |
|---|---|---|
| `OAI-SearchBot` | OpenAI — ChatGPT Search fetch | citation / search |
| `Claude-SearchBot` | Anthropic — Claude search index fetch | citation / search |
| `Claude-User` | Anthropic — fetch on a user's direct request in Claude | citation / user-directed |
| `PerplexityBot` | Perplexity — search/citation crawler | citation / search |
| `YandexAdditional` / `YandexAdditionalBot` | Yandex — content for Yandex AI answers | citation (Yandex AI answers) |
| `GPTBot` | OpenAI — may use fetched content to TRAIN models | training |
| `ClaudeBot` | Anthropic — general crawler, content may be used for TRAINING | training |
| `Google-Extended` | Training-CONTROL token for Gemini training / some grounding — does NOT fetch pages itself | training control (not a crawler) |
| `Applebot-Extended` | Training-CONTROL token for Apple AI — does NOT fetch pages itself (`Applebot` is the crawler) | training control (not a crawler) |
| `Bytespider` | ByteDance crawler — robots.txt compliance is UNCONFIRMED; do not promise it obeys | unverified |

Key consequences:

- **"Citation yes, training no"** means ALLOW `OAI-SearchBot`, `Claude-SearchBot`,
  `Claude-User`, `PerplexityBot`, `YandexAdditional`/`YandexAdditionalBot`, and DISALLOW
  the training crawlers `GPTBot` and `ClaudeBot`. Allowing `GPTBot`/`ClaudeBot` under a
  "citation" heading (as naive allowlists do) actually opts the owner INTO training.
- `Google-Extended` and `Applebot-Extended` are **training-control tokens, not
  answer-engine crawlers** — they never fetch pages. `Disallow: /` for them opts OUT of
  Gemini / Apple training without touching search indexing; they have nothing to do with
  "citation".
- `YandexAdditional`/`YandexAdditionalBot` govern **Yandex AI-answers use** — this is a
  citation-side control, NOT a training-control token.
- `Bytespider`'s robots.txt compliance is unconfirmed — do not tell the owner a `Disallow`
  reliably blocks it.

Sources: [OpenAI bots](https://developers.openai.com/api/docs/bots),
[Anthropic crawlers](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler),
[Google crawlers](https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers),
[Apple Applebot](https://support.apple.com/en-us/119829),
[Yandex AI](https://yandex.com/support/webmaster/en/yandex-ai),
[Perplexity crawlers](https://docs.perplexity.ai/docs/resources/perplexity-crawlers).

### Most-specific-group-wins (read this BEFORE adding any named-UA group)

`robots.txt` gives each crawler exactly ONE group of rules — the MOST SPECIFIC matching
`User-agent`, and ONLY that group (RFC 9309). A named group does NOT inherit the `*` group.
So if the existing file has:

```
User-agent: *
Disallow: /admin/
Disallow: /drafts/
```

and you add:

```
User-agent: GPTBot
Allow: /
```

then GPTBot now uses ITS group only — and `/admin/` and `/drafts/` become crawlable for it,
silently undoing the site's exclusions. Two safe options:

- **Preferred:** don't add redundant per-bot `Allow: /` groups at all — a crawler you never
  named already follows the `*` group, which already allows whatever `*` allows.
- If you DO create a named group, **repeat every `*` `Disallow` inside it** so the
  exclusions still apply to that bot.

Sources: [RFC 9309](https://www.rfc-editor.org/rfc/rfc9309.html),
[Google robots.txt spec — group precedence](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec).

### Examples (use only the policy the owner chose)

**A) Allow classic search + AI (owner opted into both citation and training).** No per-bot
groups needed — every unnamed crawler already follows `*`:

```
# robots.txt — allow classic search + AI (owner opted in)
User-agent: *
Allow: /

Sitemap: SITE_URL/sitemap.xml
```

**B) Citation yes, training no.** Allow the search/citation fetchers, block the training
crawlers, and set the training-control tokens to opt out of training. These are named
groups — if your `*` group carries real exclusions, repeat them inside each group per the
precedence rule above (the `*` here has none):

```
# robots.txt — cite me, don't train on me (owner opted in)
User-agent: *
Allow: /

# search / citation fetchers — allowed
User-agent: OAI-SearchBot
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: Claude-User
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: YandexAdditional
Allow: /
User-agent: YandexAdditionalBot
Allow: /

# training crawlers — blocked
User-agent: GPTBot
Disallow: /
User-agent: ClaudeBot
Disallow: /

# training-control tokens (not crawlers) — opt out of model training
User-agent: Google-Extended
Disallow: /
User-agent: Applebot-Extended
Disallow: /

Sitemap: SITE_URL/sitemap.xml
```

To BLOCK any crawler, use `Disallow: /` under its user-agent. Never allow-all silently —
write exactly the policy the owner chose.

## Why this matters

Search sends clicks; AI answers send *mentions*. Blocking the search/citation fetchers
(`OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`, `YandexAdditional`) can sharply
reduce the chance of being cited in ChatGPT / Claude / Perplexity / Yandex answers even
when you rank #1 in Google. Blocking the training crawlers (`GPTBot`, `ClaudeBot`) or
setting the training-control tokens (`Google-Extended`, `Applebot-Extended`) keeps you out
of model training. These are different levers — the owner decides each one, and you write
exactly what they chose.
