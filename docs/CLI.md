# CLI 使用指南

本指南适合在终端、脚本或管道中直接查询微博数据，而不需要 MCP 客户端的用户。

## 安装与运行

无需配置 Cookie，命令会自动申请访客 Cookie。

```bash
# 临时运行
uvx --from mcp-server-weibo weibo-cli --help

# 安装为本地命令
uv tool install mcp-server-weibo
weibo-cli --help
```

## 可选：二维码登录

CLI 默认使用自动申请的访客 Cookie。如果查询需要登录会话，可在终端执行扫码登录：

```bash
weibo-cli login
weibo-cli login --timeout 300
```

命令会在终端显示二维码，等待用户在微博 App 中扫码并确认。登录成功后，会话会先校验，再保存至 `~/.config/mcp-server-weibo/cookies.json`。请勿分享此文件。程序不会从环境变量或命令行读取用户 Cookie。扫码登录仅适用于 CLI；MCP 服务始终使用访客 Cookie。

使用 `session` 可校验并查看当前本机 CLI 会话；有效时输出登录状态和 UID，无有效会话时输出 `null`：

```bash
weibo-cli session
```

## 输出格式

集合查询命令输出一个完整 JSON 数组；没有结果时输出 `[]`。`profile` 输出一个 JSON 对象，`session` 输出登录会话对象或 `null`。所有输出均可直接由 `jq`、Python 或其他 JSON 工具解析。

```bash
weibo-cli trending -n 3
```

## 命令

| 命令 | 说明 |
|---|---|
| `profile <uid>` | 获取用户资料 |
| `feeds <uid> [-n N]` | 获取用户微博 |
| `search <keyword> [-n N] [-p P] [--no-include-pics] [--include-profile]` | 搜索微博内容 |
| `users <keyword> [-n N] [-p P]` | 搜索用户 |
| `topics <keyword> [-n N] [-p P]` | 搜索话题 |
| `trending [-n N]` | 获取热搜 |
| `comments <feed_id> [-p P]` | 获取评论 |
| `followers <uid> [-n N] [-p P]` | 获取关注列表 |
| `fans <uid> [-n N] [-p P]` | 获取粉丝列表 |
| `login [--timeout SECONDS]` | 扫码登录并保存本机 CLI 会话 |
| `session` | 校验并显示当前本机 CLI 登录会话 |

## 常见流程

先搜索用户，再将结果中的 `id` 传给资料或动态命令：

```bash
weibo-cli users "雷军" -n 5
weibo-cli profile 1749127163
weibo-cli feeds 1749127163 -n 10
```

通过动态结果中的微博 `id` 获取评论：

```bash
weibo-cli comments 5173507416919189 -p 1
```

## 精简 feeds 输出

`feeds` 和 `search` 默认返回图片元数据，但默认不返回嵌套的 `user`。按需使用以下开关：

```bash
# 省略 pics
weibo-cli feeds 1749127163 --no-include-pics

# 包含每条微博的作者资料
weibo-cli feeds 1749127163 --include-profile

# 同时省略图片并包含作者资料
weibo-cli feeds 1749127163 --no-include-pics --include-profile

# 搜索结果同样支持这两个开关
weibo-cli search "雷军" --no-include-pics --include-profile
```

## 适用场景

- 在 shell 脚本中获取并处理 JSON；
- 临时查询用户、热搜、话题或微博内容；
- 不需要 AI 客户端编排工具调用的简单任务。
