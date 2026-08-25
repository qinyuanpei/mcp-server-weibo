# CLI Guide

Use the CLI for direct terminal or script access without an MCP client.

```bash
uvx --from mcp-server-weibo weibo-cli --help
```

`profile` prints one JSON object. All collection commands print one valid JSON array, including an empty `[]` result.

## Optional QR-code login

The CLI uses automatically generated visitor cookies by default. If a query needs an authenticated Weibo session, scan a QR code with the Weibo mobile app:

```bash
weibo-cli login
weibo-cli login --timeout 300
```

The command waits for a scan and confirmation, validates the result, then stores the session in `~/.config/mcp-server-weibo/cookies.json`. Do not share this file. It is not read from environment variables or accepted as a command-line cookie value. QR login is a CLI-only feature; the MCP server continues to use visitor cookies.

```bash
weibo-cli users "Lei Jun" -n 5
weibo-cli feeds 1749127163 -n 10 --no-include-pics
weibo-cli feeds 1749127163 -n 10 --include-profile
weibo-cli search "Weibo" -n 10 --no-include-pics --include-profile
```

`feeds` and `search` include `pics` by default and exclude nested `user` data by default. Use `--no-include-pics` or `--include-profile` when needed. See [CLI.md](CLI.md) for the full command list and Chinese usage guide.
