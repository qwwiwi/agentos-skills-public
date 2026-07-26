---
name: senior-brainstorm
description: >
  Senior full-stack architect for educational SaaS platforms (Teachable/Thinkific/Kajabi level).
  Provides decision frameworks, stage-aware stack recommendations, architecture patterns,
  AI/LLM integration, agent-native design, security threat modeling, testing strategies,
  and MCP integration guidance.
  Triggers: /senior-brainstorm, "brainstorm", "architecture", "how to build",
  "stack selection", "tech choice", "architectural decision", "design this",
  "senior brainstorm", "platform stack".
  NOT for: simple CRUD tasks, non-EdTech projects, single-framework questions without product context.
---

# Senior Brainstorm v6

## Scope

Architecture design for educational SaaS platforms: stack selection, feature brainstorm,
decision review, AI/LLM integration, agent-native system design.

## Non-goals

- Simple CRUD tasks without architectural questions
- Tasks outside educational SaaS
- Single-framework questions without product context

## Decision Framework

Every decision passes through this filter:

1. **Stage** -- MVP, growth, scale, enterprise
2. **Team** -- 1-3, 4-10, 10+
3. **Budget** -- bootstrap, funded, enterprise
4. **Time-to-market** -- week, month, quarter
5. **Compliance** -- none, GDPR, SOC 2, PCI DSS, FERPA, COPPA

### Compliance Quick Reference

| Standard | Scope | Key Requirements | Trigger |
|----------|-------|-----------------|---------|
| GDPR | EU users' personal data | Consent, right to erasure, DPA, breach notification 72h | Any EU user |
| SOC 2 | Service org controls | Trust principles (security, availability, etc.), annual audit | Enterprise clients |
| PCI DSS | Payment card data | Tokenization, network segmentation, quarterly scans | Direct card processing |
| FERPA | US student education records | Consent transfers at 18 OR postsecondary enrollment; directory info opt-out; audit trail | K-12 or university data |
| COPPA | US children <13 | Verifiable parental consent (schools can consent in educational contexts); data minimization; no behavioral ads; operator carries compliance responsibility | Users under 13 |

**FERPA notes:** Rights transfer to the student at age 18 OR upon enrollment in
postsecondary education (whichever comes first), not solely based on age. Multiple
non-consent disclosure exceptions exist: directory information, legitimate educational
interest, health/safety emergencies, judicial order, and others (see 34 CFR Part 99).

**COPPA notes:** In educational contexts, schools may consent on behalf of students
under 13, but the operator (your platform) still carries compliance responsibility
for data handling, retention limits, and parental access rights.

When FERPA/COPPA applies: implement age-gating, parental consent flows, and audit
logging for all data access. Separate data stores for minors is an optional isolation
pattern (not a legal requirement) that simplifies compliance auditing and data
retention enforcement.

## Default Principles

- Start simple -- modular monolith, not microservices
- Optimize for reversibility -- easy to roll back decisions
- Avoid premature distribution -- do not split until it hurts
- Measure before scaling -- data, not intuition

## Agent Native Architecture (Core Principle)

**Every system must be agent-first: if an agent cannot operate it programmatically,
the architecture is wrong.**

This is not an afterthought -- it is a foundational design constraint equal in weight
to security and scalability.

### Principles

1. **Backend is for agents. Frontend is for humans.** Agents interact through APIs,
   tools, MCP -- never through UI. No feature should exist only behind a browser.
2. **API-first design.** Every capability exposed as a versioned, documented API endpoint
   before any UI is built. OpenAPI spec is the contract.
3. **MCP server integration (recommended).** As the system matures, expose MCP servers
   for agent discovery and tool use. At MVP stage, a well-designed REST API is sufficient;
   MCP can be added incrementally as the agent ecosystem grows.
4. **CLI tooling.** Every admin/ops action available as a CLI command. If you need a
   dashboard to do it, the architecture is incomplete.
5. **Webhook-driven workflows.** Events flow through webhooks/event bus, not polling.
   Agents subscribe to events and react autonomously.
6. **Programmatic admin interfaces.** User management, content moderation, analytics --
   all accessible via authenticated API. Admin panels are convenience layers, not gates.

### Patterns

| Pattern | Implementation | Anti-pattern |
|---------|---------------|-------------|
| API-first | OpenAPI spec -> codegen -> UI | UI-first, API bolted on |
| MCP integration | MCP server per bounded context | Monolithic API with no discovery |
| Event-driven | Webhooks + event bus (NATS, Redis Streams) | Polling loops, cron-based sync |
| CLI admin | Click/Typer CLI wrapping same service layer | Admin-only web panel |
| Auth for agents | API keys + scoped tokens (not session cookies) | OAuth browser flow only |
| Observability | Structured logs + trace IDs queryable via API | Dashboard-only metrics |

### Checklist (Gate: before approving any architecture)

- [ ] Can an agent create a user without a browser?
- [ ] Can an agent publish/unpublish content via API?
- [ ] Can an agent query analytics programmatically?
- [ ] Can an agent trigger payments/refunds via API?
- [ ] Are all admin actions available without UI?
- [ ] Does the system expose MCP server(s)? (recommended, not required at MVP)
- [ ] Are events published to a webhook/event bus?

## Default Stack for New Projects (Opinionated)

For **greenfield** projects without legacy stack, start with opinionated defaults rather than open-ended stack selection. This reduces decision fatigue and produces consistent, maintainable systems.

**Three default tracks — choose by team strength, SEO/SSR requirement, and AI/data-heaviness:**

### Track A: Lean Default (non-SSR projects)

Use for internal dashboards, admin panels, SPAs, mobile apps, desktop apps, bot control panels, APIs.

- Backend: **TypeScript + Hono + Bun**
- Frontend (SPA): **Client React + Vite 8** (no SSR, no Next.js)
- Frontend (static): **Vite 8 SSG**
- Mobile: **Expo + React Native**
- Desktop: **Electron (TS + React)**
- DB: **Managed Postgres** (DO / fly.io / Supabase / Neon) + **Prisma**
- Storage: **Tigris** or native cloud

Full details: `references/stacks-lean-default.md`.

### Track B: EdTech SaaS (SSR/SEO required)

Use for course platforms, marketing sites, content-heavy public pages.

- Frontend: **Next.js 16** (App Router) — see `references/stacks-frontend.md`
- Backend: **Node.js 22 + Fastify 5** — see `references/stacks-backend.md`
- DB: **Postgres** (managed) + Redis for cache/queues
- Auth: **Clerk / Auth0 / NextAuth** depending on enterprise needs

### Track C: Python + Supabase (AI/bots/data)

Use for Telegram bots with admin, AI/RAG projects, data-heavy backends, teams stronger in Python.

- Backend: **Python 3.12 + FastAPI 0.115+** — see `references/stacks-python-supabase.md`
- Bot framework: **aiogram 3.x** or python-telegram-bot v21+
- BaaS: **Supabase** (Postgres + Auth + Storage + Realtime + Edge Functions)
- Frontend: **Next.js 16** (App Router) или **Vite + React**
- ORM: **SQLAlchemy 2.x async** (или SQLModel) с **asyncpg**

For data layer choice across all tracks (Supabase vs Yandex Cloud vs self-hosted), see `references/stacks-data-layer.md`.

### Choosing Between Tracks

| Ask | Track |
|---|---|
| Does public content need to be indexed by Google? | B |
| Is there a course catalog / blog / marketing page? | B |
| Telegram bot + admin panel? | **C** |
| AI/RAG with LLM integration? | **C** |
| Data/ML processing in backend? | **C** |
| Internal authenticated-only tool? | **A** |
| Mobile app (Expo)? | **A** |
| Desktop app (Electron)? | **A** |
| Bot control panel or agent UI (no Python ML)? | **A** |
| 152-ФЗ (RU data residency) required? | **C** + Yandex Cloud (see `stacks-data-layer.md`) |

**Scale defaults for all tracks:** target 10K users initially. No microservices, no Kubernetes before 10K. Managed DB, managed storage, single service.

## AI/LLM Integration Architecture

RAG pipelines, AI tutoring patterns, prompt observability, guardrails, vector DB selection.
-> See `references/ai-llm.md` for detailed options, tables, and selection guidance.

## Real-Time Collaboration Patterns

WebSocket, CRDT, WebRTC, SSE, Liveblocks -- when to add real-time and how to scale it.
-> See `references/realtime.md` for technology options, architecture patterns, and scaling.

## LTI (Learning Tools Interoperability)

LMS integration via LTI 1.3/Advantage, OneRoster/SIS sync, SCORM/xAPI/cmi5 standards.
-> See `references/lti.md` for versions, implementation checklist, and content packaging.

## Build vs Buy Decision Matrix

Component sourcing decisions for EdTech: scoring matrix, decision rules, common SaaS options.
-> See `references/build-vs-buy.md` for the full matrix and buy options table.

## Golden Question Bank (Discovery Phase)

Structured questions for the Discovery phase. Select relevant categories based on project scope.

### Business

1. What is the primary revenue model? (subscription, one-time, cohort-based, B2B licensing)
2. Target user count at launch? In 12 months?
3. Who are the end users? (self-learners, K-12 students, corporate employees, university)
4. What is the competitive differentiator vs Teachable/Udemy/Coursera?
5. Is B2B (selling to institutions) in scope? Timeline?
6. What is the content creation workflow? (solo instructor, team, UGC)
7. Budget for infrastructure? Monthly ceiling?
8. Existing audience/distribution channel?

### Technical

1. Existing codebase/tech stack? Migration constraints?
2. Team size and expertise? (frontend, backend, DevOps, ML)
3. Expected content types? (video, text, interactive, code exercises, quizzes)
4. Integration requirements? (LMS via LTI, CRM, payment providers, analytics)
5. Mobile app needed? Timeline? (responsive web, PWA, native)
6. Expected concurrent users during peak? (live events, launches)
7. Data residency requirements? (EU, US, specific country)
8. Existing infrastructure? (cloud provider, CI/CD, monitoring)

### Pedagogy

1. What learning model? (self-paced, cohort, live, blended)
2. Assessment types? (quizzes, projects, peer review, AI-graded)
3. Certification/credentialing needed? (certificates, badges, transcripts)
4. Progress tracking granularity? (course, module, lesson, activity)
5. Adaptive learning or fixed curriculum?
6. Instructor-student interaction model? (forum, chat, 1:1, office hours)
7. Content versioning? (update in place, or preserve student's enrolled version)
8. Accessibility requirements? (WCAG level, screen reader, captions)

### Compliance

1. User age range? (adults only, 13+, under 13 -- triggers COPPA)
2. Geographic scope? (US -- FERPA, EU -- GDPR, both)
3. Handling student education records from institutions? (FERPA)
4. Payment card data handling? (PCI DSS scope)
5. Data retention policy requirements?
6. Right to deletion / data portability needed?
7. Audit trail requirements? (who accessed what, when)
8. Third-party data processor agreements needed?

## Deliverables

- Discovery questions (context + constraints) -- use Golden Question Bank
- Options matrix (2-3 approaches with tradeoffs)
- ADR (Architecture Decision Record) -- template: `templates/adr-template.md`
- Phased implementation plan
- Risk register

## EdTech Domain

Video delivery, entitlements, instructor workflows, cohort/live learning, progress tracking,
certificates, content moderation, analytics (completion rates, engagement), AI tutoring,
LTI integration, real-time collaboration, agent-operated admin workflows.

## Knowledge Base

Detailed reference for each domain. Load only the relevant file:

| Domain | File | When to read |
|--------|------|-------------|
| Track A (Lean) | `references/stacks-lean-default.md` | Opinionated default for non-SSR projects (Bun+Hono+Vite+Expo). |
| Track B (Frontend) | `references/stacks-frontend.md` | Next.js SSR/SEO track — stack selection, components, data fetching, mobile strategy |
| Track B (Backend) | `references/stacks-backend.md` | Node+Fastify track — API design, auth, payments, domain model, multi-tenancy, ORM choice |
| Track C (Python+Supabase) | `references/stacks-python-supabase.md` | FastAPI + aiogram + Supabase track — bots, AI/RAG, data-heavy backends, 152-ФЗ via Yandex |
| Data Layer | `references/stacks-data-layer.md` | Supabase vs Yandex Cloud vs self-hosted Postgres — pricing, lock-in, residency, edge vs containers |
| DevOps | `references/devops.md` | Deployment, CI/CD, observability, environments, backup/DR |
| Security | `references/security.md` | Threat modeling, auth hardening, encryption, compliance, incident response |
| Testing | `references/testing.md` | Test strategy, tools, EdTech test matrix, CI patterns, failure testing |
| Architecture | `references/architecture.md` | Patterns, progression, bounded contexts, infrastructure decisions |
| MCP | `references/mcp.md` | MCP vs API, server selection, security model, bounded workflows |
| AI/LLM | `references/ai-llm.md` | RAG pipelines, tutoring patterns, vector DB selection, guardrails |
| Real-Time | `references/realtime.md` | WebSocket, CRDT, WebRTC, live collaboration |
| LTI/Standards | `references/lti.md` | LMS integration, LTI 1.3/Advantage, OneRoster, SCORM/xAPI |
| Build vs Buy | `references/build-vs-buy.md` | Component sourcing decisions, EdTech SaaS options |

## Templates

| Template | File | When to use |
|----------|------|------------|
| ADR | `templates/adr-template.md` | After selecting an architectural approach |
| Threat Model | `templates/threat-model.md` | At project start or security review |
| Options Matrix | `templates/options-matrix.md` | When comparing 2+ approaches |

## Adaptive Workflow

### Small task (< 1 day)
1. Context -> 2. Decision -> 3. ADR -> done

### Greenfield project
1. **Discovery** -- constraints, success criteria, budget, timeline.
   Use Golden Question Bank (select relevant categories).
2. **Domain modeling** -- bounded contexts, entities, events. Read `references/architecture.md`
3. **Architecture options** -- 2-4 approaches with tradeoffs, cost/complexity scoring.
   Apply Agent Native checklist. Run Build vs Buy matrix for each component.
4. **Design document** -- stack, DB schema, API, infra. Read relevant `references/stacks-*.md`
5. **Gate** -- user approves or corrects
6. **Implementation plan** -- phases, tickets, dependencies

### Re-architecture / Migration
1. Audit current state (bottlenecks, tech debt, risks)
2. Target architecture (apply Agent Native principles)
3. Migration plan (strangler fig, parallel run, data migration)
4. Risk register
5. Gate: approval

### Incident / Audit
1. Investigation (logs, traces, root cause)
2. Immediate fix
3. Post-mortem + systemic fix
4. Prevention (monitoring, tests, runbook)

## Cost/Complexity Scoring

Before recommending advanced architecture:

| Criterion | Simple (1) | Medium (2) | Complex (3) |
|-----------|-----------|------------|-------------|
| Services | 1-2 | 3-5 | 6+ |
| Team | 1-3 | 4-10 | 10+ |
| Data | Single DB | Read replicas | Multi-DB, CQRS |
| Deployment | Single | 2-3 pipelines | K8s + mesh |
| AI/LLM | No AI or basic API calls | RAG pipeline, single model | Multi-model, fine-tuning, evals |
| Real-time | None or SSE | WebSocket chat/presence | CRDT editing + WebRTC |

Score < 6: modular monolith. Score 6-10: extract on pressure. Score > 10: service-oriented.

## Artifacts per Stage

- Discovery: structured questions (from Golden Question Bank), constraints list
- Options: tradeoff matrix, cost/complexity scores, Build vs Buy matrix
  (use `templates/options-matrix.md`)
- Decision: ADR (use `templates/adr-template.md`)
- Plan: phased roadmap with milestones
- Risk: assumptions log, decision log, open questions

## Source Discipline

Authoritative sources (official docs, RFC, OWASP) for recommendations. Blog posts for
supporting context. Community posts (DEV.to, reels) only for discovery, never as basis
for recommendations.
