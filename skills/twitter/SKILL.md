---
name: twitter
description: "Read Twitter/X tweets, articles, threads, profiles, and search. Use when the user shares a Twitter/X link, asks to read a tweet/article, check a profile, search tweets, or fetch tweet content. Covers both free (FxTwitter) and paid (SocialData API) methods with automatic fallback."
---

# Twitter/X Reader

Универсальный скилл для чтения Twitter/X. Два источника с автоматическим fallback.

## API ключ

`$SOCIALDATA_API_KEY` -- переменная окружения (env var или `~/.claude/skills/twitter/.secrets/socialdata.env`).
Проверка: `echo $SOCIALDATA_API_KEY` -- должен начинаться с цифр и `|`.

## Стратегия выбора источника

| Задача | Источник | Fallback |
|--------|----------|----------|
| Одиночный твит | FxTwitter (бесплатно) | SocialData |
| Профиль | FxTwitter (бесплатно) | SocialData |
| **Статья (X Article)** | **FxTwitter** (article в tweet) | SocialData article endpoint |
| Тред (цепочка) | SocialData | -- |
| Таймлайн (последние посты) | SocialData | -- |
| Поиск | SocialData | -- |
| Комментарии | SocialData | -- |

**Принцип:** бесплатное первым. SocialData только когда FxTwitter не может или не справился.

---

## 1. Одиночный твит

### Шаг 1: FxTwitter (бесплатно)

Извлеки username и tweet_id из URL:
- `https://x.com/{username}/status/{tweet_id}`
- `https://twitter.com/{username}/status/{tweet_id}`
- URL может содержать `?s=46&t=...` -- игнорируй query params.

```bash
curl -s "https://api.fxtwitter.com/{username}/status/{tweet_id}"
```

Ответ:
```json
{
  "code": 200,
  "tweet": {
    "text": "полный текст",
    "author": { "name": "...", "screen_name": "...", "followers": 12345 },
    "likes": 100, "retweets": 50, "replies": 10, "views": 5000,
    "created_at": "...",
    "media": { "photos": [...], "videos": [...] },
    "quote": { ... },
    "article": { ... }
  }
}
```

### Шаг 2: Fallback на SocialData (если code != 200)

```bash
curl -s -H "Authorization: Bearer $SOCIALDATA_API_KEY" \
  "https://api.socialdata.tools/twitter/tweets/{tweet_id}"
```

---

## 2. Статья (X Article / X Notes)

X Articles -- длинные посты (до 25000 символов). Определяются по:
- URL ведёт на твит, но текст твита пустой или содержит только `t.co` ссылку
- В ответе FxTwitter есть поле `tweet.article`
- В ответе SocialData в `entities.urls` есть `x.com/i/article/{article_id}`

### Метод 1: FxTwitter (рекомендуемый)

FxTwitter возвращает article как часть tweet response:

```bash
curl -s "https://api.fxtwitter.com/{username}/status/{tweet_id}"
```

Если в ответе есть `tweet.article`, извлеки текст:

```python
import json, sys
d = json.load(sys.stdin)
article = d.get('tweet', {}).get('article', {})
blocks = article.get('content', {}).get('blocks', [])

print(f"Title: {article.get('title', '')}")
print(f"Preview: {article.get('preview_text', '')}")
print()

for block in blocks:
    text = block.get('text', '')
    if text.strip():
        print(text)
        print()
```

**Структура article:**
```json
{
  "article": {
    "id": "article_id",
    "title": "Title of the article",
    "preview_text": "First 200 chars...",
    "created_at": "ISO datetime",
    "modified_at": "ISO datetime",
    "cover_media": { "media_info": { "original_img_url": "..." } },
    "content": {
      "blocks": [
        { "key": "...", "text": "Paragraph text", "type": "unstyled" },
        { "key": "...", "text": "Header", "type": "header-two" },
        ...
      ]
    }
  }
}
```

**Типы блоков (block.type):**
- `unstyled` -- обычный параграф
- `header-one`, `header-two`, `header-three` -- заголовки
- `unordered-list-item` -- элемент списка
- `ordered-list-item` -- нумерованный список
- `blockquote` -- цитата
- `atomic` -- медиа (изображение/видео)

### Метод 2: SocialData article endpoint (fallback)

Если FxTwitter не вернул article, попробуй SocialData:

1. Сначала получи tweet через SocialData и найди article_id в entities:
```bash
curl -s -H "Authorization: Bearer $SOCIALDATA_API_KEY" \
  "https://api.socialdata.tools/twitter/tweets/{tweet_id}"
```

2. Найди article_id в `entities.urls[].expanded_url` (формат: `x.com/i/article/{article_id}`)

3. Запроси статью:
```bash
curl -s -H "Authorization: Bearer $SOCIALDATA_API_KEY" \
  "https://api.socialdata.tools/twitter/article/{article_id}"
```

**Важно:** SocialData article endpoint иногда возвращает "Tweet not found" даже для существующих статей. В таких случаях используй FxTwitter.

### Полный pipeline для статей

```bash
# 1. Попробуй FxTwitter
RESPONSE=$(curl -s "https://api.fxtwitter.com/{username}/status/{tweet_id}")

# 2. Проверь есть ли article
HAS_ARTICLE=$(echo "$RESPONSE" | python3 -c "
import json,sys
d=json.load(sys.stdin)
a=d.get('tweet',{}).get('article')
print('yes' if a else 'no')
")

if [ "$HAS_ARTICLE" = "yes" ]; then
  # Извлеки текст из FxTwitter article
  echo "$RESPONSE" | python3 -c "
import json,sys
d=json.load(sys.stdin)
a=d['tweet']['article']
print(f\"Title: {a.get('title','')}\")
for b in a.get('content',{}).get('blocks',[]):
    t=b.get('text','')
    if t.strip(): print(t+'\n')
"
else
  # Fallback: SocialData
  # Получи article_id из entities
  ARTICLE_ID=$(curl -s -H "Authorization: Bearer $SOCIALDATA_API_KEY" \
    "https://api.socialdata.tools/twitter/tweets/{tweet_id}" | \
    python3 -c "
import json,sys
d=json.load(sys.stdin)
for u in d.get('entities',{}).get('urls',[]):
    eu=u.get('expanded_url','')
    if '/article/' in eu:
        print(eu.split('/article/')[-1])
        break
")
  if [ -n "$ARTICLE_ID" ]; then
    curl -s -H "Authorization: Bearer $SOCIALDATA_API_KEY" \
      "https://api.socialdata.tools/twitter/article/$ARTICLE_ID"
  fi
fi
```

---

## 3. Тред (цепочка твитов)

Только через SocialData. Возвращает все твиты в треде за один запрос.

```bash
curl -s -H "Authorization: Bearer $SOCIALDATA_API_KEY" \
  "https://api.socialdata.tools/twitter/thread/{tweet_id}"
```

`tweet_id` -- ID любого твита в треде (обычно первого).

---

## 4. Профиль пользователя

### Шаг 1: FxTwitter (бесплатно)

```bash
curl -s "https://api.fxtwitter.com/{username}"
```

### Шаг 2: Fallback на SocialData

```bash
curl -s -H "Authorization: Bearer $SOCIALDATA_API_KEY" \
  "https://api.socialdata.tools/twitter/user/{screen_name}"
```

---

## 5. Таймлайн (последние посты пользователя)

Только через SocialData. Требует user_id (не username).

```bash
# Сначала получи user_id
USER_ID=$(curl -s -H "Authorization: Bearer $SOCIALDATA_API_KEY" \
  "https://api.socialdata.tools/twitter/user/{screen_name}" | \
  python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")

# Затем таймлайн (до 20 твитов)
curl -s -H "Authorization: Bearer $SOCIALDATA_API_KEY" \
  "https://api.socialdata.tools/twitter/user/$USER_ID/tweets"
```

Пагинация: `?cursor={next_cursor}` из ответа.

---

## 6. Поиск твитов

Только через SocialData. Поддерживает Twitter Advanced Search операторы.

```bash
curl -s -H "Authorization: Bearer $SOCIALDATA_API_KEY" \
  "https://api.socialdata.tools/twitter/search?query={query}&type=Latest"
```

`type`: `Latest` или `Top`.

Примеры запросов:
- `from:username` -- твиты конкретного пользователя
- `"exact phrase"` -- точная фраза
- `filter:links` -- только с ссылками
- `min_faves:100` -- минимум 100 лайков
- `lang:ru` -- только русский
- `since:2026-01-01 until:2026-03-28` -- по дате

---

## 7. Комментарии к твиту

Только через SocialData.

```bash
curl -s -H "Authorization: Bearer $SOCIALDATA_API_KEY" \
  "https://api.socialdata.tools/twitter/tweets/{tweet_id}/comments"
```

Пагинация: `?cursor={next_cursor}`.

---

## Формат вывода

При показе контента пользователю:
1. Автор: имя + @handle + followers
2. Дата публикации
3. Полный текст (для статей -- title + body)
4. Медиа (если есть): описание фото/видео
5. Вовлечённость: лайки, ретвиты, просмотры, bookmarks
6. Цитата (если есть)

Для статей:
1. Title
2. Автор + метрики
3. Ключевые тезисы (summary)
4. Полный текст (если просят)

---

## Стоимость SocialData

| Endpoint | Цена |
|----------|------|
| Твиты, профили, таймлайны, поиск | $0.0002 / запрос |
| Статьи | $0.0002 / шт |
| Комментарии | $0.0002 / шт |

API key: `$SOCIALDATA_API_KEY` (env var или `~/.claude/skills/twitter/.secrets/socialdata.env`).
Dashboard: https://dashboard.socialdata.tools

---

## Ошибки

| Ситуация | Что делать |
|----------|-----------|
| FxTwitter code 404 | Твит удалён/приватный. Попробуй SocialData |
| FxTwitter таймаут | Fallback на SocialData |
| SocialData 401 | Проверь $SOCIALDATA_API_KEY |
| SocialData 429 | Rate limit. Подожди 60 сек |
| SocialData article "Tweet not found" | Используй FxTwitter -- article в поле tweet.article |
| Твит без текста + t.co ссылка | Это Article. Проверь tweet.article (FxTwitter) или entities.urls (SocialData) |
