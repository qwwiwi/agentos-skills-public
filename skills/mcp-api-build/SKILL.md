---
name: mcp-api-build
description: "Design and build production REST APIs and MCP servers following industry standards (Google AIP, Microsoft Azure, Zalando, Stripe, Anthropic MCP Spec 2025-06-18). Use when: (1) designing new API endpoints from scratch, (2) building MCP server for an existing API, (3) converting REST endpoints to MCP tools/resources, (4) reviewing API architecture, (5) writing OpenAPI spec, (6) auditing API security and production readiness, (7) debugging API anti-patterns. Triggers: «build API», «design endpoints», «create MCP server», «MCP», «API architecture», «OpenAPI spec», «REST to MCP», «спроектируй API», «сделай MCP сервер», «антипаттерны API», «review API design»."
---

# MCP API Build

Design and build production APIs and MCP servers by corporate standards.

## When to Use

- Designing a new REST API from scratch
- Wrapping an existing REST API with MCP server
- Converting REST endpoints → MCP tools/resources/prompts
- Writing OpenAPI spec (API-first approach)
- Reviewing/auditing API architecture and anti-patterns
- Planning API security and production deployment

## Workflow

### Path A: Build REST API from scratch

```
1. Domain Model → 2. Resource Inventory → 3. OpenAPI Spec → 4. Implement → 5. Audit → 6. Deploy
```

1. **Domain Model**: Identify entities, relationships, consumers. Ask: who calls API? what problems does it solve? what tiers/permissions exist?
2. **Resource Inventory**: List resources + CRUD matrix. See [rest-api-standards.md](references/rest-api-standards.md) §Design Process Checklist
3. **OpenAPI Spec**: Write spec BEFORE code. See [openapi-first-process.md](references/openapi-first-process.md)
4. **Implement**: Code against contract. Any deviation = bug
5. **Audit**: Check anti-patterns. See [advanced-patterns.md](references/advanced-patterns.md) §Anti-Patterns
6. **Deploy**: Security + production checklist. See [security-production.md](references/security-production.md)

### Path B: Build MCP server for existing API

```
1. Audit REST API → 2. Map endpoints → 3. Write server → 4. Add advanced features → 5. Test → 6. Deploy
```

1. **Audit existing API**: List all endpoints, methods, params, responses
2. **Map to MCP primitives**: Use decision matrix in [rest-to-mcp-mapping.md](references/rest-to-mcp-mapping.md)
3. **Write MCP server**: Follow patterns in [mcp-server-patterns.md](references/mcp-server-patterns.md)
4. **Advanced features**: Progress notifications, elicitation, structured output. See [advanced-patterns.md](references/advanced-patterns.md) §Advanced MCP Patterns
5. **Test**: MCP Inspector + programmatic tests
6. **Deploy**: stdio (local) or Streamable HTTP (remote)

### Path C: Design both REST API + MCP together

Combined path. Design REST first (Path A steps 1-3), then layer MCP on top (Path B steps 2-6).

## Quick Reference: REST Design Rules

- **Plural nouns**: `/users`, `/events`, `/tickets`
- **HTTP methods = actions**: GET read, POST create, PATCH update, DELETE remove
- **No verbs in URL**: `POST /tickets` not `/createTicket`
- **Max 2 nesting levels**: `/users/{id}/orders` ok, deeper = flatten
- **snake_case JSON fields**: `created_at`, `user_id`
- **Consistent responses**: same shape for all lists, all errors
- **Paginate everything**: `limit` + `offset` or cursor
- **Version in URL**: `/v1/`
- **Idempotency keys for POST**: `Idempotency-Key: req_abc123`
- **ETag for caching/concurrency**: `If-Match`, `If-None-Match`
- **Health check**: `GET /health` always

Full reference: [rest-api-standards.md](references/rest-api-standards.md)

## Quick Reference: MCP Primitives

| Primitive | What | When | Control |
|-----------|------|------|---------|
| **Tool** | Action/function | Search, create, update, delete | LLM decides to call |
| **Resource** | Static data | Profile, config, counts | App/user loads into context |
| **Prompt** | Template | Analysis, summary, recommendation | User selects |

Decision: GET without params → Resource. GET with params or any write → Tool.

Full spec: [mcp-specification.md](references/mcp-specification.md)

## Quick Reference: MCP Tool Design

```
Name:        snake_case verb_noun (search_knowledge, create_ticket)
Description: What it does + what it returns + when to use (for LLM)
inputSchema: JSON Schema with description on every field, enums where possible
Output:      Structured JSON (structuredContent), not stringified text
Errors:      Return isError: true, not exceptions
Annotations: readOnlyHint, destructiveHint, idempotentHint
```

Max 10-15 tools per server. Group logically. Write comprehensive server instructions.

Full mapping guide: [rest-to-mcp-mapping.md](references/rest-to-mcp-mapping.md)

## Quick Reference: Advanced Features (2025-06-18+)

| Feature | When | Reference |
|---------|------|-----------|
| **Structured Output** | Tool returns typed JSON | [advanced-patterns.md](references/advanced-patterns.md) §Structured Tool Output |
| **Progress Notifications** | Long-running operations (>5s) | [advanced-patterns.md](references/advanced-patterns.md) §Progress Notifications |
| **Elicitation** | Confirm destructive actions, get user input | [advanced-patterns.md](references/advanced-patterns.md) §Elicitation |
| **Sampling** | Server needs LLM analysis | [advanced-patterns.md](references/advanced-patterns.md) §Sampling |
| **Resource Subscriptions** | Auto-update on data change | [advanced-patterns.md](references/advanced-patterns.md) §Resource Subscriptions |
| **Idempotency Keys** | Safe POST retries | [advanced-patterns.md](references/advanced-patterns.md) §Idempotency Keys |
| **ETag / Conditional** | Caching, optimistic concurrency | [advanced-patterns.md](references/advanced-patterns.md) §ETag |
| **Expand/Embed** | Avoid N+1 queries | [advanced-patterns.md](references/advanced-patterns.md) §Expand Pattern |

## References (load on demand)

| File | Content | When to load |
|------|---------|-------------|
| [rest-api-standards.md](references/rest-api-standards.md) | URL design, HTTP methods, responses, errors, auth, pagination, versioning | Designing REST API |
| [mcp-specification.md](references/mcp-specification.md) | MCP architecture, lifecycle, primitives, transports, auth | Building MCP server |
| [rest-to-mcp-mapping.md](references/rest-to-mcp-mapping.md) | Decision matrix, naming, tool descriptions, inputSchema, grouping | Converting REST → MCP |
| [openapi-first-process.md](references/openapi-first-process.md) | Domain modeling, resource inventory, OpenAPI YAML, review checklist | Writing OpenAPI spec |
| [mcp-server-patterns.md](references/mcp-server-patterns.md) | Python FastMCP, TypeScript SDK, REST wrapper, testing, deployment | Implementing MCP server |
| [security-production.md](references/security-production.md) | Auth, input validation, rate limits, MCP security, production checklist | Security audit, go-live |
| [advanced-patterns.md](references/advanced-patterns.md) | Idempotency, ETags, expand, webhooks, structured output, progress, elicitation, sampling, anti-patterns | Advanced features, debugging problems |

## Example: Production MCP Server (Python)

```python
import os
import httpx
from mcp.server.fastmcp import FastMCP

BASE_URL = os.getenv("API_BASE_URL", "https://api.myapp.com/v1")
API_KEY = os.getenv("API_KEY")
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

mcp = FastMCP("myapp", instructions="""
MyApp MCP server -- educational platform for AI practitioners.

## Tools
- search_knowledge: Find learning materials (lessons, skills, workshops)
- create_ticket: Report issues or request help
- get_event: Get event details with calendar link

## Guidelines
1. Search before listing (faster)
2. Check material tier before recommending
3. For problems, create a ticket
""")

async def _api(method: str, path: str, **kwargs) -> dict:
    """Internal API caller with timeout and error handling."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as c:
        r = await getattr(c, method)(path, headers=HEADERS, **kwargs)
        if r.status_code >= 400:
            return {"error": r.json().get("error", {"code": "unknown"})}
        return r.json()

@mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
async def search_knowledge(
    query: str,
    category: str | None = None,
    limit: int = 20
) -> dict:
    """Search knowledge base by keywords.
    Returns lessons, skills, usecases, workshops, guides.
    Use when user asks about learning materials or tutorials."""
    params = {"q": query, "limit": min(limit, 100)}
    if category:
        params["category"] = category
    return await _api("get", "/knowledge/search", params=params)

@mcp.tool(annotations={"destructiveHint": False, "idempotentHint": False})
async def create_ticket(subject: str, body: str) -> dict:
    """Create support ticket. Use when user reports a problem."""
    return await _api("post", "/support/tickets",
                      json={"subject": subject, "body": body})

@mcp.resource("myapp://profile/me")
async def get_profile() -> dict:
    """Current user profile and subscription tier."""
    return await _api("get", "/profile/me")

@mcp.resource("myapp://notifications/unread")
async def unread_count() -> dict:
    """Number of unread notifications."""
    return await _api("get", "/notifications/unread-count")
```

Run: `python server.py` | Test: `npx @modelcontextprotocol/inspector python server.py`
