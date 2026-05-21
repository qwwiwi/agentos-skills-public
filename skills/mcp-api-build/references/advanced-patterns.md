# Advanced Patterns & Anti-Patterns

Patterns from production APIs (Stripe, GitHub, Supabase) and MCP spec 2025-06-18+.

## Advanced REST Patterns

### Idempotency Keys (Stripe pattern)

Client sends unique key with POST requests. Server deduplicates:
```
POST /payments
Idempotency-Key: req_abc123
Content-Type: application/json

{"amount": 1000, "currency": "usd"}
```

Server behavior:
- First call: process normally, store result keyed by idempotency key
- Retry with same key: return stored result without re-processing
- Different body with same key: return 422 Conflict

Implementation:
```python
@app.post("/payments")
async def create_payment(request: Request):
    idem_key = request.headers.get("Idempotency-Key")
    if idem_key:
        cached = await redis.get(f"idem:{idem_key}")
        if cached:
            return JSONResponse(json.loads(cached))
    
    result = await process_payment(request)
    
    if idem_key:
        await redis.setex(f"idem:{idem_key}", 86400, json.dumps(result))
    return result
```

### ETag / Conditional Requests

Prevent lost updates and enable caching:
```
# First request
GET /profile/me
→ ETag: "abc123"

# Conditional update (optimistic concurrency)
PATCH /profile/me
If-Match: "abc123"
→ 200 OK (or 412 Precondition Failed if changed)

# Conditional read (caching)
GET /profile/me
If-None-Match: "abc123"
→ 304 Not Modified (save bandwidth)
```

### Expand/Embed Pattern (Stripe)

Avoid N+1 by letting client request related data:
```
GET /orders/123?expand=customer,items
```

Response includes expanded objects inline instead of just IDs.

Alternative: `?include=customer,items` (JSON:API style)

### Sparse Fields

Client requests only needed fields:
```
GET /knowledge/list?fields=id,title,category
```

Reduces payload size. Useful for mobile and AI agents.

### Webhooks

Server pushes events to client URL:
```json
POST https://client.com/webhooks
{
  "event": "ticket.created",
  "data": { "id": 42, "subject": "Help needed" },
  "timestamp": "2026-03-29T15:00:00Z",
  "signature": "sha256=abc123..."
}
```

Security: HMAC signature verification, retry with backoff, event deduplication.

### Health Check Endpoint

```
GET /health → 200
{
  "status": "healthy",
  "version": "1.2.3",
  "uptime": 86400,
  "checks": {
    "database": "ok",
    "cache": "ok",
    "external_api": "degraded"
  }
}
```

### CORS Configuration

```python
# Allow specific origins, not *
CORS_ORIGINS = ["https://app.myapp.com", "https://admin.myapp.com"]
CORS_METHODS = ["GET", "POST", "PATCH", "DELETE"]
CORS_HEADERS = ["Authorization", "Content-Type", "Idempotency-Key"]
```

---

## Advanced MCP Patterns (Spec 2025-06-18+)

### Structured Tool Output (outputSchema)

Tools can declare an outputSchema for typed, parseable results:
```python
@mcp.tool(output_schema={
    "type": "object",
    "properties": {
        "items": {"type": "array"},
        "total": {"type": "integer"},
        "has_more": {"type": "boolean"}
    }
})
async def search_knowledge(query: str) -> dict:
    """Search knowledge base."""
    result = await _api("get", "/knowledge/search", params={"q": query})
    return result  # Goes to structuredContent
```

LLM receives structured JSON, not stringified text. Easier to parse.

### Progress Notifications

For long-running tools (batch operations, data exports):
```python
@mcp.tool()
async def export_all_knowledge(format: str = "json") -> dict:
    """Export all knowledge items. May take 30+ seconds."""
    items = []
    total = await get_total_count()
    
    for i, batch in enumerate(get_batches()):
        items.extend(batch)
        # Send progress notification
        await mcp.notify_progress(
            progress=len(items),
            total=total,
            message=f"Exported {len(items)}/{total} items"
        )
    
    return {"items": items, "total": len(items), "format": format}
```

### Elicitation (Ask User for Input)

Server can ask user for confirmation or additional data:
```python
@mcp.tool()
async def delete_api_key(key_id: str) -> dict:
    """Permanently revoke an API key. Cannot be undone."""
    # Ask user for confirmation
    confirm = await mcp.elicit(
        message=f"Are you sure you want to permanently revoke API key {key_id}?",
        schema={
            "type": "object",
            "properties": {
                "confirm": {
                    "type": "boolean",
                    "description": "Type true to confirm deletion"
                }
            },
            "required": ["confirm"]
        }
    )
    if not confirm.get("confirm"):
        return {"status": "cancelled", "message": "Deletion cancelled by user"}
    
    return await _api("delete", f"/auth/keys/{key_id}")
```

### Sampling (Server-Initiated LLM Calls)

Server asks client's LLM to analyze data:
```python
@mcp.tool()
async def analyze_ticket(ticket_id: int) -> dict:
    """Analyze support ticket and suggest resolution."""
    ticket = await _api("get", f"/support/tickets/{ticket_id}")
    
    # Ask the LLM to analyze
    analysis = await mcp.sample(
        messages=[{
            "role": "user",
            "content": f"Analyze this support ticket and categorize priority:\n\n"
                       f"Subject: {ticket['subject']}\nBody: {ticket['body']}"
        }],
        max_tokens=500
    )
    
    return {
        "ticket": ticket,
        "analysis": analysis.content,
        "suggested_priority": extract_priority(analysis.content)
    }
```

### Resource Subscriptions

Client subscribes to resource changes:
```python
@mcp.resource("myapp://notifications/unread-count")
async def unread_count() -> dict:
    """Number of unread notifications. Auto-updates on change."""
    count = await _api("get", "/notifications/unread-count")
    return count

# When data changes, server notifies:
# → notifications/resources/list_changed
```

### Dynamic Tool Registration

Server can add/remove tools at runtime and notify clients:
```python
# After user upgrades tier, add premium tools
mcp.add_tool(premium_search_tool)
await mcp.notify_tools_changed()
```

---

## Anti-Patterns (What NOT to Do)

### REST Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Verbs in URL: `/getUser` | Not RESTful | `GET /users/{id}` |
| God endpoint: `POST /api` with action field | Unpredictable | Separate endpoints per resource |
| Deep nesting: `/a/{id}/b/{id}/c/{id}` | Rigid coupling | Max 2 levels, flatten with params |
| Returning 200 for errors | Client can't distinguish | Use proper HTTP codes |
| Breaking changes in same version | Trust destroyed | New version or optional fields only |
| Internal DB IDs in URL | Security risk | UUIDs or slugs |
| No pagination on lists | Memory blowup | Always paginate |
| Inconsistent field names | Dev confusion | Linter + style guide |
| Exposing stack traces | Security risk | Sanitized error format |
| Rate limit without Retry-After | Client hammers | Always include Retry-After |
| No Content-Type header | Parse failures | Always `application/json` |
| POST for reads | Breaks caching, semantics | GET for reads |
| Missing CORS preflight | Browser clients blocked | Handle OPTIONS |

### MCP Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Too many tools (30+) | LLM confused, picks wrong | Max 10-15, group logically |
| Vague descriptions | LLM doesn't know when to use | Be specific: what, when, returns |
| No inputSchema | LLM guesses params | JSON Schema with descriptions on every field |
| Plain text results | Hard to parse | Return structured JSON |
| Throwing exceptions | Breaks client | Return isError: true in result |
| No server instructions | LLM has no context | Write comprehensive instructions |
| Leaking API keys in results | Security breach | Sanitize all outputs |
| No timeout on HTTP calls | Tool hangs forever | httpx timeout=30 |
| One tool per endpoint | Too granular | Combine related operations |
| Huge results (100KB+) | Context overflow | Paginate, truncate, summarize |
| No error context | LLM can't recover | Include error code + actionable message |
| Missing annotations | Client can't show UI hints | Add readOnly/destructive/idempotent hints |
