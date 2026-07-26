---
last_verified: 2026-04-15
applies_to: [early-stage, growth, scale]
confidence: high
---

# Frontend

> **Before reading:** if the project is **non-SSR** (internal dashboard, SPA, mobile, desktop, bot UI, no SEO), prefer the **Lean default stack** in `stacks-lean-default.md` (Vite + Hono + Bun + Expo). This document covers the **EdTech SaaS / SSR track** (Next.js) — use it when SEO or server rendering is a hard requirement (course catalogs, public content, marketing pages).

## When to use this (Next.js) track

- Public content needs Google indexing (course catalogs, blog, marketing)
- Server-rendered personalization with low TTFB
- ISR / streaming SSR for fresh content
- Existing Next.js codebase

## When to use Lean track instead

- Internal / authenticated-only tools
- Mobile app (Expo)
- Desktop app (Electron)
- SPA utilities, admin panels, bot control panels

## Core Stack

- **Next.js 16** (App Router, Server Components, Partial Prerendering)
- **React 19**, TypeScript strict
- **Tailwind CSS v4** (новая модель конфигурации, CSS-first)
- **shadcn/ui** (компоненты)

## Data & State

- **TanStack Query** (React Query) -- серверный стейт, кэш, оптимистичные обновления
- **Server Actions** -- мутации из Server Components
- **Zustand** -- клиентский стейт (если нужен)
- Cache invalidation через `revalidatePath` / `revalidateTag`

## Media & UX

- **Video.js 8.7+** / Plyr (HLS/DASH streaming)
- **Tiptap** / Lexical -- rich text editor для создания курсов
- **React DnD** -- course builder drag-n-drop
- **Recharts** -- аналитика и дашборды
- Image optimization: `next/image`, lazy loading, poster frames для видео

## Forms

- **React Hook Form** + **Zod** (schema reuse между frontend и backend)
- Async validation, optimistic UI, autosave

## Mobile

- **React Native / Expo SDK 55** -- только если нужно нативное приложение
- PWA как default для мобильного доступа (проще, дешевле)

## Accessibility & i18n

- WCAG 2.1 AA минимум
- `next-intl` для i18n/l10n
- Semantic HTML, ARIA, keyboard navigation

## Frontend Observability

- **Web Vitals** (LCP, CLS, INP) через `next/web-vitals`
- Session replay: PostHog / LogRocket (с policy по PII)
- Error grouping: Sentry frontend SDK
- Bundle budgets: `bundlewatch` в CI

## Decision Matrix

| Сценарий | Рекомендация |
|----------|-------------|
| Web-only продукт | Next.js + PWA |
| Нужно нативное приложение | Next.js + Expo SDK 55 |
| Admin-heavy dashboard | Next.js + shadcn/ui + TanStack Table |
| Content-heavy (курсы) | Next.js + Tiptap + Video.js |
