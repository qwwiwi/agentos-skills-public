# 06 — Fetch lesson content from your data source

Lesson content (timecodes, titles, descriptions) can come from any data source — a database, markdown files, JSON, or a spreadsheet. This file shows the schema and how to fetch it.

## Schema (example using Supabase)

```sql
CREATE TABLE lessons (
  id            uuid PRIMARY KEY,
  lesson_number int NOT NULL UNIQUE,
  title         text NOT NULL,
  duration_minutes int,
  summary       text,
  timecodes     jsonb,         -- [{time, label, description}, ...]
  status        text,          -- draft / ready / published
  created_at    timestamptz,
  updated_at    timestamptz
);
```

## Fetching via Supabase Management API

```bash
export SUPABASE_PROJECT_REF="<your-project-ref>"
export SUPABASE_ACCESS_TOKEN="<your-access-token>"
export SUPABASE_MGMT_API="https://api.supabase.com"

LESSON_NUM=5
curl -sS "$SUPABASE_MGMT_API/v1/projects/$SUPABASE_PROJECT_REF/database/query" \
  -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"SELECT lesson_number, title, duration_minutes, summary, timecodes FROM lessons WHERE lesson_number=$LESSON_NUM\"}" \
  | jq .
```

## timecodes structure

```json
[
  {
    "time": "00:00",
    "label": "Step 1 title",
    "description": "Step 1 full description for the lesson."
  },
  {
    "time": "04:00",
    "label": "Step 2 title",
    "description": "Step 2 description..."
  }
]
```

Each timecode → one step-frame:
- `time` → calculate step duration (difference between adjacent `time` values)
- `label` → step title
- `description` → lead-line or split into sections

## Calculate step durations

```python
import re

def parse_time(t):
    m = re.match(r'(\d+):(\d+)', t)
    return int(m[1]) * 60 + int(m[2])

timecodes = [...]
total = lesson['duration_minutes']

durations = []
for i, tc in enumerate(timecodes):
    start = parse_time(tc['time'])
    end = parse_time(timecodes[i+1]['time']) if i+1 < len(timecodes) else total*60
    durations.append((end - start) // 60)

# Use durations in eyebrow: "STEP N · K MIN"
```

## Adapting descriptions for slides

Descriptions are often too long for slides. Trim:
- **Lead-line** (subtitle frame): first sentence, <=80 characters
- **Section bullets**: split at sentence/idea boundaries, <=40 chars each

If description does not fit well — work with the content owner for an alternative.

## When content is not in the database yet

1. Ask the content owner "Where is lesson N content? Nothing in the DB yet."
2. If they provide content on the fly — write to a Markdown file, add to DB later
3. Do not invent content — factual accuracy is critical for educational products
