---
name: weibo-cli
description: Query public Weibo data from a terminal with the bundled weibo-cli command. Use for direct JSON retrieval in scripts or shell sessions; do not use when an MCP client should call tools itself.
---

# Weibo CLI

Use `weibo-cli` for direct terminal access. It automatically generates visitor cookies; do not configure or supply user cookies. If authenticated access is needed, instruct the user to run `weibo-cli login` and scan its QR code themselves.

## Install and run

```bash
# Install once for ongoing use
uv tool install mcp-server-weibo
weibo-cli --help

# Run commands directly after installation
weibo-cli trending -n 3

# Optional, interactive: saves this user's QR-login session locally
weibo-cli login
```

Use `uvx` only for an ad-hoc command when the package should not remain installed:

```bash
uvx --from mcp-server-weibo weibo-cli --help
```

## Choose a command

- Look up a user ID: `weibo-cli users "keyword" -n 5`
- Get a known user's details: `weibo-cli profile <uid>`
- Get posts: `weibo-cli feeds <uid> -n 10`
- Search posts or topics: `weibo-cli search "keyword"` or `weibo-cli topics "keyword"`
- Get heat, comments, social graph: `trending`, `comments`, `followers`, or `fans`

Use a feed `id` from `feeds` or `search` as the input to `comments`.

## Output contract

`profile` returns one JSON object. Every collection command returns one valid JSON array, including `[]` for an empty result. This makes outputs suitable for JSON parsers and shell pipelines.

`login` is CLI-only. It waits for the user to scan and confirm a QR code, then stores the session at `~/.config/mcp-server-weibo/cookies.json`; treat that file as sensitive. Do not ask users to paste cookies or attempt password or CAPTCHA login.

For `feeds` and `search`, `pics` is included by default and nested `user` is excluded by default. Use `--no-include-pics` to omit picture metadata or `--include-profile` to include each post's author data.

## Further documentation

Read [CLI usage](../docs/CLI.md) for the full command list. For AI-client integration rather than terminal use, read [MCP usage](../docs/MCP.md).
