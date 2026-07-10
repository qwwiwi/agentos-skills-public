# JSON-LD recipes (AEO)

Structured data tells search + AI engines exactly what a page is, so it can be
quoted in answers and rich results. Put each block in its own
`<script type="application/ld+json">` in `<head>`. Replace `SITE_URL`, `BRAND`,
and the content fields with the page's REAL values — every field must match what's
visible on the page.

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

Use `TechArticle` instead of `BlogPosting` for technical guides/tutorials.

## FAQPage (a page with question→answer pairs)

The single strongest AEO block — AI engines lift these straight into answers.

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

## Organization + WebSite (home page only, site-level identity)

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

## Validate

- Google Rich Results Test: https://search.google.com/test/rich-results
- Schema.org validator: https://validator.schema.org
- Yandex structured-data validator: in Yandex Webmaster.

Fix every error before shipping — invalid JSON-LD is ignored (or penalized), not
partially credited.
