# Weibo MCP Server

这是一个基于 [Model Context Protocol](https://modelcontextprotocol.io) 的服务器，用于抓取微博用户信息、动态和搜索功能。该服务器可以帮助获取微博用户的详细信息、动态内容以及进行用户搜索。

<a href="https://glama.ai/mcp/servers/@qinyuanpei/mcp-server-weibo">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@qinyuanpei/mcp-server-weibo/badge" alt="Weibo Server MCP server" />
</a>

## 安装

从源代码安装：

```json
{
    "mcpServers": {
        "weibo": {
            "command": "uvx",
            "args": [
                "--from",
                "git+https://github.com/qinyuanpei/mcp-server-weibo.git",
                "mcp-server-weibo"
            ]
        }
    }
}
```
从包管理器安装：

```json
{
    "mcpServers": {
        "weibo": {
            "command": "uvx",
            "args": ["mcp-server-weibo"],
        }
    }
}
```

## 组件

### 工具

- `search_users(keyword, limit)`: 用于搜索微博用户
- `get_profile(uid)`: 获取用户详细信息
- `get_feeds(uid, limit)`: 获取用户动态

### 资源   

无

### 提示

无

## 依赖要求

- Python >= 3.10
- httpx >= 0.24.0

## 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 免责声明

本项目与微博官方无关，仅用于学习和研究目的。