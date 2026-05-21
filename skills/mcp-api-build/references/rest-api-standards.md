# REST API Design Standards

_Compiled from: Google AIP, Microsoft Azure Guidelines, Zalando, Stripe_

## URL Design Rules

1. **Plural nouns for collections**: `/users`, `/tickets`, `/events`
2. **Max 2 levels of nesting**: `/users/{id}/orders` -- ok. `/users/{id}/orders/{id}/items` -- flatten
3. **No verbs in URL**: `POST /tickets` not `/createTicket`
4. **Filter via query params**: `GET /events?status=upcoming&limit=10`
5. **Version in URL**: `/v1/users`
6. **kebab-case for paths**: `/api-keys`, `/call-request`
7. **snake_case for JSON fields**: `created_at`, `user_id` (Stripe/Google style)

## HTTP Methods

| Method | Operation | Idempotent | Success Code |
|--------|-----------|------------|-------------|
| GET | Read | Yes | 200 |
| POST | Create | No | 201 |
| PUT | Full replace | Yes | 200 |
| PATCH | Partial update | Depends | 200 |
| DELETE | Delete | Yes | 204 |

## Response Format

### Single resource
```json
{
  "id": 42,
  "slug": "example",
  "title": "Example Resource",
  "created_at": "2026-03-29T14:00:00Z",
  "updated_at": "2026-03-29T14:00:00Z"
}
```

### Collection (Stripe pattern)
```json
{
  "items": [...],
  "total": 150,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

### Cursor-based pagination (Google/Stripe)
```json
{
  "items": [...],
  "next_cursor": "abc123",
  "has_more": true
}
```

## Error Format (RFC 7807 inspired)

```json
{
  "error": {
    "code": "not_found",
    "message": "Resource with ID 999 not found",
    "status": 404
  }
}
```

### Standard HTTP Error Codes
| Code | Meaning | Use when |
|------|---------|----------|
| 400 | Bad Request | Invalid params, missing fields |
| 401 | Unauthorized | No/invalid auth token |
| 403 | Forbidden | Valid token, insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | State conflict (duplicate, version mismatch) |
| 422 | Unprocessable | Validation error (semantic) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Error | Server bug |

## Authentication Patterns

### API Key (service-to-service, agents)
```
Authorization: Bearer myapp_live_a1b2c3d4...
```
Best practices:
- Prefix keys with app name: `stripe_live_`, `edgelab_live_`
- Scopes: `knowledge:read`, `support:write`
- Max N active keys per account
- Rotation without downtime

### JWT (user sessions)
```
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
```

### OAuth 2.0 (integrations)
- Authorization Code -- web apps
- Client Credentials -- machine-to-machine
- PKCE -- mobile/SPA

## Rate Limiting

Headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1711737600
Retry-After: 30
```

Strategies:
- Per-key limits (not per-IP)
- Tiered: free 60/min, pro 120/min, enterprise 300/min
- Sliding window preferred over fixed window
- 429 response with Retry-After header

## Versioning (Google AIP)

- Major version in URL: `/v1/`, `/v2/`
- Breaking changes = new major version
- Non-breaking (new optional fields, new endpoints) = same version
- Deprecation: `Sunset` header with date
- Support N-1 version minimum 12 months

## Filtering, Sorting, Search

```
GET /items?category=lesson&sort=-created_at&limit=20&offset=0
GET /items/search?q=keyword&category=lesson
```

Rules:
- Filter by field name: `?status=active&category=lesson`
- Sort: `?sort=field` (asc) or `?sort=-field` (desc)
- Search: separate endpoint or `?q=` param
- Always paginate lists (never return unbounded results)

## Design Process Checklist

1. [ ] Identify consumers (frontend, mobile, agents, partners)
2. [ ] Model resources as nouns
3. [ ] Map CRUD operations to HTTP methods
4. [ ] Group into modules by business domain
5. [ ] Define consistent response schemas
6. [ ] Define error schema (use everywhere)
7. [ ] Write OpenAPI spec BEFORE code
8. [ ] Design auth (API key vs JWT vs OAuth)
9. [ ] Set rate limits per tier
10. [ ] Plan versioning strategy
11. [ ] Add pagination to all list endpoints
12. [ ] Generate docs from OpenAPI spec
