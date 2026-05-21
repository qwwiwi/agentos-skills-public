---
name: perplexity-research
description: "Веб-ресёрч через Perplexity Sonar API. Используй когда нужен актуальный поиск в интернете, факт-чек, анализ трендов, best practices. Триггеры: «загугли», «найди», «ресёрч», «что говорят про», «best practices», «как правильно», «perplexity»."
metadata:
  clawdbot:
    emoji: 🔍
    command: /perplexity
---

# Perplexity Web Research

Веб-ресёрч через Perplexity Sonar API с цитатами.

## API Key

```
~/.claude/skills/perplexity-research/.secrets/perplexity.env
```

Загрузка: `source ~/.claude/skills/perplexity-research/.secrets/perplexity.env` → переменная `PERPLEXITY_API_KEY`

Set `PERPLEXITY_API_KEY=<YOUR_API_KEY>` in your environment or secrets file.

## Использование

```bash
source ~/.claude/skills/perplexity-research/.secrets/perplexity.env

curl -s --max-time 60 "https://api.perplexity.ai/chat/completions" \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
  "model": "sonar-pro",
  "messages": [{"role": "user", "content": "your query here"}],
  "search_recency_filter": "month",
  "return_citations": true
}'
```

## Модели

| Модель | Для чего | Цена |
|--------|----------|------|
| sonar-pro | Глубокий ресёрч, сложные вопросы | ~$3/1000 запросов |
| sonar | Быстрый поиск, простые вопросы | ~$1/1000 запросов |

## Параметры

- `search_recency_filter`: `hour`, `day`, `week`, `month` -- фильтр свежести
- `return_citations`: `true` -- возвращает источники
- `temperature`: 0.0-1.0 (по умолчанию 0.2)

## Парсинг ответа

```python
import json
data = json.loads(response)
text = data['choices'][0]['message']['content']
citations = data.get('citations', [])
```

## Когда использовать

- Актуальные данные из интернета
- Best practices, how-to
- Факт-чек утверждений
- Анализ трендов и новостей
- Сравнение технологий

## Когда НЕ использовать

- Internal data sources
- Внутренние файлы/конфиги
- Задачи не требующие веб-поиска
