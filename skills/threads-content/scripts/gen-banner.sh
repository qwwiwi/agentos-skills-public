#!/usr/bin/env bash
set -euo pipefail

# gen-banner.sh — generate banner for Threads thread via OpenAI gpt-image-1
#
# Usage:
#   ./gen-banner.sh --template negative --prompt "Obsidian + Claude → fail = red X" --output /tmp/banner.png
#   ./gen-banner.sh --template positive --prompt "Cognee + MCP = brain glow" --size 1024x1024
#
# Templates: negative | positive | transformation | equation
# Sizes:     1024x1024 (1:1) | 1792x1024 (16:9) | 1024x1792 (9:16)

TEMPLATE=""
USER_PROMPT=""
OUTPUT="/tmp/threads-banner-$(date +%s).png"
SIZE="1792x1024"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --template) TEMPLATE="$2"; shift 2 ;;
    --prompt)   USER_PROMPT="$2"; shift 2 ;;
    --output)   OUTPUT="$2"; shift 2 ;;
    --size)     SIZE="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 --template <negative|positive|transformation|equation> --prompt \"...\" [--output path] [--size 1792x1024]"
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$TEMPLATE" || -z "$USER_PROMPT" ]]; then
  echo "Error: --template and --prompt required" >&2
  exit 1
fi

# OpenAI API key — set via environment variable or key file
if [[ -n "${OPENAI_API_KEY:-}" ]]; then
  API_KEY="$OPENAI_API_KEY"
elif [[ -f "$HOME/.secrets/openai.key" ]]; then
  API_KEY=$(cat "$HOME/.secrets/openai.key")
else
  echo "Error: OpenAI key not found. Set OPENAI_API_KEY or create ~/.secrets/openai.key" >&2
  exit 1
fi

BASE_STYLE="Style: 3D rendered tech meme banner, black background (#0A0A0A), glossy app-icon style elements with subtle shadows and reflections, rounded squares for app icons (iOS-style 80px radius), clean white sans-serif operators (+, →, =) in Inter Bold, balanced horizontal composition, no people, no faces, no text except operators."

case "$TEMPLATE" in
  negative)
    FULL_PROMPT="${USER_PROMPT}. Equation layout: [icon A] + [icon B] → [broken result with red drooping graph or sad scribble] = [large red X mark]. ${BASE_STYLE}"
    ;;
  positive)
    FULL_PROMPT="${USER_PROMPT}. Equation layout: [icon A] + [icon B] = [winning result with golden glow #C2A878, rising graph or trophy]. ${BASE_STYLE}"
    ;;
  transformation)
    FULL_PROMPT="${USER_PROMPT}. Split layout: left half [old chaotic state in grey], center [white arrow →], right half [new clean state with golden accent #C2A878]. ${BASE_STYLE}"
    ;;
  equation)
    FULL_PROMPT="${USER_PROMPT}. Layout: [icon 1] + [icon 2] + [icon 3] = [result icon, larger, glowing golden #C2A878]. ${BASE_STYLE}"
    ;;
  *)
    echo "Unknown template: $TEMPLATE (use: negative|positive|transformation|equation)" >&2
    exit 1
    ;;
esac

echo "→ Template: $TEMPLATE"
echo "→ Size:     $SIZE"
echo "→ Output:   $OUTPUT"
echo "→ Prompt:   $FULL_PROMPT"
echo ""

RESPONSE=$(curl -sS -X POST "https://api.openai.com/v1/images/generations" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg p "$FULL_PROMPT" --arg s "$SIZE" \
    '{model:"gpt-image-1", prompt:$p, n:1, size:$s, quality:"high"}')")

if echo "$RESPONSE" | jq -e '.error' >/dev/null 2>&1; then
  ERROR=$(echo "$RESPONSE" | jq -r '.error.message')
  echo "OpenAI error: $ERROR" >&2
  echo ""
  echo "Fallback options:" >&2
  echo "  1. Generate manually in ChatGPT Plus with prompt above" >&2
  echo "  2. Top up OpenAI billing (\$10 = ~50 banners)" >&2
  echo "  3. Use Higgsfield or another image generation service" >&2
  exit 1
fi

B64=$(echo "$RESPONSE" | jq -r '.data[0].b64_json')
echo "$B64" | base64 -d > "$OUTPUT"

echo "Done. Banner saved: $OUTPUT"
ls -lh "$OUTPUT"
