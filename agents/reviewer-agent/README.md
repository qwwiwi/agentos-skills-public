# Reviewer Agent

Делает code review, аудит решений, security review, red-team на проектируемые архитектуры. Не пишет код — критикует и предлагает альтернативы.

> Эта роль в нашей команде закреплена за Codex GPT-5.5 как сильнейшим критиком/архитектором. Opus справляется тоже, но Codex дешевле + специально хорош в audit/plan фазах.

## Что умеет

- Code review с поиском багов, race conditions, security holes
- Architecture review с проверкой против индустриальных стандартов
- Red team на новые архитектуры — поиск способов как их сломать
- Аудит существующих систем на debt и тёмные углы
- Самообучение через ленинги после каждого review

## Скиллы

### Code review

- [`cross-review`](../../skills/cross-review/) — двойное ревью двумя моделями параллельно, мердж findings

### Архитектура и API дизайн

- [`mcp-api-build`](../../skills/mcp-api-build/) — стандарты Google AIP / Microsoft Azure / Stripe / Anthropic MCP Spec для аудита API-проектов
- [`mcp-builder`](../../skills/mcp-builder/) — стандарты построения MCP-серверов

### Ресерч best practices

- [`perplexity-research`](../../skills/perplexity-research/) — поиск свежих best practices, CVE, инцидентов в exact-области

### Память и самообучение

- [`learnings`](../../skills/learnings/) — записать паттерн найденного бага после review (потом другие агенты не повторят)
- [`memory-audit`](../../skills/memory-audit/) — аудит того, что reviewer запоминает

### Презентация выводов

- [`present`](../../skills/present/) — HTML-отчёты с findings по severity

## Типовой reviewer-флоу

1. Coding-agent открыл PR → запрашивает review
2. Reviewer-agent читает diff + контекст файлов
3. Через `cross-review` запускает параллельно вторую модель — две пары глаз
4. Скрипт мерджит findings, помечает дивергенцию как риск
5. Reviewer пишет REVIEW.md с findings, severity-сортировка
6. Каждый critical/high бага → `learnings` записывает паттерн
7. Если архитектурное решение спорное → `present` собирает HTML с альтернативами и trade-off

## Принципы reviewer'а

- **Никогда не пишет production-код** — это работа coding-agent
- **Всегда даёт alternatives**, не только «это плохо»
- **Различает MUST / SHOULD / NICE** — не путает hard rule и стиль
- **Помнит свои прошлые findings** через learnings — не повторяет одно и то же

## Установка

```bash
cd ~/.claude/skills
git clone https://github.com/qwwiwi/agentos-skills-public.git agentos
for skill in cross-review mcp-api-build mcp-builder perplexity-research \
  learnings memory-audit present; do
  cp -r agentos/skills/$skill ./
done
```
