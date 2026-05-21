# Marketing Agent

Делает контент для соцсетей, посты, рилсы, YouTube long-form, треды для Threads и X, AI-генерацию изображений и видео, графики и инфографику.

## Что умеет

- Писать посты с учётом tone of voice
- Делать сценарии рилсов в 5 форматах
- Готовить сценарии YouTube long-form
- Генерировать визуал через Higgsfield (Soul ID персонаж, продуктовая съёмка, карточки)
- Анализировать тренды конкурентов
- Делать инфографику и графики
- HTML-презентации в фирменном стиле

## Скиллы

### Создание контента

- [`content-engine`](../../skills/content-engine/) — TOV-aware двигатель контента, главный для постов
- [`instagram-superpower`](../../skills/instagram-superpower/) — посты и карусели для Instagram
- [`reels`](../../skills/reels/) — сценарии Reels в 5 форматах
- [`youtube-producer`](../../skills/youtube-producer/) — YouTube long-form
- [`threads-content`](../../skills/threads-content/) — контент для Threads
- [`twitter`](../../skills/twitter/) — чтение X/Twitter (для ресерча) + создание тредов

### AI-генерация

- [`higgsfield-generate`](../../skills/higgsfield-generate/) — генерация в Higgsfield
- [`higgsfield-soul-id`](../../skills/higgsfield-soul-id/) — свой персонаж через Soul ID
- [`higgsfield-product-photoshoot`](../../skills/higgsfield-product-photoshoot/) — продуктовая съёмка
- [`higgsfield-marketplace-cards`](../../skills/higgsfield-marketplace-cards/) — карточки для маркетплейсов

### Ресерч и сбор

- [`perplexity-research`](../../skills/perplexity-research/) — web research через Sonar API
- [`topic-monitor`](../../skills/topic-monitor/) — регулярный мониторинг темы
- [`transcript`](../../skills/transcript/) — транскрибация подкастов/видео конкурентов
- [`markdown-new`](../../skills/markdown-new/) — извлечение текста из URL

### Визуализация и презентации

- [`present`](../../skills/present/) — HTML-презентации в фирменном стиле
- [`datawrapper`](../../skills/datawrapper/) — графики и инфографика
- [`excalidraw`](../../skills/excalidraw/) — диаграммы

## Установка

```bash
cd ~/.claude/skills
git clone https://github.com/qwwiwi/agentos-skills-public.git agentos
for skill in content-engine instagram-superpower reels youtube-producer threads-content twitter \
  higgsfield-generate higgsfield-soul-id higgsfield-product-photoshoot higgsfield-marketplace-cards \
  perplexity-research topic-monitor transcript markdown-new present datawrapper excalidraw; do
  cp -r agentos/skills/$skill ./
done
```

## Что НЕ должен делать marketing-agent

- Не пишет код продакшен-систем
- Не деплоит на серверы
- Не лезет в инфраструктуру
- Не делает security review

Для этого есть [coding-agent](../coding-agent/) и [reviewer-agent](../reviewer-agent/).
