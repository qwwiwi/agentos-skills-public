---
name: cross-review
version: 1.0.0
description: Cross-review PRs in team repos. Use when reviewing PRs from other agents, creating PRs that need cross-review, or checking change levels and merge rules.
---

# Cross-Review

Ревью PR в монорепо `jasonqween/team-constitution`.

## Cross-review правило

- Все PR Иллидана -> ревьюю я (Тралл)
- Все мои PR -> ревьюит Иллидан
- Никто не одобряет свой PR
- L3 (конституция) -> merge только Вождь

## Change Levels

| Level | Описание | Review | Merge |
|-------|----------|--------|-------|
| L0 | Typo, docs | Любой | Reviewer |
| L1 | Скрипты, конфиги, AGENTS.md, скиллы | Cross-reviewer | Reviewer |
| L2 | Deploy, auth, CI, multi-server | Cross-reviewer + CI | Reviewer |
| L3 | Конституция, новый/удаление агента | Cross-reviewer + Вождь | Вождь |

## Модели для review

- Обычный: Codex + Opus (оба OAuth $0)
- HIGH risk (P0/P1 баги, security, multi-server, финансовый код): + Gemini (Triple Review)

## Как делать review

1. `gh api` -- достать diff, файлы
2. Определить Change Level (L0-L3)
3. Проверить: логика, безопасность, стиль, тесты, breaking changes
4. APPROVE / REQUEST_CHANGES / COMMENT (с обоснованием)
5. Merge если APPROVE + CI green + не L3

## Раскатка после merge

```bash
# Все 3 сервера
cd /home/openclaw/.openclaw/constitution && git checkout main && git pull origin main
ssh root@100.107.104.91 'cd /home/openclaw/.openclaw/constitution && git pull origin main'
ssh root@100.115.122.16 'cd /home/openclaw/.openclaw/constitution && git pull origin main'
```
