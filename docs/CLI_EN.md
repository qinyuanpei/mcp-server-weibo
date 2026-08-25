# CLI Guide

Use the CLI for direct terminal or script access without an MCP client.

```bash
uvx --from mcp-server-weibo weibo-cli --help
```

`profile` prints one JSON object. All collection commands print one valid JSON array, including an empty `[]` result.

```bash
weibo-cli users "Lei Jun" -n 5
weibo-cli feeds 1749127163 -n 10 --no-include-pics
weibo-cli feeds 1749127163 -n 10 --include-profile
```

`feeds` includes `pics` by default and excludes nested `user` data by default. See [CLI.md](CLI.md) for the full command list and Chinese usage guide.
