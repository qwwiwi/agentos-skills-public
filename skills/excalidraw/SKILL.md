---
name: excalidraw
description: >
  Генерация Excalidraw-схем (.excalidraw v2) из JSON.
  Поддерживает pipeline, mindmap, flowchart, sequence, freeform.
  Цветовая палитра и формат по стандартам MCP Excalidraw.
  Экспорт файла для excalidraw.com.
user-invocable: true
metadata: {"openclaw":{"emoji":"","requires":{"bins":["python3"],"config":[]}}}
---

# Excalidraw Skill v2.0

## Когда использовать
- «нарисуй схему» / «визуализация» / «excalidraw»
- «майнд-карта» / «mind map»
- «pipeline схема» / «flowchart» / «sequence diagram»
- «архитектура» / «diagram» / «нарисуй»

## Типы диаграмм

| Тип | Описание |
|-----|----------|
| `pipeline` | Вертикальный flow по этапам со стрелками |
| `mindmap` | Радиальная карта от центра |
| `flowchart` | Произвольный граф: nodes + edges |
| `sequence` | UML sequence: actors + messages |
| `freeform` | Сырые Excalidraw elements (полный контроль) |

## Скрипт
`./scripts/excalidraw_gen.py`

### Входные данные
JSON через stdin или `--input schema.json`

### Выход
stdout (по умолчанию) или `--output result.excalidraw`

### Флаги
- `--dark` -- тёмная тема

## Стандарты визуализации (MCP Excalidraw)

### Шрифты
- `fontFamily: 1` (Hand-drawn)
- Body/labels: fontSize 18 (min 16)
- Stage headers: fontSize 20
- Titles: fontSize 28
- Secondary annotations: fontSize 14 (только если необходимо)
- НИКОГДА fontSize < 14

### Sizing
- Min shape: 120x60 для labeled rectangles
- Gaps: 20-30px между элементами
- Меньше крупных элементов лучше чем много мелких

### Камера (4:3 ratio обязательно)
| Размер | Width x Height | Когда |
|--------|---------------|-------|
| S | 400x300 | 2-3 элемента, close-up |
| M | 600x450 | Секция диаграммы |
| L | 800x600 | Стандарт (по умолчанию) |
| XL | 1200x900 | Большие диаграммы |
| XXL | 1600x1200 | Панорама сложных схем |

### Цвета
Полная палитра: `./references/color-palette.md`

Быстрый маппинг типов:
| Type | Fill | Stroke |
|------|------|--------|
| input | `#ffc9c9` | `#ef4444` |
| research | `#a5d8ff` | `#4a9eed` |
| analysis | `#d0bfff` | `#8b5cf6` |
| review | `#ffd8a8` | `#f59e0b` |
| final | `#b2f2bb` | `#22c55e` |
| storage | `#c3fae8` | `#06b6d4` |
| warning | `#fff3bf` | `#f59e0b` |
| metrics | `#eebefa` | `#ec4899` |

### Контраст текста
- На белом фоне: min цвет текста `#757575`
- На цветных fills: тёмные варианты (`#15803d`, не `#22c55e`)
- Белый текст: только на тёмных backgrounds

### Dark Mode
Включай `"dark": true` в JSON schema или `--dark` флаг.
Автоматически: тёмный фон, тёмные fills, светлый текст.

## Формат JSON по типам

### Pipeline
```json
{
  "title": "Pipeline название",
  "type": "pipeline",
  "dark": false,
  "stages": [
    {
      "label": "1. ЗАПРОС",
      "color": "input",
      "blocks": [{"text": "Новость\nПост"}]
    },
    {
      "label": "2. РЕСЁРЧ",
      "subtitle": "параллельно",
      "color": "research",
      "blocks": [
        {"text": "Grok\nВеб-поиск"},
        {"text": "Opus\nАнализ", "color": "analysis"}
      ]
    }
  ]
}
```

### Mindmap
```json
{
  "title": "Центральная тема",
  "type": "mindmap",
  "nodes": [
    {"text": "Ветка 1", "color": "research"},
    {"text": "Ветка 2", "color": "analysis"},
    {"text": "Ветка 3", "color": "success"}
  ]
}
```

### Flowchart
```json
{
  "title": "Architecture",
  "type": "flowchart",
  "nodes": [
    {"id": "api", "x": 0, "y": 0, "text": "API Server", "color": "analysis"},
    {"id": "db", "x": 0, "y": 200, "text": "PostgreSQL", "color": "storage"},
    {"id": "ui", "x": -300, "y": 0, "text": "React App", "color": "research"}
  ],
  "edges": [
    {"from": "ui", "to": "api", "label": "REST"},
    {"from": "api", "to": "db"}
  ]
}
```

### Sequence
```json
{
  "title": "Auth Flow",
  "type": "sequence",
  "actors": [
    {"id": "user", "name": "User"},
    {"id": "api", "name": "API"},
    {"id": "db", "name": "Database"}
  ],
  "messages": [
    {"from": "user", "to": "api", "label": "POST /login"},
    {"from": "api", "to": "db", "label": "SELECT user"},
    {"from": "db", "to": "api", "label": "user record", "response": true},
    {"from": "api", "to": "user", "label": "JWT token", "response": true}
  ]
}
```

### Freeform (raw elements)
```json
{
  "type": "freeform",
  "elements": [
    {"type":"cameraUpdate","width":800,"height":600,"x":0,"y":0},
    {"type":"rectangle","id":"b1","x":100,"y":100,"width":200,"height":80,
     "roundness":{"type":3},"backgroundColor":"#a5d8ff","fillStyle":"solid",
     "label":{"text":"Start","fontSize":20}}
  ]
}
```

## Команды

```bash
# Pipeline
echo '{"title":"Test","type":"pipeline","stages":[...]}' | python3 scripts/excalidraw_gen.py > out.excalidraw

# Dark mode
python3 scripts/excalidraw_gen.py --input schema.json --output result.excalidraw --dark

# Freeform
echo '{"type":"freeform","elements":[...]}' | python3 scripts/excalidraw_gen.py > out.excalidraw
```

## References
- `./references/color-palette.md` -- полная палитра цветов + dark mode
- `./references/element-format.md` -- формат JSON элементов, bindings, camera
- `./references/examples.md` -- примеры готовых диаграмм

## Нюансы
- Labeled shapes (`"label"` в rect/ellipse/diamond) экономят токены -- не нужен отдельный text element
- Arrow bindings: `fixedPoint` для точного присоединения к сторонам shape
- Drawing order = z-order: background -> shapes -> arrows
- cameraUpdate -- мощный инструмент, направляет внимание пользователя
- Emoji не рендерятся в шрифте Excalidraw -- используй текст
