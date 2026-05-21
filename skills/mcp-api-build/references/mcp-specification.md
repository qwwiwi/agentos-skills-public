# MCP Protocol Specification Reference

_Source: modelcontextprotocol.io/specification/2025-06-18_

## Architecture

```
Host (IDE/App)
├── Client A ←→ Server A (filesystem)
├── Client B ←→ Server B (database)
└── Client C ←→ Server C (external API)
```

- **Host**: Application housing LLM (Claude Desktop, IDE, agent framework)
- **Client**: Maintains 1:1 connection with server, handles protocol negotiation
- **Server**: Exposes tools, resources, prompts via MCP primitives

Communication: JSON-RPC 2.0 over stdio or Streamable HTTP.

## Lifecycle

```
Client → initialize(protocolVersion, capabilities, clientInfo)
Server → response(protocolVersion, capabilities, serverInfo, instructions?)
Client → initialized (notification)
... normal operations ...
Client → shutdown / close transport
```

### Capability Negotiation

Client and server declare capabilities during initialize:
- Client: `roots`, `sampling`, `elicitation`
- Server: `tools`, `resources`, `prompts`, `logging`, `completions`

## Three Primitives

### Tools (Model-controlled)

Functions the LLM can invoke. Like POST endpoints.

```json
{
  "name": "search_knowledge",
  "description": "Search knowledge base by keywords",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": { "type": "string", "description": "Search terms" },
      "limit": { "type": "integer", "default": 20 }
    },
    "required": ["query"]
  },
  "annotations": {
    "title": "Search Knowledge Base",
    "readOnlyHint": true,
    "openWorldHint": true
  }
}
```

Tool result:
```json
{
  "content": [
    { "type": "text", "text": "{\"items\": [...], \"total\": 42}" }
  ],
  "isError": false
}
```

**Tool annotations** (hints, not guarantees):
- `title`: Human-readable display name
- `readOnlyHint`: true if tool doesn't modify state
- `destructiveHint`: true if tool may delete/destroy data
- `idempotentHint`: true if calling multiple times has same effect
- `openWorldHint`: true if tool interacts with external systems

### Resources (Application-controlled)

Data/content exposed by server. Like GET endpoints without parameters.

```json
{
  "uri": "myapp://profile/me",
  "name": "My Profile",
  "description": "Current user profile data",
  "mimeType": "application/json"
}
```

Resource templates (parameterized):
```json
{
  "uriTemplate": "myapp://knowledge/{id}",
  "name": "Knowledge Item",
  "description": "Get specific knowledge item by ID"
}
```

### Prompts (User-controlled)

Reusable prompt templates.

```json
{
  "name": "analyze_material",
  "description": "Analyze an EdgeLab material and provide recommendations",
  "arguments": [
    { "name": "material_id", "description": "ID of the material", "required": true }
  ]
}
```

## Transports

### stdio
- Server runs as subprocess, communicates via stdin/stdout
- Best for: local tools, CLI integration, development
- Messages: newline-delimited JSON-RPC

### Streamable HTTP
- Server exposes HTTP endpoint, client sends JSON-RPC via POST
- Optional SSE for server-to-client streaming
- Session management via `Mcp-Session-Id` header
- Best for: remote servers, multi-client, production

### Authorization (Streamable HTTP)
- OAuth 2.1 based
- Server acts as Resource Server
- Authorization Server metadata at `/.well-known/oauth-authorization-server`
- Dynamic Client Registration supported
- Scopes for granular access control

## Error Handling

Standard JSON-RPC error codes:
| Code | Name | Meaning |
|------|------|---------|
| -32700 | Parse error | Invalid JSON |
| -32600 | Invalid request | Not valid JSON-RPC |
| -32601 | Method not found | Unknown method |
| -32602 | Invalid params | Bad parameters |
| -32603 | Internal error | Server error |

Tool errors: return `isError: true` in tool result, not JSON-RPC error.

## Server Instructions

Optional `instructions` field in server's initialize response. Plain text guidance for LLM on how to use the server. Max ~10K chars recommended.

```json
{
  "serverInfo": { "name": "edgelab", "version": "1.0.0" },
  "instructions": "EdgeLab server provides access to educational content. Use search_knowledge for finding materials, get_knowledge for details. Always check user's tier before suggesting pro/vip content."
}
```
