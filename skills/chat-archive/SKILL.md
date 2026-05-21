---
name: chat-archive
description: >
  Archive messages from a Telegram business chat. Saves each message to
  daily markdown, classifies (DECISION/TASK/OPEN_QUESTION), makes daily summary,
  pushes decisions and summaries to storage.
  Use when: (1) a message is received from the monitored chat,
  (2) @mention of the monitor agent in this chat, (3) request for flush/day summary,
  (4) request for data from chat history of a partnership.
  NOT for: messages from other chats, direct user commands outside partnership context.
---

# Chat Archive

Skill for archiving business chat correspondence.

- **Chat ID:** `<your-chat-id>`
- **Workspace:** `<your-workspace>`
- **Storage CLI:** `your-storage-cli`

---

## 1. File structure

```
partnerships/<partner-name>/
├── chat-history/
│   └── YYYY-MM-DD.md          # daily log (append-only)
├── chat-summary/
│   └── YYYY-MM-DD-summary.md  # daily summary
├── documents/                   # partnership documents
└── questionnaire/               # questionnaires etc.
```

All paths are relative to the agent workspace.
Create directories on first use:
```bash
mkdir -p partnerships/<partner-name>/chat-history partnerships/<partner-name>/chat-summary
```

---

## 2. On receiving a message from the monitored chat

### 2.1 Determine date and time

Use the message timestamp. File date format: `YYYY-MM-DD`.
Time format in record: `HH:MM` (your local timezone).

### 2.2 Append to daily log

File: `partnerships/<partner-name>/chat-history/YYYY-MM-DD.md`

If file does not exist -- create with header:
```markdown
# Chat Log -- YYYY-MM-DD

```

Append each message in format:

```markdown
[HH:MM] @username: message text
```

#### Media messages

If message contains media, add tag before text:

| Type | Tag |
|-----|-----|
| Photo | `[photo]` |
| Voice | `[voice]` |
| Video | `[video]` |
| Document/file | `[document]` |
| Sticker | `[sticker]` |
| Video note | `[video_note]` |
| Audio | `[audio]` |
| Location | `[location]` |
| Contact | `[contact]` |
| Forwarded | `[forwarded]` |

Format with media:
```markdown
[HH:MM] @username: [photo] photo caption
[HH:MM] @username: [voice] (voice message)
[HH:MM] @username: [document] filename.pdf
```

If both media and text (caption) -- record both.
If no text -- record only the media tag in parentheses.

### 2.3 Message classification

Analyze text and add tag **at end of line** when matched:

#### [DECISION] -- decision/agreement
Keywords/phrases:
- agreed, decided, plan, ok let's do it, confirmed
- accepted, approved, done deal

```markdown
[14:30] @partner: ok let's do 70/30 [DECISION]
```

#### [TASK] -- a task
Keywords/phrases:
- do, need, task, to-do, deadline
- prepare, by tomorrow, by Monday
- your responsibility

```markdown
[15:10] @user: need to prepare presentation by Friday [TASK]
```

#### [OPEN_QUESTION] -- unanswered question
Criteria:
- Message contains a question mark `?`
- No direct answer in the following 2-3 messages
- Message asks a question requiring a decision (not rhetorical)

If unclear -- mark `[QUESTION]`.
At daily summary review: if still unanswered, reclassify to `[OPEN_QUESTION]`.

```markdown
[16:00] @partner: what about the legal entity, decided? [OPEN_QUESTION]
```

#### Regular message -- no tag

```markdown
[16:05] @user: hi, how are things?
```

### 2.4 Push decisions to storage

On detecting `[DECISION]` -- push immediately:

```bash
your-storage-cli push partnerships/<partner-name>/decisions << 'EOF'
{
  "date": "YYYY-MM-DD",
  "time": "HH:MM",
  "author": "@username",
  "text": "decision text",
  "chat_message_id": MESSAGE_ID
}
EOF
```

### 2.5 Push tasks to storage

On detecting `[TASK]` -- push:

```bash
your-storage-cli push partnerships/<partner-name>/tasks << 'EOF'
{
  "date": "YYYY-MM-DD",
  "time": "HH:MM",
  "author": "@username",
  "text": "task text",
  "status": "open",
  "chat_message_id": MESSAGE_ID
}
EOF
```

---

## 3. Daily Summary

Runs once per day (via cron, on flush, or on context compaction).

### 3.1 Generate summary

Read file `partnerships/<partner-name>/chat-history/YYYY-MM-DD.md`.
Create file: `partnerships/<partner-name>/chat-summary/YYYY-MM-DD-summary.md`

Format:
```markdown
# Summary -- YYYY-MM-DD

## Stats
- Total messages: N
- Participants: @user1 (X messages), @user2 (Y messages)

## Key topics
- Topic 1: brief description
- Topic 2: brief description

## Decisions [DECISION]
1. "decision text" -- @author, HH:MM
2. ...

(If no decisions: "No decisions recorded for the day.")

## Tasks [TASK]
1. "task text" -- @author, HH:MM, status: open
2. ...

(If no tasks: "No tasks recorded for the day.")

## Open questions [OPEN_QUESTION]
1. "question text" -- @author, HH:MM
2. ...

(If no questions: "All questions for the day received answers.")

## Context
Brief description of the overall tone and flow of conversation (2-3 sentences).
```

### 3.2 Push summary to storage

```bash
your-storage-cli push partnerships/<partner-name>/chat-summaries << 'EOF'
{
  "date": "YYYY-MM-DD",
  "total_messages": N,
  "decisions_count": N,
  "tasks_count": N,
  "open_questions_count": N,
  "topics": ["topic1", "topic2"],
  "decisions": ["text1", "text2"],
  "tasks": ["text1", "text2"],
  "open_questions": ["text1"],
  "summary_file": "partnerships/<partner-name>/chat-summary/YYYY-MM-DD-summary.md"
}
EOF
```

---

## 4. On @mention of the monitor agent in the chat

When the monitor agent is mentioned in the monitored chat:

1. **Read context** -- last 20-30 messages from current chat-history
2. **Identify question/request** from the mention message
3. **Pull data** as needed:
   - Chat history: `partnerships/<partner-name>/chat-history/`
   - Summaries: `partnerships/<partner-name>/chat-summary/`
   - Documents: `partnerships/<partner-name>/documents/`
   - Stored decisions: `your-storage-cli get partnerships/<partner-name>/decisions`
   - Stored tasks: `your-storage-cli get partnerships/<partner-name>/tasks`
4. **Reply in chat** -- briefly, to the point, citing sources

Example responses:
- "What did we agree on regarding X?" → find in decisions, quote
- "What tasks are open?" → collect from tasks with status open
- "What did we discuss last week?" → collect summaries for period

---

## 5. Rules

1. **Append-only.** Never delete or overwrite chat-history. Only append.
2. **Do not reply** to regular messages. Only archive silently.
3. **Reply only on @mention.**
4. **Do not reveal** technical information (paths, storage internals) in chat -- internal mechanics only.
5. **Timezone:** all timestamps in your local timezone.
6. **Encoding:** UTF-8.
7. **Privacy:** do not forward or display chat contents outside the context of tasks.

---

## 6. Environment check (first run)

```bash
# Check storage CLI
your-storage-cli get partnerships/<partner-name>

# Create directory structure
mkdir -p partnerships/<partner-name>/chat-history
mkdir -p partnerships/<partner-name>/chat-summary
mkdir -p partnerships/<partner-name>/documents

# Check storage credentials
ls -la ~/.secrets/storage/credentials.json
```

---

## 7. Fallbacks

| Situation | Action |
|----------|----------|
| Storage unavailable | Write to file, mark `[storage-pending]`. Push when restored |
| No chat-history file for today | Create with header `# Chat Log -- YYYY-MM-DD` |
| Cannot determine message type | Record as regular (no tag) |
| Message in English | Archive as-is, classification works in both languages |
| Edited message | Append line: `[HH:MM] @username: [edited] new text` |
| Deleted message | Ignore (do not record deletion) |

---

## 8. Voice messages (voice/audio)

On receiving a voice message from the monitored chat:

1. Extract the .ogg file path from `[media attached: /path/to/file.ogg ...]`
2. Transcribe via Groq Whisper:
```bash
bash ~/.claude/skills/groq-voice/transcribe.sh "/path/to/file.ogg"
```
3. Write to chat-history with [voice] tag AND transcription:
```markdown
[HH:MM] @username: [voice] «transcription of voice message»
```
4. Classify transcribed text by normal rules ([DECISION], [TASK], [OPEN_QUESTION])

If transcription failed -- write:
```markdown
[HH:MM] @username: [voice] (could not transcribe)
```
