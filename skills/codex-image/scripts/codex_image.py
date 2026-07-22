#!/usr/bin/env python3
"""
codex_image.py — генерация картинок через подписку Codex (ChatGPT Plus/Pro),
                 БЕЗ OPENAI_API_KEY и без поштучной оплаты API.

Картинки делает модель gpt-image-2. Доступ идёт по OAuth-подписке Codex
(тот же бэкенд, что у консольного агента Codex), а не по платному API-ключу.

────────────────────────────────────────────────────────────────────────
УСТАНОВКА (один раз)
────────────────────────────────────────────────────────────────────────
1) Установить Codex CLI:
       npm install -g @openai/codex

2) Залогиниться СВОЕЙ подпиской ChatGPT Plus/Pro (не ключом):
       codex login
   На сервере без браузера:
       codex login --device-auth
   (даётся ссылка + код, подтверждаешь с телефона)
   Токен сохранится в ~/.codex/auth.json — это и есть «доступ по подписке».

3) Поставить openai SDK для Python:
       pip install --upgrade openai

────────────────────────────────────────────────────────────────────────
ЗАПУСК
────────────────────────────────────────────────────────────────────────
    python3 codex_image.py "prompt на английском" [quality] [aspect] [ref1 ... ref5]

    quality : low (~45с) | medium (по умолч., ~1-2мин) | high (~2-3мин)
    aspect  : landscape (1536x1024) | square (1024x1024) | portrait (1024x1536)
    refN    : до 5 путей к референс-картинкам (png/jpg/webp) — стиль/персонаж/лого
              передаются модели как input_image (data URL) вместе с промптом

Скрипт печатает путь к готовому PNG (по умолчанию в ~/.codex/cache/images/).

────────────────────────────────────────────────────────────────────────
ВАЖНЫЕ НЮАНСЫ (проверено на практике, иначе ловишь ошибки)
────────────────────────────────────────────────────────────────────────
  • OAuth-токен лежит в  data["tokens"]["access_token"]  в ~/.codex/auth.json
  • Параметр `input` — это СПИСОК message-объектов, не голая строка.
  • stream=True ОБЯЗАТЕЛЕН (иначе HTTP 400) — поэтому читаем SSE через openai SDK.
  • store=False ОБЯЗАТЕЛЕН (иначе HTTP 400 от бэкенда Codex).
  • host-модель — gpt-5.5: именно она стабильно вызывает инструмент image_generation.
  • Референсы РАБОТАЮТ: до 5 картинок content-блоками
    {"type":"input_image","image_url":"data:<mime>;base64,...","detail":"auto"}
    рядом с input_text (подтверждено 2026-06-07, техника из ningzimu/codex-gpt-image).
    tool_choice={"type":"image_generation"} заставляет host-модель сразу рисовать.
  • НЕЛЬЗЯ вызывать openai.images.generate() / client.images — это путь API-ключа,
    через OAuth-подписку он не пустит. Только Responses API + tool image_generation.
  • Квота общая на подписку (не безлимит, но для потока контента хватает).
"""

from __future__ import annotations

import base64
import json
import mimetypes
import sys
import time
from pathlib import Path
from typing import Optional

from openai import OpenAI

CODEX_BASE_URL = "https://chatgpt.com/backend-api/codex"
HOST_MODEL = "gpt-5.5"            # host-модель, которая дёргает image-инструмент
IMAGE_MODEL = "gpt-image-2"
INSTRUCTIONS = (
    "You are an assistant that must fulfill image generation "
    "requests by using the image_generation tool when provided."
)
SIZES = {
    "landscape": "1536x1024",
    "square": "1024x1024",
    "portrait": "1024x1536",
}
AUTH_FILE = Path.home() / ".codex" / "auth.json"
CACHE_DIR = Path.home() / ".codex" / "cache" / "images"


def _load_auth() -> tuple[str, str]:
    """Читаем OAuth-токен подписки из ~/.codex/auth.json (создаётся `codex login`)."""
    if not AUTH_FILE.exists():
        raise RuntimeError(f"Codex auth не найден: {AUTH_FILE}. Запусти `codex login`.")
    data = json.loads(AUTH_FILE.read_text())
    tokens = data.get("tokens") or {}
    token = tokens.get("access_token")
    account_id = tokens.get("account_id", "")
    if not token:
        raise RuntimeError("Нет tokens.access_token в ~/.codex/auth.json")
    return token, account_id


def _client(token: str, account_id: str) -> OpenAI:
    """openai-клиент, нацеленный на Codex-бэкенд, авторизация = OAuth-токен подписки."""
    headers = {
        "OpenAI-Beta": "responses=experimental",
        "originator": "codex_cli_rs",
    }
    if account_id:
        headers["chatgpt-account-id"] = account_id
    return OpenAI(
        base_url=CODEX_BASE_URL,
        api_key=token,            # сюда идёт OAuth access_token, НЕ sk-... ключ
        default_headers=headers,
    )


def _extract_b64(obj) -> Optional[str]:
    """Рекурсивно обходим payload события и достаём самый длинный base64 картинки."""
    best: Optional[str] = None

    def visit(node):
        nonlocal best
        if isinstance(node, dict):
            for k, v in node.items():
                if k in ("result", "partial_image_b64", "b64_json", "image") and isinstance(v, str) and len(v) > 100:
                    if best is None or len(v) > len(best):
                        best = v
                else:
                    visit(v)
        elif isinstance(node, list):
            for it in node:
                visit(it)

    visit(obj)
    return best


MAX_REFS = 5
MAX_REF_BYTES = 15 * 1024 * 1024        # per file, pre-base64 (data URL adds ~33%)
MAX_REFS_TOTAL_BYTES = 40 * 1024 * 1024  # all refs combined
ALLOWED_REF_MIME = {"image/png", "image/jpeg", "image/webp"}


def _ref_block(path: Path) -> dict:
    """Build an input_image content block from a local image file (data URL)."""
    if not path.is_file():
        raise RuntimeError(f"Референс не найден или не файл: {path}")
    mime = mimetypes.guess_type(str(path))[0]
    if mime not in ALLOWED_REF_MIME:
        raise RuntimeError(
            f"Референс {path.name}: тип {mime or 'неизвестен'} не поддерживается "
            f"(только png/jpg/webp)")
    size = path.stat().st_size
    if size > MAX_REF_BYTES:
        raise RuntimeError(
            f"Референс {path.name}: {size // 1024 // 1024} MB > лимита "
            f"{MAX_REF_BYTES // 1024 // 1024} MB — ужми картинку")
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return {"type": "input_image",
            "image_url": f"data:{mime};base64,{b64}",
            "detail": "auto"}


def generate(prompt: str, quality: str = "medium", aspect: str = "landscape",
             refs: list[Path] | None = None) -> Path:
    token, account_id = _load_auth()
    client = _client(token, account_id)
    size = SIZES.get(aspect, SIZES["landscape"])

    refs = refs or []
    if len(refs) > MAX_REFS:
        raise RuntimeError(f"Максимум {MAX_REFS} референсов, передано {len(refs)}")
    total = sum(p.stat().st_size for p in refs if p.is_file())
    if total > MAX_REFS_TOTAL_BYTES:
        raise RuntimeError(
            f"Референсы суммарно {total // 1024 // 1024} MB > лимита "
            f"{MAX_REFS_TOTAL_BYTES // 1024 // 1024} MB")
    content = [{"type": "input_text", "text": prompt}]
    content += [_ref_block(p) for p in refs]

    stream = client.responses.create(
        model=HOST_MODEL,
        instructions=INSTRUCTIONS,
        input=[{
            "type": "message",
            "role": "user",
            "content": content,
        }],
        tools=[{
            "type": "image_generation",
            "model": IMAGE_MODEL,
            "quality": quality,
            "size": size,
        }],
        tool_choice={"type": "image_generation"},  # сразу рисуем, без размышлений
        store=False,    # обязательно
        stream=True,    # обязательно
    )

    # Картинка приходит кусками в потоке событий — собираем самый полный кадр.
    image_b64: Optional[str] = None
    for event in stream:
        try:
            payload = event.model_dump()
        except Exception:
            payload = getattr(event, "__dict__", {})
        found = _extract_b64(payload)
        if found and (image_b64 is None or len(found) > len(image_b64)):
            image_b64 = found

    if not image_b64:
        raise RuntimeError("В потоке не пришло изображение")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CACHE_DIR / f"img_{int(time.time())}.png"
    out_path.write_bytes(base64.b64decode(image_b64))
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: codex_image.py 'prompt' [quality:low|medium|high] "
              "[aspect:landscape|square|portrait] [ref1.png ... ref5.png]")
        sys.exit(2)
    p = sys.argv[1]
    rest = sys.argv[2:]
    # Foot-gun guard: quality/aspect are optional positionals, so a ref passed
    # as the 2nd arg must not be eaten as "quality". Anything that exists as a
    # file is a ref; the first two non-file args are quality and aspect.
    opts = [x for x in rest if not Path(x).is_file()]
    refs = [Path(x) for x in rest if Path(x).is_file()]
    if len(opts) > 2:
        # A third non-file arg is almost always a TYPO'D ref path — refuse
        # loudly instead of silently generating without the reference.
        print(f"Ошибка: лишние аргументы {opts[2:]} — это опечатка в пути "
              f"референса? Файл(ы) не найдены на диске", file=sys.stderr)
        sys.exit(2)
    q = opts[0] if len(opts) > 0 else "medium"
    a = opts[1] if len(opts) > 1 else "landscape"
    if q not in ("low", "medium", "high"):
        print(f"Ошибка: quality '{q}' не из low|medium|high "
              f"(если это путь референса — файла нет на диске)", file=sys.stderr)
        sys.exit(2)
    if a not in SIZES:
        print(f"Ошибка: aspect '{a}' не из {'|'.join(SIZES)}", file=sys.stderr)
        sys.exit(2)
    try:
        print(generate(p, q, a, refs=refs))
    except RuntimeError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        sys.exit(1)
