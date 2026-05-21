# MCP Server Implementation Patterns

Practical patterns for building MCP servers in Python and TypeScript.

## Python: FastMCP (recommended)

### Minimal Server

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "myapp",
    instructions="MyApp MCP server. Provides access to knowledge base and user data."
)

@mcp.tool()
async def search_knowledge(query: str, category: str | None = None, limit: int = 20) -> dict:
    """Search knowledge base by keywords.

    Returns lessons, skills, usecases, workshops, guides.
    Use when user asks about learning materials or tutorials.
    """
    # Call your REST API internally
    params = {"q": query, "limit": limit}
    if category:
        params["category"] = category
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/knowledge/search", headers=headers, params=params)
        r.raise_for_status()
        return r.json()

@mcp.resource("myapp://profile/me")
async def get_profile() -> dict:
    """Current user profile."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/profile/me", headers=headers)
        return r.json()

@mcp.prompt()
async def analyze_material(material_id: int) -> str:
    """Analyze a knowledge material and provide learning recommendations."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/knowledge/{material_id}", headers=headers)
        data = r.json()
    return f"Analyze this material and suggest next steps:\n\n{data['title']}\n{data['description']}"
```

### Running

```bash
# stdio (local, for Claude Desktop / IDE)
python server.py

# HTTP (remote, for multi-client)
mcp run server.py --transport http --port 8080
```

### Configuration (claude_desktop_config.json)

```json
{
  "mcpServers": {
    "myapp": {
      "command": "python",
      "args": ["server.py"],
      "env": {
        "MYAPP_API_KEY": "myapp_live_..."
      }
    }
  }
}
```

## TypeScript SDK

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

const server = new McpServer({
  name: "myapp",
  version: "1.0.0"
});

server.tool(
  "search_knowledge",
  "Search knowledge base. Use when user asks about learning materials.",
  {
    query: z.string().min(2).describe("Search keywords"),
    category: z.enum(["lesson", "skill", "usecase"]).optional(),
    limit: z.number().int().min(1).max(100).default(20)
  },
  async ({ query, category, limit }) => {
    const params = new URLSearchParams({ q: query, limit: String(limit) });
    if (category) params.set("category", category);
    const res = await fetch(`${BASE_URL}/knowledge/search?${params}`, { headers });
    const data = await res.json();
    return { content: [{ type: "text", text: JSON.stringify(data) }] };
  }
);
```

## Pattern: REST API Wrapper

Most MCP servers wrap an existing REST API. Standard pattern:

```python
import os
import httpx
from mcp.server.fastmcp import FastMCP

# Config from env
BASE_URL = os.getenv("MYAPP_BASE_URL", "https://api.myapp.com/v1")
API_KEY = os.getenv("MYAPP_API_KEY")

mcp = FastMCP("myapp", instructions="...")

async def _api(method: str, path: str, **kwargs) -> dict:
    """Internal API caller with error handling."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        r = await getattr(client, method)(
            path,
            headers={"Authorization": f"Bearer {API_KEY}"},
            **kwargs
        )
        if r.status_code >= 400:
            return {"error": r.json().get("error", {"code": "unknown", "message": r.text})}
        return r.json()

@mcp.tool()
async def search_knowledge(query: str, category: str | None = None, limit: int = 20) -> dict:
    """Search knowledge base."""
    params = {"q": query, "limit": limit}
    if category:
        params["category"] = category
    return await _api("get", "/knowledge/search", params=params)

@mcp.tool()
async def create_ticket(subject: str, body: str, priority: str = "normal") -> dict:
    """Create support ticket. Use when user reports a problem or asks for help."""
    return await _api("post", "/support/tickets", json={
        "subject": subject, "body": body, "priority": priority
    })
```

## Pattern: Tool Annotations

```python
@mcp.tool(annotations={
    "title": "Search Knowledge Base",
    "readOnlyHint": True,
    "openWorldHint": True
})
async def search_knowledge(query: str) -> dict:
    """Search knowledge base."""
    ...

@mcp.tool(annotations={
    "title": "Delete API Key",
    "destructiveHint": True,
    "idempotentHint": True
})
async def revoke_api_key(key_id: str) -> dict:
    """Permanently revoke an API key. This cannot be undone."""
    ...
```

## Pattern: Server Instructions

Write comprehensive instructions for the LLM:

```python
mcp = FastMCP("edgelab", instructions="""
EdgeLab MCP Server — educational platform for AI practitioners.

## Available Tools
- search_knowledge: Find lessons, skills, usecases, workshops, guides
- list_knowledge: Browse with category/tier filters
- get_knowledge: Get full details of a specific material
- create_ticket: Report issues or request help
- list_events: Upcoming community events

## Usage Guidelines
1. Always search before listing (search is faster)
2. Check material tier (edge/pro/vip) before recommending
3. For support issues, create a ticket rather than just describing the problem
4. Events may have limited spots — mention registration deadlines

## Content Categories
- lesson: Step-by-step tutorials
- skill: Practical skill modules
- usecase: Real-world applications
- live: Recorded live sessions
- workshop: Interactive workshops
- guide: Reference guides
""")
```

## Pattern: Error Handling

Never throw exceptions from tools. Return error info:

```python
@mcp.tool()
async def get_knowledge(knowledge_id: int) -> dict:
    """Get knowledge item details."""
    try:
        result = await _api("get", f"/knowledge/{knowledge_id}")
        if "error" in result:
            return {"error": result["error"]["message"], "code": result["error"]["code"]}
        return result
    except httpx.ConnectError:
        return {"error": "API unavailable", "code": "connection_error"}
    except Exception as e:
        return {"error": str(e), "code": "internal_error"}
```

## Testing

```bash
# MCP Inspector (interactive testing)
npx @modelcontextprotocol/inspector python server.py

# Programmatic test
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test():
    params = StdioServerParameters(command="python", args=["server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            result = await session.call_tool("search_knowledge", {"query": "bitcoin"})
            print(result)
```

## Deployment

### Local (stdio)
- Best for development and single-user
- No auth needed (inherits host process permissions)
- Config in claude_desktop_config.json or IDE settings

### Remote (Streamable HTTP)
- Best for production, multi-user
- Requires OAuth 2.1 or API key auth
- Deploy as any HTTP service (Docker, Cloud Run, Lambda)
- Add rate limiting, logging, monitoring

### Cloudflare Workers (edge)
```bash
npx create-cloudflare@latest my-mcp -- --template=cloudflare/ai/demos/remote-mcp-authless
```

### Docker
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY server.py .
CMD ["python", "server.py"]
```
