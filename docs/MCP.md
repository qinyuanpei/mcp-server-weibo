# MCP 接入指南

本指南适合希望让 Claude、Cursor、MCP Inspector 或其他 MCP 客户端调用微博数据工具的用户。

## 快速选择

- **本地客户端**：使用 `stdio`，无需自行管理端口。
- **远程或容器部署**：使用 Streamable HTTP，服务地址为 `http://<host>:4200/mcp`。

服务始终自动申请微博访客 Cookie；不读取或保存用户提供的 Cookie。微博可能对部分搜索或翻页施加访问限制。

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

从源码运行时，可将 `command` 改为 Python 可执行文件，并传入 `-m mcp_server_weibo.server`。

## Streamable HTTP

启动服务：

```bash
mcp-server-weibo http
```

Docker：

```bash
docker build -t mcp-server-weibo .
docker run -p 4200:4200 mcp-server-weibo
```

客户端配置：

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

`/mcp` 是当前 Streamable HTTP 端点；不要使用旧的 `/sse` 地址。

## 可用工具

| 工具 | 用途 |
|---|---|
| `search_users(keyword, limit, page)` | 搜索用户 |
| `get_profile(uid)` | 获取用户资料 |
| `get_feeds(uid, limit)` | 获取用户微博 |
| `get_hot_feeds(uid, limit)` | 获取热门微博 |
| `get_trendings(limit)` | 获取热搜 |
| `search_content(keyword, limit, page)` | 搜索微博内容 |
| `search_topics(keyword, limit, page)` | 搜索话题 |
| `get_comments(feed_id, page)` | 获取评论 |
| `get_followers(uid, limit, page)` | 获取关注列表 |
| `get_fans(uid, limit, page)` | 获取粉丝列表 |

## 使用 MCP Inspector 测试

先启动 HTTP 服务，再执行：

```bash
npx @modelcontextprotocol/inspector --cli http://127.0.0.1:4200/mcp --transport http --method tools/list
```

调用工具：

```bash
npx @modelcontextprotocol/inspector --cli http://127.0.0.1:4200/mcp --transport http --method tools/call --tool-name get_trendings --tool-arg limit=3
```

## 适用场景

- 让 AI 助手自主发现并调用微博工具；
- 在多步骤工作流中组合搜索、资料、动态与评论；
- 将服务部署为可被多个 MCP 客户端访问的端点。
