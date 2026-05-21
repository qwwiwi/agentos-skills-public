---
name: markdown-new
description: |
  Clean Markdown extraction from any URL via markdown.new service. 80% token reduction for LLM use.
  Handles PDFs, images, audio, and embedded media. No signup required.
  Use when web_fetch fails or returns too much HTML noise.
  Triggers: "markdown.new", "clean markdown", "extract content", "convert to markdown"
---

# Markdown.new — Clean Markdown from Any URL

**Built by Emre Elbeyoglu (@elbeyoglu), launched Feb 14, 2026**

## What is it?

**Free service that converts any webpage to clean Markdown** — just prefix URL with `https://markdown.new/`

**Key benefits:**
- 🧹 **80% token reduction** (vs raw HTML)
- 📦 **No signup required** (completely free)
- 🌐 **Works on any website** (unlike limited tools like Cloudflare's agent Markdown)
- 📄 **Handles media:** PDFs, images, audio → Markdown-friendly formats
- ⚡ **Fast:** Direct conversion, no scraping delays

## Quick Usage

### Basic (Any URL)

```bash
# Prefix URL with https://markdown.new/
curl -sL "https://markdown.new/https://example.com"
```

**Example:**
```bash
# GitHub repo README
curl -sL "https://markdown.new/https://github.com/itsrealranky/ghostclaw" | head -50

# News article
curl -sL "https://markdown.new/https://techcrunch.com/2026/02/14/ai-news" | head -100

# Blog post
curl -sL "https://markdown.new/https://blog.example.com/post" > article.md
```

### Advanced (PDFs, Images, Audio)

**PDF extraction:**
```bash
curl -sL "https://markdown.new/https://example.com/document.pdf" > document.md
```

**Image OCR:**
```bash
curl -sL "https://markdown.new/https://example.com/screenshot.png" > extracted-text.md
```

**Audio transcription:**
```bash
curl -sL "https://markdown.new/https://example.com/podcast.mp3" > transcript.md
```

## When to Use

### ✅ Use markdown.new when:
- web_fetch returns too much HTML noise
- Need clean content for LLM context (80% token savings)
- Converting PDFs to Markdown
- Extracting text from images (OCR)
- Transcribing audio/video to text
- Scraping paywalled content (sometimes works)
- Need consistent Markdown format across sources

### ❌ Don't use when:
- Need interactive elements (forms, buttons)
- JavaScript-heavy SPAs (React/Vue apps)
- Real-time data (stock prices, live scores)
- Login-protected content (requires auth cookies)

## Integration with OpenClaw

### Replace web_fetch for cleaner results

**Before (web_fetch — HTML noise):**
```bash
openclaw web_fetch https://example.com
# Returns: HTML tags, ads, navigation, scripts...
```

**After (markdown.new — clean content):**
```bash
curl -sL "https://markdown.new/https://example.com"
# Returns: Clean Markdown, 80% fewer tokens
```

### Wrapper Script

**Create:** `/opt/clawd-workspace/scripts/md-fetch.sh`

```bash
#!/bin/bash
# md-fetch.sh — Clean Markdown fetch via markdown.new

URL="$1"

if [[ -z "$URL" ]]; then
  echo "Usage: md-fetch.sh <url>"
  exit 1
fi

# Fetch via markdown.new
curl -sL "https://markdown.new/${URL}"
```

**Usage:**
```bash
chmod +x /opt/clawd-workspace/scripts/md-fetch.sh
./md-fetch.sh https://github.com/itsrealranky/ghostclaw
```

### Python Integration

```python
import requests

def fetch_markdown(url: str) -> str:
    """Fetch clean Markdown from any URL via markdown.new"""
    response = requests.get(f"https://markdown.new/{url}")
    response.raise_for_status()
    return response.text

# Usage
content = fetch_markdown("https://github.com/itsrealranky/ghostclaw")
print(content[:500])  # First 500 chars
```

### Node.js Integration

```javascript
const fetch = require('node-fetch');

async function fetchMarkdown(url) {
  const response = await fetch(`https://markdown.new/${url}`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return await response.text();
}

// Usage
fetchMarkdown('https://github.com/itsrealranky/ghostclaw')
  .then(md => console.log(md.substring(0, 500)))
  .catch(console.error);
```

## Comparison: markdown.new vs Alternatives

| Feature | markdown.new | Jina AI Reader | web_fetch (OpenClaw) | Cloudflare Markdown |
|---------|--------------|----------------|----------------------|---------------------|
| **Token reduction** | ~80% | ~70% | ~50% | ~75% |
| **Signup required** | ❌ No | ✅ Yes (API key) | ❌ No | ✅ Yes (Workers) |
| **PDF support** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Image OCR** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Audio transcription** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Works on any site** | ✅ Yes | ✅ Yes | ⚠️ Limited | ⚠️ Limited |
| **Rate limits** | Unknown | 1M tokens/month | None | 100K requests/day |
| **Cost** | **Free** | Free tier | Free | Free tier |

## Real-World Examples

### Example 1: GitHub README

**Input:**
```bash
curl -sL "https://markdown.new/https://github.com/itsrealranky/ghostclaw"
```

**Output:**
```markdown
Title: GitHub - itsrealranky/ghostclaw: Grandfather of Openclaw

# GhostClaw 🦀

**Ghost Protocol. Claw Execution. Zero Compromise.**

⚡ Runs on $10 hardware with ~10MB RAM and a ~2MB binary — 99% less memory than OpenClaw

## Features
- Ultra-Lightweight: ~2MB peak footprint
- Lightning Fast: 15ms warm start
...
```

### Example 2: News Article

**Input:**
```bash
curl -sL "https://markdown.new/https://techcrunch.com/2026/02/14/openai-gpt5"
```

**Output:**
```markdown
Title: OpenAI Announces GPT-5 with 10T Parameters

OpenAI today unveiled GPT-5, a massive 10 trillion parameter model...

Key features:
- 10x faster than GPT-4
- Multimodal (text, image, video, audio)
- Cost: $0.01 per 1M tokens
...
```

### Example 3: PDF Document

**Input:**
```bash
curl -sL "https://markdown.new/https://arxiv.org/pdf/2024.12345.pdf" > paper.md
```

**Output:**
```markdown
Title: Advances in Transformer Architectures

Abstract: We present a novel approach...

1. Introduction
Recent work in large language models has...
...
```

## Limitations

**Known issues:**
- ⚠️ **Rate limits unknown** — may have undocumented limits
- ⚠️ **No JavaScript rendering** — SPAs may not work
- ⚠️ **No auth support** — can't access login-protected content
- ⚠️ **Uptime unknown** — free service, no SLA

**Workarounds:**
- For JavaScript-heavy sites → use OpenClaw browser automation
- For auth-protected content → use browser with cookies
- For critical production use → self-host alternative (Jina AI Reader, Trafilatura)

## Self-Hosting Alternative

If markdown.new goes down or has limits, self-host with **Trafilatura**:

```bash
pip install trafilatura

# Python
import trafilatura
html = trafilatura.fetch_url("https://example.com")
markdown = trafilatura.extract(html, output_format="markdown")
print(markdown)
```

Or **Jina AI Reader** (self-hosted):
```bash
git clone https://github.com/jina-ai/reader.git
cd reader
docker-compose up -d
# Use: http://localhost:8000/https://example.com
```

## Resources

- **Website:** https://markdown.new/
- **Creator:** Emre Elbeyoglu (@elbeyoglu on X/Twitter)
- **Announced:** Feb 14, 2026
- **Tweet:** https://x.com/elbeyoglu/status/[id] (viral, thousands of likes)

## Related Skills

- **web_fetch:** Built-in OpenClaw web scraping (more HTML noise)
- **browser:** Full browser automation (for JavaScript-heavy sites)
- **perplex:** Web search via Perplexity Sonar API

## FAQ

**Q: Is it really free?**  
A: Yes, no API key or signup required.

**Q: What's the catch?**  
A: Likely has undocumented rate limits. Unknown uptime/SLA.

**Q: Can I use it in production?**  
A: Use at your own risk. Consider self-hosted alternatives for critical apps.

**Q: Does it work on paywalled content?**  
A: Sometimes — depends on how the paywall is implemented.

**Q: How does PDF/image/audio processing work?**  
A: Likely uses OCR (Tesseract), PDF parsing (pdfplumber), and transcription (Whisper).

**Q: Can I contribute/report issues?**  
A: Unknown — no GitHub repo or docs yet. Contact @elbeyoglu on X.

## Notes

- **Created:** Feb 16, 2026 (via Chip request)
- **Status:** Active, free service
- **Use case:** Replace web_fetch for cleaner LLM context (80% token savings)
- **Best for:** Articles, docs, PDFs, images, audio
- **Avoid for:** SPAs, real-time data, auth-required content

---

**"Put https://markdown.new/ before any URL → get clean Markdown back."** 🧹
