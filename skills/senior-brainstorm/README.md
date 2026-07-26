# Senior Brainstorm v5

Senior full-stack architect skill for Claude Code. Focused on **educational SaaS platforms** at the level of Teachable / Thinkific / Kajabi.

Provides decision frameworks, stage-aware stack recommendations, architecture patterns, AI/LLM integration, agent-native design, security threat modeling, testing strategies, and MCP integration guidance.

## When to use

**Triggers:** `/senior-brainstorm`, "brainstorm", "architecture", "how to build", "stack selection", "tech choice", "architectural decision", "design this", "senior brainstorm", "platform stack".

**Use for:**
- Greenfield EdTech platform design
- Re-architecture / migration planning
- Stack selection with compliance constraints (GDPR, SOC 2, PCI DSS, FERPA, COPPA)
- AI/LLM integration design (RAG, tutoring, guardrails)
- Build vs buy decisions for EdTech components
- LTI / SCORM / xAPI integration strategy

**NOT for:**
- Simple CRUD tasks
- Non-EdTech projects
- Single-framework questions without product context

## What you get

- **Decision Framework** — stage, team, budget, time-to-market, compliance filter
- **Agent Native checklist** — backend-for-agents, API-first, MCP integration, CLI tooling
- **Golden Question Bank** — structured discovery questions (business, technical, pedagogy, compliance)
- **Cost/Complexity Scoring** — quantitative gate before recommending advanced architecture
- **Adaptive Workflow** — small task / greenfield / re-architecture / incident flows
- **Knowledge Base** — 11 detailed reference docs (backend, frontend, devops, security, testing, architecture, MCP, AI/LLM, real-time, LTI, build-vs-buy)
- **Templates** — ADR, threat model, options matrix

## Install

```bash
git clone https://github.com/qwwiwi/senior-brainstorm-skill ~/.claude/skills/senior-brainstorm
```

Or use `skill-installer` if you have it configured.

## File structure

```
senior-brainstorm/
├── SKILL.md                        # Main skill definition
├── references/
│   ├── ai-llm.md                   # RAG, tutoring, vector DB selection, guardrails
│   ├── architecture.md             # Patterns, bounded contexts, progression
│   ├── build-vs-buy.md             # Component sourcing decisions
│   ├── devops.md                   # CI/CD, observability, deployment
│   ├── lti.md                      # LTI 1.3, OneRoster, SCORM, xAPI
│   ├── mcp.md                      # MCP server design
│   ├── realtime.md                 # WebSocket, CRDT, WebRTC, live collab
│   ├── security.md                 # Threat modeling, encryption, compliance
│   ├── stacks-backend.md           # API design, auth, payments, multi-tenancy
│   ├── stacks-frontend.md          # Frontend stack, SSR, PWA
│   └── testing.md                  # Test strategy, CI patterns, EdTech matrix
└── templates/
    ├── adr-template.md             # Architecture Decision Record
    ├── options-matrix.md           # Compare 2+ approaches
    └── threat-model.md             # Security review
```

## Core principle — Agent Native

Every system must be agent-first: **if an agent cannot operate it programmatically, the architecture is wrong.**

- Backend for agents (API, MCP, tools) — frontend for humans
- API-first design — OpenAPI contract before UI
- CLI for every admin action — no browser-only features
- Webhook-driven workflows — not polling
- API keys + scoped tokens — not session-cookie-only auth

Full checklist in `SKILL.md`.

## Workflow

### Greenfield project
1. **Discovery** — Golden Question Bank
2. **Domain modeling** — bounded contexts, entities, events
3. **Architecture options** — 2-4 approaches with tradeoffs + cost/complexity scoring + Build vs Buy
4. **Design document** — stack, schema, API, infra
5. **Approval gate**
6. **Implementation plan** — phases, tickets, dependencies

### Re-architecture / Migration
1. Audit current state
2. Target architecture with Agent Native review
3. Migration plan (strangler fig, parallel run)
4. Risk register
5. Approval gate

## License

MIT — see `LICENSE`.
