# CTA Workshop — финальный пост треда

Каждый Threads-тред заканчивается CTA на воркшоп. Без CTA — это просто пост, без воронки.

## Базовый URL

```
https://<your-domain>/workshop
```

## UTM-параметры (обязательны)

```
?utm_source=threads&utm_medium=social&utm_campaign=workshop&utm_content=<slug>
```

Где `<slug>` — короткий идентификатор треда (например `cognee-vs-obsidian`, `mcp-memory`, `agent-graph`). Это нужно чтобы в аналитике видеть какой именно тред приносит трафик.

**Внутри Telegram-черновика для принца:** амперсанды экранировать как `&amp;`, иначе HTML-парсер ломается:

```
<your-domain>/workshop?utm_source=threads&amp;utm_medium=social&amp;utm_campaign=workshop&amp;utm_content=cognee-vs-obsidian
```

**В самом Threads:** ссылка вставляется обычными амперсандами (Threads не парсит HTML).

## Шаблоны CTA-поста (последний в треде)

### Вариант 1 — Прямой

```
Такие пайплайны (Cognee, MCP-память, агентные графы) разбираем на воркшопе «Запусти AI-агента за 3 дня».

3 дня практики, готовый агент к концу третьего дня.

<your-domain>/workshop?utm_source=threads&utm_medium=social&utm_campaign=workshop&utm_content=<slug>
```

### Вариант 2 — Через боль

```
Если узнал себя в этом треде — собираю на воркшоп «Запусти AI-агента за 3 дня».

Берём такие связки и упаковываем в работающий пайплайн. Без теории – сразу руками.

<your-domain>/workshop?utm_source=threads&utm_medium=social&utm_campaign=workshop&utm_content=<slug>
```

### Вариант 3 — Через результат

```
Хочешь свой агентный слой памяти, который сам индексирует и сам отвечает?

Делаем за 3 дня на воркшопе «Запусти AI-агента за 3 дня». К финалу — рабочий агент в твоём стеке.

<your-domain>/workshop?utm_source=threads&utm_medium=social&utm_campaign=workshop&utm_content=<slug>
```

## Что НЕ писать

- «Купи курс», «Скидка», «Только сегодня» — Threads режет инграмм за рекламные триггеры
- Цены, скидки, акции — это для Telegram/email, не для Threads
- ≥3 ссылок в одном посте — алгоритм режет охват
- «Подписывайся» в CTA — на воркшоп ведём, не на подписку

## Длина CTA-поста

≤500 символов. Если основной CTA-копи + ссылка не влезают — режем основной копи, ссылку не трогаем.

## Замер эффективности

UTM-параметры трекаются через:
- Yandex.Metrica на <your-domain> ()
- Signups table with utm_content in metadata
- Weekly review: which `utm_content` дал больше всего конверсий
