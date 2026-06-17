---
name: telegram-chip
description: Unified Telegram core (HTTP API + MCP stdio + tgdl + sales hooks) with single-session Telethon architecture. Use when setting up Telegram automation, reading/sending Telegram messages via local API, exporting chat history, or troubleshooting Telethon auth/session conflicts.
metadata: {"clawdbot": {"always": false}}
---

# telegram-chip

Unified Telegram core with a single Telethon client and optional sales hooks.

## Correct authorization procedure (important)

Use this exact order:

1. Prepare `.env` with `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`.
2. Run `./generate-session.sh` and complete interactive login:
   - phone number (`+7...`),
   - Telegram login code,
   - 2FA password (if enabled).
3. Verify `TELEGRAM_SESSION_STRING` is present in `.env`.
4. Start only one active Telethon process for this session string.

## Credential acquisition recommendations

When obtaining `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` at `my.telegram.org/apps`:
- Prefer phone mobile internet (without Wi‑Fi/VPN), **or**
- Use a clean private/incognito browser session.

This reduces auth friction and weird web-session/cache issues.

## Hard rules

- Never share `TELEGRAM_SESSION_STRING` in chats/logs.
- If session leaks, revoke/regenerate immediately.
- One session string must not be used by multiple concurrent Telethon processes (prevents `AuthKeyDuplicatedError`).
- Use HTTP API (`api.py`) as the only integration point.
- Do not use direct Telethon imports outside this skill runtime (`skills/telegram-chip/.venv`).

## Reading polls

Anonymous multi-choice polls hide per-option vote counts from non-participants. Ask the session-owner human to vote manually in Telegram first, then `GET /chats/{chat_id}/messages/{message_id}` returns `poll.results[].voters`. See `README.md` → "Reading polls" for details.

## Read receipts (read_outbox_max_id)

To check if a peer has read a message you sent: `sent_message_id <= read_outbox_max_id` ⇒ read.

- `GET /chats/list` returns `read_outbox_max_id`, `read_inbox_max_id`, `top_message_id` per chat (alongside `unread_count`).
- `GET /chats/{chat_id}/read_status` — single-peer endpoint, lighter than `/chats/list` (uses `GetPeerDialogsRequest`).

`read_outbox_max_id == top_message_id` ⇒ peer прочитал всё.

See `README.md` → "Read receipts" for details.

See `README.md` and `TROUBLESHOOTING.md` for full setup and failure recovery.
