# Monitoring Agent

Следит за логами, метриками, чатами команды, делает daily digests, поднимает long-term память о происходящем.

## Что умеет

- Анализировать архивы Telegram-чатов
- Собирать daily/weekly digest по чатам
- Делать самодиагностику системы
- Аудитить файлы памяти (что выросло, что устарело, что декомпонзировать)
- Регулярный мониторинг тем (через cron)

## Скиллы

### Анализ чатов

- [`chat-archive`](../../skills/chat-archive/) — анализ архивов Telegram-чатов, извлечение ключевых событий

### Мониторинг тем

- [`topic-monitor`](../../skills/topic-monitor/) — регулярный мониторинг темы через cron, alerts при появлении свежего контента
- [`perplexity-research`](../../skills/perplexity-research/) — углублённый ресерч найденного

### Память и аудит

- [`memory-audit`](../../skills/memory-audit/) — аудит файлов памяти, выявление устаревшего и дублей
- [`learnings`](../../skills/learnings/) — Episodes → Learnings, фиксация инцидентов и патернов
- [`agent-introspection`](../../skills/agent-introspection/) — самодиагностика агента

### Транскрибация и сбор

- [`transcript`](../../skills/transcript/) — расшифровка созвонов
- [`groq-voice`](../../skills/groq-voice/) — быстрая транскрибация через Groq Whisper
- [`markdown-new`](../../skills/markdown-new/) — выжимка из URL

### Отчёты

- [`present`](../../skills/present/) — HTML-отчёты по итогам наблюдения

## Типовой monitoring-флоу

1. Cron: каждое утро → `chat-archive` парсит последние 24 часа чатов
2. → выжимает 5-10 ключевых событий
3. → `learnings` записывает «error pattern» если кто-то жаловался на повторяющуюся проблему
4. → `present` собирает daily digest в HTML
5. Отправляет принцу в Telegram до 9:00

## Установка

```bash
cd ~/.claude/skills
git clone https://github.com/qwwiwi/agentos-skills-public.git agentos
for skill in chat-archive topic-monitor perplexity-research memory-audit \
  learnings agent-introspection transcript groq-voice markdown-new present; do
  cp -r agentos/skills/$skill ./
done
```
