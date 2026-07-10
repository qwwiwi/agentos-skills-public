# seo-tune — a Claude Code skill

Audit and tune ANY existing site (static HTML, Astro, Next.js, ...) for three
layers at once: **SEO** (Yandex & Google), **AEO** (AI answer engines), **GEO**
(LLM / agent discovery). Your agent checks robots.txt, sitemap.xml, canonical,
meta/OG tags, JSON-LD, llms.txt and IndexNow — then generates whatever's missing,
using YOUR domain and keys.

It tunes a site that already exists; it doesn't build one from scratch.

## Install

One command (recommended):

```bash
npx skills add github.com/qwwiwi/agentos-skills-public --skill seo-tune
```

Add `-g` to install it globally for every project.

**Fallback — manual:** download the skill folder (or the release ZIP) and unzip it
into your Claude Code skills folder:

```
~/.claude/skills/seo-tune/
```

Then say: **"tune my site for SEO with the seo-tune skill"**, and point it at your
built HTML folder or your live URL.

## What's inside

- `SKILL.md` — the audit → generate workflow.
- `references/jsonld-recipes.md` — copy-paste JSON-LD (Article, FAQ, HowTo, ...).
- `references/llms-txt.md` — llms.txt + the AI-crawler allowlist (GEO).
- `references/indexnow.md` — IndexNow (fast indexing on Yandex & Bing).

MIT.
