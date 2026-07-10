# JSON-LD recipes (AEO)

Structured data tells search + AI engines exactly what a page is, so it can be
quoted in answers and (where the engine still supports it) rich results. Put each
block in its own `<script type="application/ld+json">` in `<head>`. Replace
`SITE_URL`, `BRAND`, and the content fields with the page's REAL values — every
field must match what's visible on the page.

**What still earns a Google rich result has narrowed.** Google removed the HowTo
rich result in 2023 and stopped showing FAQ rich results for almost all sites (fully
retired ~2026-05-07, docs removed June 2026). Those blocks are still worth adding for
**AEO / AI answer engines** (and Yandex, with the caveats below) — just don't promise
a Google rich snippet from them. [Google search updates / changelog](https://developers.google.com/search/updates).

## Article / BlogPosting (any article page)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Exact page title (≤110 chars)",
  "description": "One-sentence summary, same as the meta description.",
  "image": "SITE_URL/path/to/cover.jpg",
  "datePublished": "2026-07-05",
  "dateModified": "2026-07-05",
  "author": { "@type": "Person", "name": "Author Name" },
  "publisher": {
    "@type": "Organization",
    "name": "BRAND",
    "logo": { "@type": "ImageObject", "url": "SITE_URL/logo.png" }
  },
  "mainEntityOfPage": { "@type": "WebPage", "@id": "SITE_URL/path/" }
}
</script>
```

`TechArticle` is valid schema.org and fine for AI engines, but Google's Article rich
result only documents `Article`, `NewsArticle` and `BlogPosting` — so for a Google
Article appearance prefer `BlogPosting` (or `Article`) over `TechArticle`.
[Google Article structured data](https://developers.google.com/search/docs/appearance/structured-data/article).

## FAQPage (a page with question→answer pairs)

**AEO / AI engines only — no Google rich result.** Google retired FAQ rich results for
almost all sites (~2026-05-07). This block is still useful because AI answer engines
read it, but it will not produce a Google FAQ snippet. For a Yandex Q&A rich snippet,
Yandex documents [`QAPage`](https://yandex.com/support/webmaster/en/supported-schemas/q-and-a),
not `FAQPage` — use `QAPage` if Yandex Q&A appearance is the goal.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "The question, exactly as a person would ask it",
      "acceptedAnswer": { "@type": "Answer", "text": "A direct, complete answer in 1–3 sentences." }
    },
    {
      "@type": "Question",
      "name": "Second question",
      "acceptedAnswer": { "@type": "Answer", "text": "Second answer." }
    }
  ]
}
</script>
```

Only mark up FAQs that are actually on the page.

## HowTo (step-by-step page)

**AEO / AI engines only — no Google rich result.** Google removed the HowTo rich
result in 2023; this block no longer produces a Google appearance. Keep it only for AI
answer engines, and only when the steps are truly on the page.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "How to do X",
  "step": [
    { "@type": "HowToStep", "name": "Step 1", "text": "What to do first." },
    { "@type": "HowToStep", "name": "Step 2", "text": "What to do next." }
  ]
}
</script>
```

## BreadcrumbList (navigation context)

Valid for Google's breadcrumb rich result. Note: Yandex does not support breadcrumb
navigation-chain markup, so the Yandex structured-data validator may flag errors on a
`BreadcrumbList` that is perfectly valid for Google — that is expected, not a bug in your
markup. [Yandex markup limitations](https://yandex.com/support/webmaster/en/search-results/site-description).

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "Home", "item": "SITE_URL/" },
    { "@type": "ListItem", "position": 2, "name": "Blog", "item": "SITE_URL/blog/" },
    { "@type": "ListItem", "position": 3, "name": "This article", "item": "SITE_URL/blog/this/" }
  ]
}
</script>
```

## Site subject + WebSite (home page only, site-level identity)

Pick the **most specific TRUE type** for what the site actually is — `Organization` is
NOT right for every site. Use `Person` for a personal site or portfolio, `LocalBusiness`
(or a specific subtype like `Restaurant`) for a business with a physical location,
`OnlineStore` for a shop. Google recommends the most specific truthful type.
[Google Organization structured data](https://developers.google.com/search/docs/appearance/structured-data/organization).

The recipe below shows `Organization`; swap `@type` (and the type-specific fields) for the
truthful subject:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "BRAND",
  "url": "SITE_URL",
  "logo": "SITE_URL/logo.png",
  "sameAs": ["https://t.me/yourchannel", "https://x.com/yourhandle"]
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "BRAND",
  "url": "SITE_URL"
}
</script>
```

For a personal site, the subject would instead be, e.g.:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Author Name",
  "url": "SITE_URL",
  "sameAs": ["https://t.me/yourchannel", "https://x.com/yourhandle"]
}
</script>
```

## Validate

- Google Rich Results Test: https://search.google.com/test/rich-results
- Schema.org validator: https://validator.schema.org
- Yandex structured-data validator: in Yandex Webmaster.

Fix every error before shipping — malformed JSON-LD is simply ignored, not partially
credited. Misleading-but-valid markup can cost you rich-result eligibility or (if it
misrepresents the page) trigger a structured-data manual action, but Google states that
does not change your normal web ranking; Yandex likewise ignores markup it can't trust
rather than treating it as a ranking factor. Mark up honestly for eligibility — there is
no "ranking penalty" to fear from a bad block, only lost eligibility.
[Google structured-data policies](https://developers.google.com/search/docs/appearance/structured-data/sd-policies),
[Yandex semantic-markup FAQ](https://yandex.com/support/webmaster/en/schema-org/semantic-faq).
