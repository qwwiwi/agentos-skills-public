# Security & Production Checklist

Standards from Google, Microsoft, Stripe, and MCP security best practices.

## API Security

### Authentication
- [ ] API keys with app-specific prefix (`myapp_live_`, `myapp_test_`)
- [ ] Keys stored in env vars, never in code or config files
- [ ] Key rotation without downtime (overlap period)
- [ ] Separate test/live environments with different keys
- [ ] Scope-based access: `knowledge:read`, `support:write`

### Authorization
- [ ] RBAC (Role-Based Access Control) on every endpoint
- [ ] Row-Level Security for multi-tenant data (Supabase RLS)
- [ ] Check ownership: user can only access their own data
- [ ] Admin endpoints separated and extra-protected

### Input Validation
- [ ] Validate all inputs server-side (JSON body, query params, headers)
- [ ] JSON Schema validation on request bodies
- [ ] Reject unknown fields (strict mode)
- [ ] Sanitize strings (prevent XSS, SQL injection)
- [ ] Limit string lengths, array sizes, number ranges
- [ ] File upload: validate MIME type, size, extension

### Transport Security
- [ ] HTTPS only (redirect HTTP → HTTPS)
- [ ] TLS 1.2+ minimum
- [ ] HSTS header: `Strict-Transport-Security: max-age=31536000`
- [ ] No sensitive data in URL query strings (use POST body)

### Rate Limiting
- [ ] Per-key rate limits (not just per-IP)
- [ ] Tiered limits by subscription
- [ ] 429 response with Retry-After header
- [ ] Separate limits for read vs write operations
- [ ] Burst protection (sliding window)

### Error Handling
- [ ] Never expose stack traces in production
- [ ] Never expose internal IDs, paths, or SQL queries
- [ ] Consistent error format across all endpoints
- [ ] Log errors server-side with correlation ID
- [ ] Return correlation ID to client for support

## MCP Security

### Tool Input Validation
- [ ] JSON Schema validation on all tool inputs (inputSchema)
- [ ] Validate types, ranges, enums strictly
- [ ] Reject extra properties
- [ ] Sanitize before passing to downstream API

### Output Safety
- [ ] Never return raw API keys, passwords, tokens in tool results
- [ ] Sanitize error messages (no internal paths, no stack traces)
- [ ] Limit response size (truncate large results)
- [ ] Mask PII in logs

### Prompt Injection Defense
- [ ] Treat all tool inputs as untrusted
- [ ] Don't execute arbitrary code from tool arguments
- [ ] Don't construct SQL/shell commands from raw input
- [ ] Validate URLs before fetching (allowlist domains)

### Human-in-the-Loop
- [ ] Destructive operations (delete, revoke) require confirmation
- [ ] Financial operations require confirmation
- [ ] Mark destructive tools with `destructiveHint: true`
- [ ] Server instructions mention which tools need confirmation

### Least Privilege
- [ ] Each MCP server has minimal API permissions
- [ ] Read-only tools don't have write API keys
- [ ] Separate API keys for MCP server vs admin operations
- [ ] No wildcard scopes

## Production Readiness

### Monitoring
- [ ] Health check endpoint: `GET /health` → 200
- [ ] Structured logging (JSON)
- [ ] Request/response logging (sanitized)
- [ ] Error rate alerting
- [ ] Latency percentile tracking (p50, p95, p99)
- [ ] Rate limit hit tracking

### Reliability
- [ ] Graceful shutdown (drain connections)
- [ ] Timeout on all external calls (5-30s)
- [ ] Circuit breaker for downstream services
- [ ] Retry with exponential backoff (client side)
- [ ] Idempotency keys for POST operations (Stripe pattern)

### Documentation
- [ ] OpenAPI spec is single source of truth
- [ ] Every endpoint has request/response examples
- [ ] Error codes documented with recovery actions
- [ ] Rate limits documented per tier
- [ ] Changelog maintained
- [ ] Migration guide for breaking changes

### Testing
- [ ] Contract tests (spec vs implementation)
- [ ] Integration tests for each endpoint
- [ ] Load testing (verify rate limits work)
- [ ] Security scan (OWASP ZAP, Burp)
- [ ] MCP Inspector for tool testing
