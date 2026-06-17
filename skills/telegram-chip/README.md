# telegram-chip

Single-client Telegram integration built on Telethon.

## What it provides

- HTTP API (FastAPI, default `:8080`)
- Optional MCP stdio server
- Optional sales webhook hooks
- Chat export (`tgdl`-style JSON)

## Architecture

One Telethon client is the source of truth. All operations should go through that single process.

## Configuration

Use `.env` in this folder.

Required:

```env
TELEGRAM_API_ID=...
TELEGRAM_API_HASH=...
TELEGRAM_SESSION_STRING=...
```

Optional:

```env
TELEGRAM_SESSION_NAME=telegram_session
SALES_WEBHOOK_URL=http://localhost:18789/api/cron/wake
SALES_MONITORED_USERS=12345,67890
```

## Recommended authorization flow (important)

1. Obtain `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` at `https://my.telegram.org/apps`.
   - Prefer mobile internet without Wi‑Fi/VPN, or use a fresh private/incognito browser session.
2. Put API credentials into `.env`.
3. Run:

```bash
./generate-session.sh
```

4. Complete prompts:
   - phone number (`+...`),
   - login code from Telegram,
   - 2FA password (if enabled).
5. Verify session string:

```bash
grep '^TELEGRAM_SESSION_STRING=' .env
```

## Security rules

- Treat `TELEGRAM_SESSION_STRING` like a password.
- Never send it in chats/issues/logs.
- If leaked, revoke/regenerate immediately.
- Do not run multiple Telethon processes with the same session string.
- Keep Telethon isolated to `skills/telegram-chip-ws/.venv` and access Telegram from other code only via HTTP API.

## Run API

```bash
.venv/bin/python api.py
```

Health check:

```bash
curl http://127.0.0.1:8080/health
```

## Main endpoints

- `GET /health`
- `GET /chats/list?limit=50&chat_type=user|group|channel&unread_only=false` — chat metadata. Each item includes `unread_count`, `is_pinned`, `read_outbox_max_id`, `read_inbox_max_id`, `top_message_id`.
- `GET /chats/{chat_id}/read_status` — read receipts for one chat: `{read_outbox_max_id, read_inbox_max_id, top_message_id, unread_count}`. Lighter than `/chats/list` (single peer via `GetPeerDialogsRequest`).
- `GET /chats/{chat_id}/messages?limit=50`
- `GET /chats/{chat_id}/messages/{message_id}` — single message; if `media_type=MessageMediaPoll`, response includes `poll{ question, answers, results, total_voters, multiple_choice, public_voters, closed }`
- `POST /messages/send`
- `POST /messages/edit`
- `POST /messages/delete`
- `POST /tgdl/export?chat_id=<id>&limit=500`

## Read receipts

To check whether a peer has read a message you sent:

```
sent_message_id <= read_outbox_max_id  ⇒  peer прочитал
```

`read_outbox_max_id` is the id of the latest **outgoing** message the peer has acknowledged as read. `read_inbox_max_id` is the symmetric value for **incoming** messages you've read. `top_message_id` is the id of the latest message in the chat — handy for "has peer read everything I sent" comparisons (`read_outbox_max_id == top_message_id` ⇒ all read).

Example:

```bash
curl http://127.0.0.1:8080/chats/123456789/read_status
# {"chat_id": 123456789, "read_outbox_max_id": 65367, "read_inbox_max_id": 65279, "top_message_id": 65367, "unread_count": 0}
```

## Reading polls (important caveat)

For **anonymous multi-choice polls** (`public_voters: false` AND `multiple_choice: true`) Telegram returns per-option vote counts ONLY to accounts that have already voted in that poll. The session user account behind this skill must vote first — otherwise `results[]` is empty and only `total_voters` is visible.

There is no `vote` endpoint in this API by design (one session = one user account; programmatic votes pollute the data). Correct flow:

1. The session-owner human votes in the poll manually from Telegram (mobile/desktop client).
2. Then call `GET /chats/{chat_id}/messages/{message_id}` — `poll.results` will contain `voters` per option.

For single-choice or non-anonymous polls (`public_voters: true`) results are visible without voting.

## MCP stdio (optional)

Use `main.py` only when MCP tool integration is needed. If HTTP API is enough, keep MCP disabled.

## Troubleshooting quick hits

- `AuthKeyDuplicatedError` → stop all parallel clients, generate new session string.
- API not starting → check `.env`, port 8080 conflict, stale lock file.
- Auth problems on my.telegram.org → retry via mobile internet or private/incognito session.
