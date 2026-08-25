# MCP Integration Guide

Use MCP when an AI client should discover and call Weibo tools. The server automatically creates visitor cookies and exposes Streamable HTTP at `/mcp`.

## stdio

```json
{
  "mcpServers": {
    "weibo": {
      "command": "uvx",
      "args": ["--from", "mcp-server-weibo", "mcp-server-weibo"]
    }
  }
}
```

## Streamable HTTP

```bash
mcp-server-weibo http
```

```json
{
  "mcpServers": {
    "weibo": {
      "type": "streamable-http",
      "url": "http://localhost:4200/mcp"
    }
  }
}
```

Use `/mcp`, not the legacy `/sse` endpoint.

Available tools cover user search and profiles, feeds and hot feeds, content and topic search, trending topics, comments, followers, and fans. See the Chinese guide for the complete tool table and Inspector examples: [MCP.md](MCP.md).
