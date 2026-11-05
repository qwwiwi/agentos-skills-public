#!/usr/bin/env python3
"""Brief (ТЗ) tool for codex-image: intake questions -> brief.json -> check -> prompt.

Subcommands:
    questions [--type T]   print the intake questionnaire (Russian) to ask the requester
    init <brief.json>      write an empty brief template
    check <brief.json>     validate the brief; exit 1 with a list of what to ask
    prompt <brief.json>    build the final English prompt and the run command

Offline by design: no network, no API keys, no image generation.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import shlex
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

LOG = logging.getLogger("brief")

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = SKILL_DIR / "references" / "brands.json"

TYPES = ("youtube-cover", "banner", "post-illustration", "infographic", "sticker", "logo", "other")
ROUTES = ("subscription", "api")
ROLES = ("subject", "face", "style", "logo", "background", "layout", "clothing")
REF_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp")
MAX_REFS = {"subscription": 5, "api": 16}
QUALITIES = {
    "subscription": ("low", "medium", "high"),
    "api": ("low", "medium", "high", "xhigh", "max"),
}
SUBSCRIPTION_ASPECTS = {"landscape": "1536x1024", "square": "1024x1024", "portrait": "1024x1536"}
API_SIZE_PRESETS = {
    "1k": "1024x1024",
    "2k": "2048x2048",
    "2k-wide": "2048x1152",
    "qhd": "2560x1440",
    "4k": "3840x2160",
    "4k-tall": "2160x3840",
}
API_DEFAULT_MODEL = "gpt-image-2.6-flare"
# Folders whose images must never be used as refs: put rejected frames
# (blink, squint, side gaze) there and `check` will refuse them.
REJECTED_PATH_PARTS = ("_rejected",)
FACE_CONSTRAINT = (
    "eyes fully open, natural direct gaze exactly as in the face reference; "
    "do not redraw or restyle the face"
)
MAX_REF_BYTES = 15 * 1024 * 1024
MAX_TOTAL_REF_BYTES = 40 * 1024 * 1024

ROLE_PHRASES = {
    "subject": "subject reference: keep this subject/object recognisable and accurate",
    "face": (
        "face reference: the person MUST be this exact person; preserve the real face, "
        "likeness, glasses and hair, do NOT beautify"
    ),
    "style": (
        "style reference: copy its visual style (layout, palette, lighting, typography look), "
        "not its content or its text"
    ),
    "logo": "logo reference: reproduce this logo exactly as given, do not redraw or alter it",
    "background": "background reference: use this as the background / environment",
    "layout": "layout reference: follow this composition and element placement",
    "clothing": "clothing reference: dress the subject in this outfit",
}

COMMON_QUESTIONS = (
    ("purpose", "Зачем картинка и какую задачу решает? (кликабельность, анонс, объяснение, продажа)"),
    ("placement", "Где будет использоваться? (YouTube, Telegram-пост, лендинг, реклама, печать)"),
    ("size", "Формат и размер: горизонт/квадрат/вертикаль или точные пиксели? Нужен ли итоговый кроп (например 1920x1080)?"),
    ("text", "Какой ТОЧНЫЙ текст должен быть на картинке? Дословно, с регистром и пунктуацией. Или текста нет совсем?"),
    ("subject", "Что или кто в кадре? Люди (чьё лицо), предметы, логотипы."),
    ("scene", "Сцена и фон: где это происходит, какое окружение?"),
    ("outfit", "Если в кадре лицо автора: какой образ (одежда)? Только кадры с открытыми глазами и прямым взглядом (пресет лица из реестра)."),
    ("style", "Стиль и бренд: какой пресет бренда из реестра (brief.py presets) или свои пожелания по стилю, палитре, шрифту?"),
    ("references", "Референсы: пришлите файлы и для каждого скажите роль – лицо, стиль, логотип, объект, фон, композиция, одежда. Подписка – до 5, API – до 16."),
    ("avoid", "Чего точно НЕ должно быть? (цвета, элементы, лишний текст, водяные знаки)"),
    ("route", "Качество и маршрут: черновик/обычная картинка по подписке (до 1536 px) или 2K–4K через API (платно, нужно «да» владельца)?"),
)

TYPE_QUESTIONS: dict[str, tuple[tuple[str, str, bool], ...]] = {
    # (extra key, question, required)
    "youtube-cover": (
        ("headline", "Заголовок – не больше 4 слов. Какие именно слова?", False),
        ("highlight_word", "Какое ключевое слово выделить (жёлтая плашка)?", False),
        ("face_emotion", "Какая эмоция лица? (удивление, улыбка, серьёзный, указывает на текст)", True),
        ("face_side", "С какой стороны лицо – слева или справа (текст на противоположной)?", True),
        ("readability_320", "Подтвердите: заголовок должен читаться на превью 320x180 (крупно, контрастно).", False),
    ),
    "banner": (
        ("platform", "Площадка и точный размер баннера в пикселях?", True),
        ("safe_zone", "Есть ли зоны, которые обрежутся или перекроются (аватар, кнопки)?", False),
        ("cta", "Есть ли призыв к действию? Точный текст кнопки/CTA.", False),
    ),
    "post-illustration": (
        ("post_topic", "О чём пост одной фразой? Какую мысль картинка должна передать?", True),
        ("platform", "Telegram, Instagram, VK? (влияет на формат)", False),
    ),
    "infographic": (
        ("data_points", "Точные цифры и подписи, которые должны быть на инфографике (каждую дословно)?", True),
        ("reading_order", "Порядок чтения: сверху вниз, слева направо, по шагам?", False),
    ),
    "sticker": (
        ("transparent", "Нужен ли прозрачный фон?", True),
        ("emotion", "Какая эмоция/действие у персонажа?", False),
    ),
    "logo": (
        ("logo_kind", "Знак, надпись или знак + надпись?", True),
        ("vector_needed", "Нужен ли вектор (SVG)? Подписка SVG не умеет – только API 2.6 или ручной SVG.", True),
    ),
    "other": (),
}


@dataclass
class Reference:
    """One reference image with its role.

    Attributes:
        path: Absolute (or ~) path to a local png/jpg/webp file.
        role: One of ROLES.
        note: Free-form note about what to take from the image.
    """

    path: str = ""
    role: str = ""
    note: str = ""


@dataclass
class TextItem:
    """One exact text string to render on the image.

    Attributes:
        content: Exact text, verbatim (case and punctuation matter).
        position: Where on the image (e.g. "left half, top").
        typography: Font look (e.g. "heavy bold condensed sans, all caps").
        kind: headline | subline | label | cta | other.
    """

    content: str = ""
    position: str = ""
    typography: str = ""
    kind: str = "headline"


@dataclass
class Brief:
    """A full image brief (ТЗ). Field names match the JSON file."""

    type: str = "other"
    preset: str = ""
    preset_replace_roles: list[str] = field(default_factory=list)
    purpose: str = ""
    placement: str = ""
    route: str = "subscription"
    quality: str = "medium"
    aspect: str = "landscape"
    size: str = ""
    api_model: str = ""
    api_owner_ok: bool = False
    final_size: str = ""
    scene: str = ""
    subject: str = ""
    details: str = ""
    style: str = ""
    no_text: bool = False
    text: list[TextItem] = field(default_factory=list)
    references: list[Reference] = field(default_factory=list)
    references_none_reason: str = ""
    avoid: list[str] = field(default_factory=list)
    preserve: list[str] = field(default_factory=list)
    extra: dict[str, str] = field(default_factory=dict)


@dataclass
class Preset:
    """A brand preset from the registry."""

    name: str
    description: str = ""
    references: list[Reference] = field(default_factory=list)
    style_notes: list[str] = field(default_factory=list)
    avoid: list[str] = field(default_factory=list)


class BriefError(Exception):
    """Raised when a brief file cannot be read or parsed."""


def _as_str(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _as_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [v.strip() for v in value if isinstance(v, str) and v.strip()]


def _parse_refs(value: object) -> list[Reference]:
    if not isinstance(value, list):
        return []
    refs = []
    for item in value:
        if isinstance(item, dict):
            refs.append(Reference(_as_str(item.get("path")), _as_str(item.get("role")), _as_str(item.get("note"))))
        elif isinstance(item, str):
            refs.append(Reference(path=item.strip()))
    return refs


def load_brief(path: Path) -> Brief:
    """Read and parse a brief JSON file.

    Args:
        path: Path to brief.json.

    Returns:
        Parsed Brief. Unknown keys are ignored; wrong types become empty values.

    Raises:
        BriefError: If the file is missing or not a JSON object.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BriefError(f"файл брифа не найден: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BriefError(f"бриф не является валидным JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise BriefError("бриф должен быть JSON-объектом")

    text_items = []
    raw_text = raw.get("text")
    if isinstance(raw_text, str):
        raw_text = [{"content": raw_text}]
    if isinstance(raw_text, list):
        for item in raw_text:
            if isinstance(item, dict):
                text_items.append(
                    TextItem(
                        content=item.get("content", "") if isinstance(item.get("content"), str) else "",
                        position=_as_str(item.get("position")),
                        typography=_as_str(item.get("typography")),
                        kind=_as_str(item.get("kind")) or "headline",
                    )
                )
            elif isinstance(item, str):
                text_items.append(TextItem(content=item))

    raw_extra = raw.get("extra")
    extra = {str(k): _as_str(v) if not isinstance(v, bool) else ("да" if v else "нет")
             for k, v in raw_extra.items()} if isinstance(raw_extra, dict) else {}

    return Brief(
        type=_as_str(raw.get("type")) or "other",
        preset=_as_str(raw.get("preset")),
        preset_replace_roles=_as_str_list(raw.get("preset_replace_roles")),
        purpose=_as_str(raw.get("purpose")),
        placement=_as_str(raw.get("placement")),
        route=_as_str(raw.get("route")),
        quality=_as_str(raw.get("quality")),
        aspect=_as_str(raw.get("aspect")),
        size=_as_str(raw.get("size")),
        api_model=_as_str(raw.get("api_model")),
        api_owner_ok=raw.get("api_owner_ok") is True,
        final_size=_as_str(raw.get("final_size")),
        scene=_as_str(raw.get("scene")),
        subject=_as_str(raw.get("subject")),
        details=_as_str(raw.get("details")),
        style=_as_str(raw.get("style")),
        no_text=raw.get("no_text") is True,
        text=text_items,
        references=_parse_refs(raw.get("references")),
        references_none_reason=_as_str(raw.get("references_none_reason")),
        avoid=_as_str_list(raw.get("avoid")),
        preserve=_as_str_list(raw.get("preserve")),
        extra=extra,
    )


def load_registry(path: Path) -> dict[str, Preset]:
    """Load brand presets from the registry JSON.

    Args:
        path: Path to references/brands.json.

    Returns:
        Mapping preset name -> Preset. Empty if the file is missing.

    Raises:
        BriefError: If the file exists but is not valid JSON.
    """
    if not path.is_file():
        LOG.warning("registry not found: %s", path)
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BriefError(f"реестр брендов не является валидным JSON: {exc}") from exc
    presets_raw = raw.get("presets") if isinstance(raw, dict) else None
    if not isinstance(presets_raw, dict):
        return {}
    presets = {}
    for name, item in presets_raw.items():
        if not isinstance(item, dict):
            continue
        presets[name] = Preset(
            name=name,
            description=_as_str(item.get("description")),
            references=_parse_refs(item.get("references")),
            style_notes=_as_str_list(item.get("style_notes")),
            avoid=_as_str_list(item.get("avoid")),
        )
    return presets


def resolve(brief: Brief, registry: dict[str, Preset]) -> tuple[list[Reference], list[str], list[str]]:
    """Merge preset data into the brief's own references, style notes and avoid list.

    Preset references come first, then the brief's own. Preset refs whose role is in
    brief.preset_replace_roles are dropped (e.g. swap the brand logo); refs with the
    same path are not duplicated.

    Args:
        brief: Parsed brief.
        registry: Loaded presets.

    Returns:
        (references, style_notes, avoid) after merging. Unknown preset -> brief data only.
    """
    preset = registry.get(brief.preset) if brief.preset else None
    refs = [r for r in preset.references if r.role not in brief.preset_replace_roles] if preset else []
    seen = {r.path for r in refs}
    refs += [r for r in brief.references if r.path not in seen]
    notes = list(preset.style_notes) if preset else []
    avoid = list(preset.avoid) if preset else []
    avoid += [a for a in brief.avoid if a not in avoid]
    return refs, notes, avoid


def parse_size(value: str) -> tuple[int, int] | None:
    """Parse "WxH" into integers, or None if malformed."""
    m = re.fullmatch(r"\s*(\d+)\s*[xх×]\s*(\d+)\s*", value)
    return (int(m.group(1)), int(m.group(2))) if m else None


def api_size_errors(size: str) -> list[str]:
    """Validate an API image size against the rules in SKILL.md.

    Args:
        size: "WxH" or a preset name (1k, 2k, 2k-wide, qhd, 4k, 4k-tall).

    Returns:
        List of Russian error strings (empty if legal).
    """
    resolved = API_SIZE_PRESETS.get(size, size)
    wh = parse_size(resolved)
    if wh is None:
        return [f"size «{size}»: нужен формат ШxВ (например 2048x1152) или пресет {'/'.join(API_SIZE_PRESETS)}"]
    w, h = wh
    errors = []
    if w % 16 or h % 16:
        errors.append(f"size {w}x{h}: ширина и высота должны быть кратны 16")
    if max(w, h) > 3840:
        errors.append(f"size {w}x{h}: сторона не больше 3840 px")
    if min(w, h) == 0 or max(w, h) / min(w, h) > 3:
        errors.append(f"size {w}x{h}: соотношение сторон не больше 3:1")
    if not 655_360 <= w * h <= 8_294_400:
        errors.append(f"size {w}x{h}: площадь {w * h:,} px вне диапазона 655,360–8,294,400")
    return errors


def check(brief: Brief, registry: dict[str, Preset]) -> list[str]:
    """Validate a brief. Every problem is phrased as what to ask or fix.

    Args:
        brief: Parsed brief.
        registry: Loaded presets.

    Returns:
        List of Russian problem strings; empty means the brief is ready.
    """
    p: list[str] = []
    if brief.type not in TYPES:
        p.append(f"type «{brief.type}» неизвестен: один из {', '.join(TYPES)}")
    if brief.preset and brief.preset not in registry:
        p.append(f"preset «{brief.preset}» нет в реестре брендов: {', '.join(sorted(registry)) or 'реестр пуст'}")
    for key, label in (
        ("purpose", "зачем картинка (purpose)"),
        ("placement", "где будет использоваться (placement)"),
        ("subject", "кто/что в кадре (subject)"),
    ):
        if not getattr(brief, key):
            p.append(f"не заполнено: {label}")
    if not brief.scene and brief.type not in ("logo", "sticker"):
        p.append("не заполнено: сцена и фон (scene)")

    refs, notes, _ = resolve(brief, registry)
    if not brief.style and not notes:
        p.append("не заполнено: стиль/бренд (style или preset)")

    # Route, quality, size.
    if brief.route not in ROUTES:
        p.append(f"route «{brief.route}»: subscription (подписка) или api")
    else:
        if brief.quality not in QUALITIES[brief.route]:
            p.append(f"quality «{brief.quality}» недопустим для {brief.route}: {'|'.join(QUALITIES[brief.route])}")
        if brief.route == "subscription":
            if brief.aspect not in SUBSCRIPTION_ASPECTS:
                p.append(f"aspect «{brief.aspect}»: для подписки только {'|'.join(SUBSCRIPTION_ASPECTS)}")
            if brief.size and brief.size not in SUBSCRIPTION_ASPECTS.values():
                p.append(
                    f"size «{brief.size}» недоступен по подписке (только {', '.join(SUBSCRIPTION_ASPECTS.values())}); "
                    "для 2K–4K нужен route=api, итоговый кроп укажите в final_size"
                )
        else:
            if not brief.size:
                p.append("не заполнено: size для API (ШxВ или пресет)")
            else:
                p.extend(api_size_errors(brief.size))
            model = brief.api_model or API_DEFAULT_MODEL
            if not model.startswith(("gpt-image-", "chatgpt-image-")):
                p.append(f"api_model «{model}»: ключ API только для image-моделей (gpt-image-*, chatgpt-image-*)")
            if not brief.api_owner_ok:
                p.append("route=api платный: нужно явное «да» владельца (api_owner_ok: true)")
    if brief.final_size and parse_size(brief.final_size) is None:
        p.append(f"final_size «{brief.final_size}»: нужен формат ШxВ")

    # Text.
    if brief.no_text and brief.text:
        p.append("no_text=true, но text заполнен: уточните, нужен ли текст")
    elif not brief.no_text:
        if not brief.text:
            p.append("не заполнено: точный текст на картинке (text) или явно no_text: true")
        for i, t in enumerate(brief.text, 1):
            if not t.content.strip():
                p.append(f"text[{i}]: пустой текст – спросите точную формулировку")
                continue
            if t.content != t.content.strip():
                p.append(f"text[{i}]: лишние пробелы по краям – текст должен быть дословным")
            if '"' in t.content or "«" in t.content or "»" in t.content:
                p.append(f"text[{i}]: уберите кавычки из content – строка сама будет взята в кавычки в промпте")
            if "→" in t.content:
                p.append(f"text[{i}]: стрелка «→» искажается моделью – замените словом")
            if not t.position:
                p.append(f"text[{i}] «{t.content}»: не указано положение (position)")

    # References.
    if not refs and not brief.references_none_reason:
        p.append("нет референсов: спросите у заказчика (или preset), либо укажите references_none_reason")
    limit = MAX_REFS.get(brief.route)
    if limit is not None and len(refs) > limit:
        p.append(f"референсов {len(refs)}, а для {brief.route} максимум {limit}")
    total = 0
    for i, r in enumerate(refs, 1):
        label = f"референс {i} ({r.path or 'без пути'})"
        if r.role not in ROLES:
            p.append(f"{label}: нет роли или роль неизвестна – одна из {'|'.join(ROLES)}")
        if not r.path:
            p.append(f"референс {i}: не указан путь к файлу")
            continue
        path = Path(r.path).expanduser()
        if any(part in REJECTED_PATH_PARTS for part in path.parts):
            p.append(f"{label}: кадр из отбракованной папки ({'/'.join(REJECTED_PATH_PARTS)}) – запрещён, возьмите одобренный кадр из пресета лица")
            continue
        if not path.is_file():
            p.append(f"{label}: файл не найден")
            continue
        if path.suffix.lower() not in REF_SUFFIXES:
            p.append(f"{label}: только png/jpg/webp (svg растеризуйте в png)")
        size = path.stat().st_size
        total += size
        if size > MAX_REF_BYTES:
            p.append(f"{label}: больше 15 МБ")
    if brief.route == "subscription" and total > MAX_TOTAL_REF_BYTES:
        p.append("референсы суммарно больше 40 МБ – уменьшите файлы")

    # Type-specific answers.
    for key, question, required in TYPE_QUESTIONS.get(brief.type, ()):
        if required and not brief.extra.get(key):
            p.append(f"{brief.type}: нет ответа extra.{key} – «{question}»")
    if brief.type == "youtube-cover":
        headlines = [t for t in brief.text if t.kind == "headline"]
        words = sum(len(t.content.split()) for t in headlines)
        if words > 4:
            p.append(f"youtube-cover: заголовок {words} слов, нужно не больше 4")
        if brief.route == "subscription" and brief.aspect != "landscape":
            p.append("youtube-cover: по подписке нужен aspect=landscape (16:9 кроп в final_size)")
        if not any(r.role == "face" for r in refs) and not brief.references_none_reason:
            p.append("youtube-cover: нет референса лица (role=face)")
    return p


def _sentence(text: str) -> str:
    text = text.strip()
    return text if not text or text[-1] in ".!?" else text + "."


def _format_label(brief: Brief) -> str:
    if brief.route == "api":
        return API_SIZE_PRESETS.get(brief.size, brief.size)
    return f"{brief.aspect} {SUBSCRIPTION_ASPECTS.get(brief.aspect, '')}".strip()


def build_prompt(brief: Brief, registry: dict[str, Preset]) -> str:
    """Build the final English prompt following the official template.

    Order: Intent/use -> References -> Scene -> Subject -> Details -> Text -> Constraints.

    Args:
        brief: Parsed, checked brief.
        registry: Loaded presets.

    Returns:
        Prompt text (one paragraph per section).
    """
    refs, notes, avoid = resolve(brief, registry)
    parts = [
        f"Intent: {_sentence(brief.purpose)} Use: {_sentence(brief.placement)} "
        f"Format: {_format_label(brief)}{', final crop ' + brief.final_size if brief.final_size else ''}."
    ]
    if refs:
        lines = []
        for i, r in enumerate(refs, 1):
            note = f" ({r.note})" if r.note else ""
            lines.append(f"Image {i}: {ROLE_PHRASES.get(r.role, r.role)}{note}.")
        parts.append("References: " + " ".join(lines))
    if brief.scene:
        parts.append(f"Scene: {_sentence(brief.scene)}")
    parts.append(f"Subject: {_sentence(brief.subject)}")
    extra_bits = [f"{k.replace('_', ' ')}: {v}" for k, v in brief.extra.items() if v and k != "headline"]
    details = " ".join(_sentence(x) for x in [brief.details, brief.style, *notes, *extra_bits] if x)
    if details:
        parts.append(f"Details: {details}")
    if brief.no_text:
        parts.append("Text: no text, letters, numbers, logos with words or watermarks anywhere in the image.")
    else:
        items = []
        for t in brief.text:
            bits = [f'"{t.content}"', t.position, t.typography]
            items.append(", ".join(b for b in bits if b))
        parts.append(
            "Text: render exactly the following text, each string exactly once, spelled exactly as written "
            "(keep the original language, case and punctuation): "
            + "; ".join(items)
            + ". No extra text, no other words, letters or watermarks."
        )
    constraints = []
    if brief.preserve:
        constraints.append("Preserve: " + "; ".join(brief.preserve) + ".")
    if avoid:
        constraints.append("Avoid: " + "; ".join(avoid) + ".")
    if any(r.role == "face" for r in refs):
        constraints.append(FACE_CONSTRAINT[0].upper() + FACE_CONSTRAINT[1:] + ".")
    constraints.append("High contrast, crisp, no watermark.")
    parts.append("Constraints: " + " ".join(constraints))
    return "\n".join(parts)


def run_command(brief: Brief, registry: dict[str, Preset], prompt: str) -> str:
    """Return the exact command (subscription) or the API params block.

    Args:
        brief: Parsed, checked brief.
        registry: Loaded presets.
        prompt: The built prompt.

    Returns:
        Shell command or a parameters listing. Never touches any API key.
    """
    refs, _, _ = resolve(brief, registry)
    if brief.route == "api":
        size = API_SIZE_PRESETS.get(brief.size, brief.size)
        endpoint = "/v1/images/edits" if refs else "/v1/images/generations"
        lines = [
            "# route=api (paid, owner OK required; print the cost estimate before the call)",
            f"model:    {brief.api_model or API_DEFAULT_MODEL}",
            f"size:     {size}",
            f"quality:  {brief.quality}",
            f"endpoint: {endpoint}",
            f"images:   {len(refs)} (in the order of 'Image N' in the prompt)",
        ]
        lines += [f"  {i}. {r.path}" for i, r in enumerate(refs, 1)]
        lines.append("# key: see SKILL.md rule (image models only); brief.py never reads it")
        return "\n".join(lines)
    args = ["scripts/run.sh", prompt, brief.quality, brief.aspect, *[str(Path(r.path).expanduser()) for r in refs]]
    cmd = " ".join(shlex.quote(a) for a in args)
    return f"# run from the skill root: cd {shlex.quote(str(SKILL_DIR))}\n{cmd}"


def questionnaire(kind: str) -> str:
    """Return the Russian intake questionnaire for a brief type."""
    lines = ["Вопросы заказчику перед генерацией (задайте все, ответы – в brief.json):", ""]
    lines += [f"{i}. {q}  [{key}]" for i, (key, q) in enumerate(COMMON_QUESTIONS, 1)]
    specific = TYPE_QUESTIONS.get(kind, ())
    if specific:
        lines += ["", f"Для типа {kind}:"]
        lines += [
            f"{i}. {q}  [extra.{key}{', обязательно' if req else ''}]"
            for i, (key, q, req) in enumerate(specific, len(COMMON_QUESTIONS) + 1)
        ]
    lines += ["", f"Роли референсов: {', '.join(ROLES)}.", "Пресеты брендов: brief.py presets."]
    return "\n".join(lines)


def template(kind: str) -> dict[str, object]:
    """Return an empty brief template as a JSON-ready dict."""
    data = asdict(Brief(type=kind))
    data["text"] = [asdict(TextItem())]
    data["references"] = [asdict(Reference())]
    data["extra"] = {key: "" for key, _, _ in TYPE_QUESTIONS.get(kind, ())}
    data["api_model"] = ""
    return data


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Arguments without the program name (defaults to sys.argv[1:]).

    Returns:
        Process exit code.
    """
    logging.basicConfig(level=logging.WARNING, format="[brief] %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description="codex-image brief (ТЗ) tool")
    ap.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help="brand presets JSON")
    sub = ap.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("questions", help="print the intake questionnaire")
    q.add_argument("--type", choices=TYPES, default="other")
    i = sub.add_parser("init", help="write an empty brief template")
    i.add_argument("brief", type=Path)
    i.add_argument("--type", choices=TYPES, default="other")
    i.add_argument("--force", action="store_true", help="overwrite an existing file")
    c = sub.add_parser("check", help="validate a brief")
    c.add_argument("brief", type=Path)
    pr = sub.add_parser("prompt", help="build the prompt and the run command")
    pr.add_argument("brief", type=Path)
    sub.add_parser("presets", help="list brand presets")
    args = ap.parse_args(argv)

    if args.cmd == "questions":
        print(questionnaire(args.type))
        return 0
    if args.cmd == "init":
        if args.brief.exists() and not args.force:
            print(f"Файл уже есть: {args.brief} (--force чтобы перезаписать)", file=sys.stderr)
            return 1
        args.brief.write_text(json.dumps(template(args.type), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        LOG.info("template written: %s", args.brief)
        print(f"Шаблон брифа записан: {args.brief}")
        return 0

    try:
        registry = load_registry(args.registry)
        if args.cmd == "presets":
            for name, preset in sorted(registry.items()):
                print(f"{name}: {preset.description} ({len(preset.references)} refs)")
            return 0
        brief = load_brief(args.brief)
    except BriefError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 2

    problems = check(brief, registry)
    if problems:
        print("Бриф не готов – вернитесь к заказчику и уточните:", file=sys.stderr)
        for n, item in enumerate(problems, 1):
            print(f"  {n}. {item}", file=sys.stderr)
        return 1
    if args.cmd == "check":
        print("Бриф готов: check пройден.")
        return 0
    prompt = build_prompt(brief, registry)
    print(prompt)
    print()
    print(run_command(brief, registry, prompt))
    return 0


if __name__ == "__main__":
    sys.exit(main())
