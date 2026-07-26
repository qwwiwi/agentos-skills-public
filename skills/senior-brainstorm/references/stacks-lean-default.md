---
last_verified: 2026-04-20
applies_to: [early-stage, growth]
confidence: high
source: "Lean default stack"
---

# Default Stack for New Non-SSR Projects (Lean)

**Track:** Lean — an opinionated default stack for non-SSR projects.

Opinionated default for **greenfield** projects where SSR / SEO is NOT a hard requirement: internal dashboards, admin panels, SPA utilities, authenticated-only web apps, desktop apps, mobile apps, APIs, Telegram bots with web UIs. For content-heavy SEO-dependent projects (course catalogs, marketing sites, blogs), see `stacks-frontend.md` Next.js section instead.

## When to apply

- New project, no legacy stack to inherit
- SSR is NOT required (no SEO, no OG tags, no SSG for crawlers)
- Team wants minimal build-step complexity
- Speed of iteration matters more than framework ecosystem

## When NOT to apply

- Project needs SEO (marketing site, public content, blog) — use Next.js
- Project needs SSR (personalized server-rendered dashboards, low TTFB) — use Next.js
- Existing codebase on different stack — inherit it, do not force migration
- Team has zero Bun experience and deadline is tight — Node is fine

## Stack

| Layer | Default | Notes |
|---|---|---|
| Backend | **TypeScript + Hono + Bun** | Fastest TS runtime, native TS, no build step |
| Mobile (iOS/Android) | **Expo + React Native** | App Store/Google Play builds in one command, Expo Push out of the box |
| Web frontend (SPA) | **Client React + Vite 8** | No SSR, no Next.js. Fast HMR, simple mental model |
| Web frontend (static site) | **Vite 8 SSG** | SSG out of the box in Vite 8 |
| Desktop | **Electron (TypeScript + React)** | Same backend stack as web |
| Database | **Managed Postgres** (DO / fly.io / Supabase / Neon) | Zero ops, point-in-time recovery, managed backups |
| ORM | **Prisma** (default) or **Drizzle** (worth trying) | — |
| Storage | **Tigris** (CDN included) or native cloud (DO Spaces, Fly storage) | Fly has Tigris partner integration |
| 152-ФЗ (RU data residency) | **Yandex Cloud**: serverless containers + Managed Postgres + S3 | Only when RU data-residency is a hard constraint |
| Infra experiment | **Cloudflare** (Workers, D1, R2) | Optional, discuss with user |

## Scale Assumptions

- **Initial target: 10K users.** Do NOT architect for 10M users upfront.
- **No microservices, no Kubernetes** at this stage. Single service + managed DB + managed storage.
- **Async inter-instance communication, sharding, event buses** — introduce only when 10K cap is reached.

## Rationale

- **Bun + Hono:** fastest TypeScript runtime, minimal boilerplate, native TS without build step. Hono is ~2KB, fastest TS web framework in benchmarks.
- **Expo:** App Store / Google Play builds in one command (`eas build`), Expo Push for notifications out of the box, OTA updates via EAS Update.
- **Vite 8 over Next.js:** no server-render coupling, simpler mental model, fast HMR, SSG available when needed. Avoids App Router learning curve.
- **Managed Postgres:** zero ops, point-in-time recovery, managed backups — scales to 10K users without tuning.
- **10K cap:** premature scaling is the #1 architecture mistake — simple scales further than most teams think.

## Conflicts to Surface During Brainstorming

If the user requests something that conflicts with this default, call it out and let them choose:

- **«Next.js for a new SPA»** — ask why: SSR? SEO? ISR? App Router features? If none apply, Lean default is Vite.
- **«Microservices from day one»** — push back. Recommend modular monolith until 10K users or team > 10.
- **«Self-hosted Postgres»** — push back. Recommend managed unless there is a hard constraint (compliance, cost at scale).
- **«Kubernetes for a new project»** — push back. Recommend single-service deploy (Fly, DO App Platform, Railway).
- **«Node.js instead of Bun»** — acceptable fallback if team has zero Bun experience, but lose the TS-native advantage.

## Decision Matrix: Lean Default vs Next.js Stack

| Project type | Recommended |
|---|---|
| EdTech platform with course catalog (SEO matters) | Next.js (see `stacks-frontend.md`) |
| Marketing site, blog, public content | Next.js App Router or Astro |
| Internal admin dashboard (auth-gated) | **Lean: Vite + Hono** |
| SPA tool, calculator, utility | **Lean: Vite + Hono** |
| Mobile app (iOS+Android) | **Lean: Expo React Native** |
| Desktop app (cross-platform) | **Lean: Electron + TS + React** |
| Bot control panel, agent UI, internal tool | **Lean: Vite + Hono** |
| Static documentation site | **Lean: Vite SSG** or Docusaurus/Nextra |
