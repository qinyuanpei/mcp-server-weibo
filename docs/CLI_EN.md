# CLI Guide

Use the CLI to query Weibo data directly from a terminal, script, or pipeline without an MCP client.

## Install and run

No manual cookie configuration is required. Commands automatically obtain a visitor cookie.

```bash
# Run once without installing the package permanently
uvx --from mcp-server-weibo weibo-cli --help

# Install as a local command for continued use
uv tool install mcp-server-weibo
weibo-cli --help
```

## Optional QR-code login

The CLI uses automatically generated visitor cookies by default. If a query needs an authenticated session, log in from the terminal by scanning a QR code with the Weibo mobile app:

```bash
weibo-cli login
weibo-cli login --timeout 300
```

The command displays a QR code and waits for the user to scan and confirm it in the Weibo app. After a successful login, the session is validated and saved to `~/.config/mcp-server-weibo/cookies.json`. Do not share this file. The program never reads user cookies from environment variables or command-line options. QR-code login is available only through the CLI; the MCP server always uses visitor cookies.

Use `session` to validate and inspect the current local CLI session. It prints the login status and UID when valid, or `null` when no valid session exists:

```bash
weibo-cli session
```

## Output format

Collection commands print one complete JSON array, including `[]` when no result is available. `profile` prints one JSON object, and `session` prints a login-session object or `null`. This makes all output suitable for `jq`, Python, and other JSON tools.

```bash
weibo-cli trending -n 3
```

## Commands

| Command | Description |
|---|---|
| `profile <uid>` | Get a user profile. |
| `feeds <uid> [-n N]` | Get a user's posts. |
| `search <keyword> [-n N] [-p P] [--no-include-pics] [--include-profile]` | Search Weibo posts. |
| `users <keyword> [-n N] [-p P]` | Search users. |
| `topics <keyword> [-n N] [-p P]` | Search topics. |
| `trending [-n N]` | Get trending searches. |
| `comments <feed_id> [-p P]` | Get comments for a post. |
| `followers <uid> [-n N] [-p P]` | Get a user's followers. |
| `fans <uid> [-n N] [-p P]` | Get a user's fans. |
| `login [--timeout SECONDS]` | Log in by QR code and save a local CLI session. |
| `session` | Validate and display the current local CLI login session. |

## Common workflows

Search for a user first, then pass the returned `id` to a profile or feeds command:

```bash
weibo-cli users "Lei Jun" -n 5
weibo-cli profile 1749127163
weibo-cli feeds 1749127163 -n 10
```

Use a feed `id` returned by `feeds` or `search` to retrieve comments:

```bash
weibo-cli comments 5173507416919189 -p 1
```

## Compact `feeds` and `search` output

`feeds` and `search` include picture metadata by default, but exclude nested `user` data by default. Use these switches as needed:

```bash
# Omit pics
weibo-cli feeds 1749127163 --no-include-pics

# Include the author profile for every post
weibo-cli feeds 1749127163 --include-profile

# Omit pictures and include the author profile
weibo-cli feeds 1749127163 --no-include-pics --include-profile

# Search results support the same switches
weibo-cli search "Lei Jun" --no-include-pics --include-profile
```

## When to use the CLI

- Process JSON in shell scripts.
- Look up users, trending topics, topics, posts, or comments on demand.
- Perform a simple task without orchestrating tool calls through an AI client.
