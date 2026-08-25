# MCP Integration Guide

Use MCP when an AI client such as Claude, Cursor, or MCP Inspector should discover and call Weibo tools.

## Choose a transport

- **Local client:** use `stdio`; no port management is needed.
- **Remote or container deployment:** use Streamable HTTP at `http://<host>:4200/mcp`.

The server always obtains Weibo visitor cookies automatically. It does not accept user-provided cookies or expose QR-code login; some searches and pagination requests may still be subject to Weibo access restrictions.

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

When running from source, set `command` to the Python executable and pass `-m mcp_server_weibo.server` as its arguments.

## Streamable HTTP

Start the server:

```bash
mcp-server-weibo http
```

With Docker:

```bash
docker build -t mcp-server-weibo .
docker run -p 4200:4200 mcp-server-weibo
```

Configure the client:

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

`/mcp` is the current Streamable HTTP endpoint. Do not use the legacy `/sse` endpoint.

## Available tools

| Tool | Purpose |
|---|---|
| `search_users(keyword, limit, page)` | Search users. |
| `get_profile(uid)` | Get a user profile. |
| `get_feeds(uid, limit)` | Get a user's posts. |
| `get_hot_feeds(uid, limit)` | Get hot posts for a user. |
| `get_trendings(limit)` | Get trending searches. |
| `search_content(keyword, limit, page)` | Search Weibo posts. |
| `search_topics(keyword, limit, page)` | Search topics. |
| `get_comments(feed_id, page)` | Get comments for a post. |
| `get_followers(uid, limit, page)` | Get a user's followers. |
| `get_fans(uid, limit, page)` | Get a user's fans. |

See the [Schema Reference](SCHEMAS_EN.md) for response fields and types.

## Test with MCP Inspector

Start the HTTP server, then list tools:

```bash
npx @modelcontextprotocol/inspector --cli http://127.0.0.1:4200/mcp --transport http --method tools/list
```

Call a tool:

```bash
npx @modelcontextprotocol/inspector --cli http://127.0.0.1:4200/mcp --transport http --method tools/call --tool-name get_trendings --tool-arg limit=3
```

## When to use MCP

- Let an AI assistant discover and call Weibo tools autonomously.
- Combine user lookup, profiles, feeds, searches, and comments in a multi-step workflow.
- Deploy a Weibo-data endpoint for access by multiple MCP clients.
