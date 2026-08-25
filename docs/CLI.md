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

## 输出格式

`profile` 输出一个 JSON 对象。其他命令都输出一个完整 JSON 数组；没有结果时输出 `[]`，可直接由 `jq`、Python 或其他 JSON 工具解析。

```bash
weibo-cli trending -n 3
```

## 命令

| 命令 | 说明 |
|---|---|
| `profile <uid>` | 获取用户资料 |
| `feeds <uid> [-n N]` | 获取用户微博 |
| `search <keyword> [-n N] [-p P]` | 搜索微博内容 |
| `users <keyword> [-n N] [-p P]` | 搜索用户 |
| `topics <keyword> [-n N] [-p P]` | 搜索话题 |
| `trending [-n N]` | 获取热搜 |
| `comments <feed_id> [-p P]` | 获取评论 |
| `followers <uid> [-n N] [-p P]` | 获取关注列表 |
| `fans <uid> [-n N] [-p P]` | 获取粉丝列表 |

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

`feeds` 默认返回图片元数据，但默认不返回嵌套的 `user`。按需使用以下开关：

```bash
# 省略 pics
weibo-cli feeds 1749127163 --no-include-pics

# 包含每条微博的作者资料
weibo-cli feeds 1749127163 --include-profile

# 同时省略图片并包含作者资料
weibo-cli feeds 1749127163 --no-include-pics --include-profile
```

## 适用场景

- 在 shell 脚本中获取并处理 JSON；
- 临时查询用户、热搜、话题或微博内容；
- 不需要 AI 客户端编排工具调用的简单任务。
