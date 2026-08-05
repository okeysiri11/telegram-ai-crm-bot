# Enterprise MCP Gateway (ADOS OS 4.2)

Exposes ADOS capabilities through the Model Context Protocol so Claude Desktop (and future MCP clients) can interact with the running Runtime — without bypassing enterprise boundaries.

```
Claude Desktop → MCP Client → ADOS MCP Gateway → Runtime API
  → AI Orchestrator → Provider Gateway → Enterprise Modules
```

## Module

`src/mcp` · service id `ados.mcp` · package `@ados/mcp` 4.2.0  
Config: `config/mcp.config.json`

| Component | Role |
|-----------|------|
| `MCPGateway` | Facade |
| `MCPServer` | JSON-RPC MCP methods |
| `MCPTransport` | Runtime invoker / HTTP fallback |
| `MCPRegistry` | Tools + resources + prompts |
| `MCPToolRegistry` | Tool definitions → Runtime paths |
| `MCPResources` | Read-only resource URIs |
| `MCPPrompts` | Prompt templates |
| `MCPSession` | Client sessions |
| `MCPPermissions` | read / execute / admin |
| `MCPAuthentication` | Session tokens |
| `MCPEvents` | Event bus + audit logs |
| `MCPConfig` | Disk + env configuration |

## Principle

**Do not expose internals.** Every tool/resource call goes through the Runtime API (in-process invoker bound at Runtime start).

## Tools

`system.status` · `system.health` · `system.version` · `runtime.status` · `runtime.metrics` · `agent.list` · `agent.info` · `agent.execute` · `workflow.list` · `workflow.execute` · `provider.list` · `provider.status` · `project.list` · `project.info` · `knowledge.search` · `document.search` · `dashboard.status` · `voice.status`

## Resources

`ados://architecture` · `ados://sprint` · `ados://documentation` · `ados://knowledge` · `ados://modules` · `ados://providers` · `ados://agents` · `ados://configuration`

## Prompts

`explain_module` · `review_code` · `create_workflow` · `generate_ui` · `generate_documentation` · `architecture_review` · `bug_investigation`

## Permissions

| Level | Access |
|-------|--------|
| read | Status, lists, resources |
| execute | Agent/workflow tools |
| admin | Configuration resource |

## Authentication

Session tokens (`x-ados-mcp-token` / RPC `token` field). Default admin token from `config/mcp.config.json` (override with `ADOS_MCP_TOKEN`).

## REST (Control Center)

| Method | Path |
|--------|------|
| GET | `/mcp/status` |
| GET | `/mcp/tools` |
| GET | `/mcp/resources` |
| GET | `/mcp/prompts` |
| POST | `/mcp/rpc` |
| POST | `/mcp/connect` |

## Events

`mcp.connected` · `mcp.disconnected` · `mcp.tool.called` · `mcp.tool.completed` · `mcp.resource.read` · `mcp.permission.denied`

## Configuration example

```json
{
  "enabled": true,
  "host": "127.0.0.1",
  "port": 3100,
  "transport": "http+stdio",
  "authentication": {
    "required": true,
    "defaultAdminToken": "ados-mcp-dev-token"
  }
}
```

## Example — call tool via Runtime

```bash
curl -s -X POST http://localhost:3000/mcp/rpc \
  -H 'Content-Type: application/json' \
  -d '{"method":"tools/call","token":"ados-mcp-dev-token","params":{"name":"system.health","arguments":{}}}'
```

## Control Center

Page **MCP Gateway** (`/mcp`): clients, tools, resources, prompts, permissions, sessions, requests, errors, logs.

## Boot order

… → Voice → **MCP** → Runtime Server (binds Runtime invoker into MCP Gateway)
