# OpenAPI-First Design Process

Design the API contract before writing any code.

## Why API-First

1. **Frontend and backend develop in parallel** -- frontend uses mocks from spec
2. **Contract is the single source of truth** -- no "docs vs code" drift
3. **Auto-generate**: docs (Mintlify, Redoc), SDKs, server stubs, tests, mocks
4. **Review API design before implementation** -- catch issues early

## Step-by-Step Process

### 1. Domain Modeling (whiteboard phase)

Identify entities and relationships:
```
User ──has──> Profile
User ──creates──> Ticket
User ──earns──> Points
Knowledge ──has──> Files
Event ──has──> Proposals
User ──connects──> User (via Network)
```

Deliverable: entity-relationship diagram or text list.

### 2. Resource Inventory

List all resources with CRUD operations:

| Resource | C | R | U | D | Search | List | Notes |
|----------|---|---|---|---|--------|------|-------|
| Profile | - | ✓ | ✓ | - | - | - | /me only |
| API Key | ✓ | ✓ | - | ✓ | - | ✓ | rotate = custom |
| Knowledge | - | ✓ | - | - | ✓ | ✓ | read-only for users |
| Ticket | ✓ | ✓ | - | - | - | ✓ | create + read |
| Event | - | ✓ | - | - | - | ✓ | propose = custom |
| Network | - | - | - | - | ✓ | ✓ | connect = custom |
| Points | - | ✓ | - | - | - | ✓ | read-only |
| Notification | - | ✓ | ✓ | - | - | ✓ | mark_read = patch |

### 3. Write OpenAPI Spec

Start with paths, then schemas:

```yaml
openapi: 3.1.0
info:
  title: MyApp API
  version: "1.0"
  description: |
    API for MyApp platform.

servers:
  - url: https://api.myapp.com/v1

security:
  - bearerAuth: []

paths:
  /knowledge/search:
    get:
      operationId: searchKnowledge
      summary: Search knowledge base
      tags: [Knowledge]
      parameters:
        - name: q
          in: query
          required: true
          schema:
            type: string
            minLength: 2
          description: Search query
        - name: category
          in: query
          schema:
            type: string
            enum: [lesson, skill, usecase, live, workshop, guide]
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
            minimum: 1
            maximum: 100
        - name: offset
          in: query
          schema:
            type: integer
            default: 0
      responses:
        "200":
          description: Search results
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/KnowledgeList"
        "400":
          $ref: "#/components/responses/BadRequest"
        "401":
          $ref: "#/components/responses/Unauthorized"

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      description: "API key: Bearer edgelab_live_..."

  schemas:
    KnowledgeItem:
      type: object
      properties:
        id:
          type: integer
        slug:
          type: string
        title:
          type: string
        category:
          type: string
          enum: [lesson, skill, usecase, live, workshop, guide]
        description:
          type: string
        created_at:
          type: string
          format: date-time
      required: [id, slug, title, category]

    KnowledgeList:
      type: object
      properties:
        items:
          type: array
          items:
            $ref: "#/components/schemas/KnowledgeItem"
        total:
          type: integer
        limit:
          type: integer
        offset:
          type: integer
        has_more:
          type: boolean

    Error:
      type: object
      properties:
        error:
          type: object
          properties:
            code:
              type: string
            message:
              type: string
            status:
              type: integer

  responses:
    BadRequest:
      description: Invalid request
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/Error"
          example:
            error:
              code: bad_request
              message: "Query parameter 'q' is required"
              status: 400
    Unauthorized:
      description: Missing or invalid API key
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/Error"
```

### 4. Review Spec

Checklist before implementation:
- [ ] All resources covered
- [ ] Consistent naming (snake_case fields, plural paths)
- [ ] Shared schemas (Error, Pagination) reused via $ref
- [ ] Auth defined in securitySchemes
- [ ] Every endpoint has error responses
- [ ] Tags match modules
- [ ] Examples included for complex responses

### 5. Generate Artifacts

From OpenAPI spec, generate:
- **Documentation**: Mintlify, Redoc, Swagger UI
- **Mock server**: Prism (`npx @stoplight/prism-cli mock openapi.yaml`)
- **Client SDK**: openapi-generator, openapi-typescript
- **Server stub**: openapi-generator for Python/Node
- **Tests**: contract tests from spec

### 6. Implement Against Contract

Code must match spec exactly. Any deviation = bug (not "feature").
CI pipeline validates: `npx @stoplight/spectral-cli lint openapi.yaml`

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| Spec diverges from code | CI lint + contract tests |
| Over-nesting URLs | Max 2 levels, flatten with query params |
| Inconsistent field names | Linter rule: enforce snake_case |
| Missing error responses | Template: every endpoint gets 400/401/404/500 |
| No pagination | Rule: every list endpoint has limit+offset |
| Exposing internal IDs | Use slugs or UUIDs externally |
