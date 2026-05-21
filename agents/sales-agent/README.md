# Sales Agent

Делает квалификацию лидов, ресерч клиентов, подготовку follow-up'ов, разбор возражений.

## Что умеет

- Ресерч клиента по соцсетям и сайту перед звонком
- Анализ чатов и переписок
- Извлечение фактов из транскриптов созвонов
- Подготовка персонализированных follow-up'ов

> **Важно:** скиллы для CRM-флоу (`crm-workflow`, `qualification`, `objection-handling`, `follow-up`) пока в работе — войдут в публичную часть отдельным релизом. Сейчас sales-роль работает на универсальных research-скиллах.

## Скиллы

### Ресерч лида

- [`perplexity-research`](../../skills/perplexity-research/) — глубокий web research по компании и человеку
- [`twitter`](../../skills/twitter/) — чтение X/Twitter профиля клиента
- [`markdown-new`](../../skills/markdown-new/) — выжимка текста с сайта компании
- [`transcript`](../../skills/transcript/) — транскрипция созвона + извлечение ключевых поинтов

### Разбор переписок

- [`chat-archive`](../../skills/chat-archive/) — анализ архивов Telegram-чатов

### Подготовка материалов

- [`present`](../../skills/present/) — персональные HTML-предложения / коммерческие
- [`content-engine`](../../skills/content-engine/) — генерация follow-up writeups с TOV

## Типовой sales-флоу

1. Лид пришёл → `perplexity-research` по компании (отрасль, размер, последние новости)
2. + `twitter` по руководителю → понимаем тон коммуникации
3. + `markdown-new` по их сайту → находим продукт/цены/позиционирование
4. Созвон → `transcript` записи → извлекаем pain points + bant-сигналы
5. Follow-up → `content-engine` пишет персональное письмо
6. Если нужна презентация → `present` собирает HTML по нашему фирстилю

## Установка

```bash
cd ~/.claude/skills
git clone https://github.com/qwwiwi/agentos-skills-public.git agentos
for skill in perplexity-research twitter markdown-new transcript chat-archive present content-engine; do
  cp -r agentos/skills/$skill ./
done
```
