#!/usr/bin/env python3
"""Minimal Loore REST client (stdlib only).

Loore (https://docs.loore.ai) is the Instagram data source of this skill.
Every operation is `POST https://mcp.loore.ai/v1/<method>` with a JSON body and
`Authorization: Bearer $LOORE_API_KEY`; the answer is an envelope
`{"status": "ok", "result": {...}}` or `{"status": "error", "error": ..., "details": ...}`.

Paid calls need the user's spend approval. Create a flow budget once
(the user names the total cap in credits) and export its id:

    python3 loore.py approve --flow reels-analytics-for-brokers --cap 300
    export LOORE_SPEND_AUTHORIZATION_ID=<printed id>

Without it, a paid call answers 428 needs_user_confirmation and the script stops.
The key is read from the environment only and never printed.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from typing import Any

BASE_URL = os.environ.get("LOORE_API_BASE", "https://mcp.loore.ai").rstrip("/")
TIMEOUT = 120
MAX_RETRIES = 3

log = logging.getLogger("loore")


class LooreError(RuntimeError):
    """A refused Loore call: HTTP status, the envelope's error code and details."""

    def __init__(self, http_status: int, error: str, details: dict[str, Any] | None = None) -> None:
        self.http_status = http_status
        self.error = error
        self.details = details or {}
        super().__init__(f"Loore {http_status} {error}")

    @property
    def fatal(self) -> bool:
        """401/402/403/428/502 cannot be fixed by retrying — stop and tell the human."""
        return self.http_status in (401, 402, 403, 428, 502)

    def hint(self) -> str:
        """One-line Russian explanation for the person running the script."""
        if self.http_status == 401:
            return "ключ Loore не принят – проверьте LOORE_API_KEY (app.loore.ai → Настройки → API и MCP)"
        if self.http_status == 402:
            return "закончились кредиты или квота тарифа Loore – пополните баланс"
        if self.http_status == 403:
            return "ключ не имеет прав на этот метод или аккаунт приватный"
        if self.http_status == 428:
            cap = self.details.get("suggestedFlowCapCredits")
            extra = f" (Loore предлагает лимит {cap} кредитов)" if cap is not None else ""
            return (
                "нужно одобрение расхода" + extra + ": python3 scripts/loore.py approve --flow <имя> --cap <кредиты>, "
                "затем export LOORE_SPEND_AUTHORIZATION_ID=<id>"
            )
        if self.http_status == 429:
            return "исчерпан бюджет запросов Loore – повторите позже"
        return f"ошибка Loore: {self.error}"


def api_key() -> str:
    """Read the Loore key from $LOORE_API_KEY; exit 3 when it is missing."""
    key = os.environ.get("LOORE_API_KEY", "").strip()
    if not key:
        print(
            "LOORE_API_KEY не задан – создайте ключ в https://app.loore.ai → Настройки → API и MCP "
            "(документация: https://docs.loore.ai)",
            file=sys.stderr,
        )
        raise SystemExit(3)
    return key


def _post(method: str, body: dict[str, Any], key: str) -> tuple[int, dict[str, Any], dict[str, str]]:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/v1/{method}",
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "agentos-skills/loore-client",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8", errors="replace")), dict(resp.headers)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            env = json.loads(raw)
        except json.JSONDecodeError:
            env = {"status": "error", "error": raw[:200] or e.reason}
        return e.code, env if isinstance(env, dict) else {"error": str(env)}, dict(e.headers or {})


def call(method: str, body: dict[str, Any] | None = None, *, key: str | None = None, paid: bool = True) -> dict[str, Any]:
    """Call one Loore operation and return its `result`.

    Args:
        method: REST method name, e.g. "ig-profile" (MCP tool ig_profile).
        body: JSON arguments exactly as in the OpenAPI contract.
        key: API key; read from the environment when omitted.
        paid: attach $LOORE_SPEND_AUTHORIZATION_ID (only paid operations accept it).

    Returns:
        The envelope's `result` object.

    Raises:
        LooreError: the call was refused; `.fatal` says whether retrying is pointless.
    """
    key = key or api_key()
    payload = dict(body or {})
    spend_id = os.environ.get("LOORE_SPEND_AUTHORIZATION_ID", "").strip()
    if paid and spend_id and "spend_authorization_id" not in payload:
        payload["spend_authorization_id"] = spend_id

    for attempt in range(MAX_RETRIES + 1):
        status, env, headers = _post(method, payload, key)
        if status == 200 and env.get("status") == "ok":
            result = env.get("result")
            return result if isinstance(result, dict) else {"value": result}
        err = LooreError(status, str(env.get("error", "unknown")), env.get("details") if isinstance(env.get("details"), dict) else None)
        retriable = status in (429, 503) or (status == 500 and attempt == 0)
        if not retriable or attempt == MAX_RETRIES:
            raise err
        wait = err.details.get("retry_after_seconds") or headers.get("Retry-After") or 2 ** (attempt + 1)
        try:
            wait_s = min(float(wait), 120.0)
        except (TypeError, ValueError):
            wait_s = 2.0 ** (attempt + 1)
        log.warning("%s: %s, retry in %.0fs", method, err, wait_s)
        time.sleep(wait_s)
    raise RuntimeError("unreachable")


def paginate(method: str, body: dict[str, Any], *, key: str | None = None, max_pages: int = 10) -> Iterator[dict[str, Any]]:
    """Yield rows of a cursor-paginated read (items / hasMore / nextCursor)."""
    cursor: str | None = None
    for _ in range(max_pages):
        page_body = dict(body)
        if cursor:
            page_body["cursor"] = cursor
        result = call(method, page_body, key=key)
        yield from result.get("items") or []
        cursor = result.get("nextCursor")
        if not result.get("hasMore") or not cursor:
            return


def approve(flow_id: str, cap_credits: float) -> str:
    """Create a 24h flow budget the user approved; returns spend_authorization_id."""
    result = call(
        "spend-authorization",
        {"action": "create", "flow_id": flow_id, "approved_cap_credits": cap_credits, "user_approved": True},
        paid=False,
    )
    sid = result.get("spend_authorization_id") or result.get("id")
    if not sid:
        raise LooreError(200, "spend_authorization_id missing in answer")
    return str(sid)


def main() -> int:
    p = argparse.ArgumentParser(description="Loore helper: create a spend budget approved by the user.")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("approve", help="create a flow budget (run only after the user approved the cap)")
    a.add_argument("--flow", required=True, help="workflow name, e.g. reel-radar")
    a.add_argument("--cap", required=True, type=float, help="total cap in credits approved by the user")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        sid = approve(args.flow, args.cap)
    except LooreError as e:
        print(e.hint(), file=sys.stderr)
        return 1
    print(sid)
    return 0


if __name__ == "__main__":
    sys.exit(main())
