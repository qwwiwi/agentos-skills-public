# REST → MCP Mapping Guide

How to convert existing REST API endpoints into MCP primitives.

## Decision Matrix

```
REST endpoint → Which MCP primitive?

Is it a simple GET without params?
  → Resource (uri: "myapp://entity/name")

Is it a GET with dynamic ID only?
  → Resource Template (uriTemplate: "myapp://entity/{id}")
  OR Tool (if LLM needs to decide when to fetch)

Is it a GET with search/filter params?
  → Tool (search_entity, list_entity)

Is it POST/PUT/PATCH/DELETE?
  → Tool (create_entity, update_entity, delete_entity)

Is it a static config/status?
  → Resource (loaded once into context)
```

## Naming Conventions

### Tools (snake_case, verb_noun)

| REST | MCP Tool Name |
|------|--------------|
| GET /knowledge/search?q= | search_knowledge |
| GET /knowledge/list | list_knowledge |
| GET /knowledge/{id} | get_knowledge |
| POST /tickets | create_ticket |
| PATCH /profile/me | update_profile |
| DELETE /api-keys/{id} | revoke_api_key |
| POST /network/connect | send_connect_request |
| PATCH /notifications/{id}/read | mark_notification_read |

Patterns:
- Read one: `get_{resource}` (get_knowledge, get_event)
- Read list: `list_{resources}` (list_events, list_tickets)
- Search: `search_{resources}` (search_knowledge)
- Create: `create_{resource}` (create_ticket)
- Update: `update_{resource}` (update_profile)
- Delete: `delete_{resource}` or domain verb (revoke_api_key, dismiss_notification)

### Resources (URI scheme)

```
{app}://{resource}/{identifier}

edgelab://profile/me
edgelab://notifications/unread-count
edgelab://knowledge/42
edgelab://faq
```

### Prompts (action-oriented)

```
analyze_{domain}     -- analyze_material, analyze_portfolio
summarize_{domain}   -- summarize_events, summarize_activity
recommend_{domain}   -- recommend_content, recommend_connections
```

## Tool Description Best Practices

Description is for the LLM. It decides when to call the tool based on description.

**Good:**
```
Search EdgeLab knowledge base by keywords. Returns lessons, skills, usecases,
workshops, guides, and live recordings. Use when user asks about learning
materials, tutorials, or educational content. Supports category filtering.
```

**Bad:**
```
Searches knowledge.
```

**Structure:**
1. What the tool does (one sentence)
2. What it returns (brief)
3. When to use it (triggers for LLM)
4. Important constraints (optional)

## inputSchema Best Practices

Every property needs a description:
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search keywords, minimum 2 characters"
    },
    "category": {
      "type": "string",
      "enum": ["lesson", "skill", "usecase", "live", "workshop", "guide"],
      "description": "Filter by content category. Omit to search all categories"
    },
    "limit": {
      "type": "integer",
      "default": 20,
      "minimum": 1,
      "maximum": 100,
      "description": "Max results to return (default 20)"
    }
  },
  "required": ["query"]
}
```

Rules:
- Use `enum` when possible (LLM picks from list, not guesses)
- Set `default` for optional params
- Set `minimum`/`maximum` for numbers
- Mark truly required fields in `required`
- `description` on every field -- LLM reads them

## Tool Result Best Practices

Return structured JSON, not plain text:
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"items\": [...], \"total\": 5, \"query\": \"bitcoin\"}"
    }
  ],
  "isError": false
}
```

Error handling inside tool (don't throw):
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"error\": \"not_found\", \"message\": \"No results for query\"}"
    }
  ],
  "isError": true
}
```

## Grouping Tools by Module

Same modules as REST API, but flat tool names:

| REST Module | MCP Tools |
|------------|-----------|
| Auth | list_api_keys, create_api_key, revoke_api_key, rotate_api_key |
| Profile | get_my_profile, update_my_profile |
| Knowledge | search_knowledge, list_knowledge, get_knowledge, get_knowledge_files |
| Events | list_events, get_event, propose_event, get_event_calendar |
| Network | list_members, find_matches, send_connect, handle_request |
| Support | list_tickets, create_ticket, get_ticket, list_faq |
| Points | get_points_total, get_points_history |
| Notifications | list_notifications, mark_read, get_unread_count |

Server instructions should document these groupings for the LLM.
