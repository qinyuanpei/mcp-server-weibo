# Weibo MCP Server

![mcp-server-weibo cover](assets/mcp-server-weibo-cover.png)

Access Weibo users, posts, trending topics, comments, topics, and social-graph data through automatically generated visitor cookies. User-provided cookies are never read; CLI users may optionally create a locally stored session by scanning a QR code.

## Choose an interface

| Goal | Use |
|---|---|
| Let an AI client discover and call Weibo tools | [MCP Integration Guide](docs/MCP_EN.md) |
| Fetch JSON directly from a shell script or terminal | [CLI Guide](docs/CLI_EN.md) |
| Let a coding agent follow the project's CLI conventions | [Weibo CLI Skill](skills/SKILL.md) |

See the [Schema Reference](docs/SCHEMAS_EN.md) ([中文](docs/SCHEMAS.md)) for every returned field, type, and command-to-schema mapping.

## Quick start

### MCP

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

The Streamable HTTP endpoint is `http://localhost:4200/mcp`. See the [MCP guide](docs/MCP_EN.md) for HTTP configuration, tool discovery, and testing.

### CLI

```bash
uvx --from mcp-server-weibo weibo-cli trending -n 3
uvx --from mcp-server-weibo weibo-cli users "Lei Jun" -n 5
uvx --from mcp-server-weibo weibo-cli feeds 1749127163 -n 10 --no-include-pics

# Optional: scan the displayed QR code to create a local authenticated CLI session
uvx --from mcp-server-weibo weibo-cli login

# Validate the current local CLI session
uvx --from mcp-server-weibo weibo-cli session
```

Collection commands print one valid JSON array; `profile` prints one JSON object, and `session` prints a login-session object or `null`. See the [CLI guide](docs/CLI_EN.md) for all commands.

## From source

```bash
git clone https://github.com/qinyuanpei/mcp-server-weibo.git
cd mcp-server-weibo
uv sync --extra dev
uv run mcp-server-weibo
```

Python >= 3.10. Licensed under [MIT](LICENSE). This project is not affiliated with Weibo and is intended for learning and research.
