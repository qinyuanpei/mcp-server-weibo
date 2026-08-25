# 数据 Schema 参考

本文档描述 `mcp-server-weibo` 对外返回的 JSON 数据结构。字段类型以 Python/Pydantic 类型表示；CLI 输出是这些模型序列化后的 JSON，MCP 工具返回相同结构。

除 `profile` 外，大多数 CLI 查询命令返回数组。字段会随微博接口实际数据而变化，本文仅承诺项目当前转换层输出的字段。

## 类型速览

| 记号 | JSON 类型 | 说明 |
|---|---|---|
| `int` | number | 整数标识、计数或排名。 |
| `str` | string | 文本、URL、时间字符串或平台原始格式化计数。 |
| `bool` | boolean | 真 / 假值。 |
| `list[T]` | array | 元素类型为 `T` 的数组。 |
| `dict` | object | 键和值未受进一步 schema 约束的对象。 |
| `T \| null` | value 或 null | 可为空的字段。 |

## `UserProfile`：用户资料

由 `profile`、`users`、`followers`、`fans` 返回；也可嵌套在微博和评论的 `user` 字段中。

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | `int` | 微博用户 UID。 |
| `screen_name` | `str` | 显示昵称。 |
| `profile_image_url` | `str` | 头像缩略图 URL。 |
| `profile_url` | `str` | 移动端个人主页 URL。 |
| `description` | `str` | 个人简介；未填写时为空字符串。 |
| `follow_count` | `int` | 该用户关注的人数。 |
| `followers_count` | `str` | 粉丝数。保留微博原始展示格式，例如 `"456"`、`"1.2万"`。 |
| `avatar_hd` | `str` | 高清头像 URL；可能为空字符串。 |
| `verified` | `bool` | 是否认证。 |
| `verified_reason` | `str` | 认证说明；未认证时通常为空字符串。 |
| `gender` | `str` | 性别标记，常见值为 `"m"`、`"f"` 或空字符串。 |

## `FeedItem`：微博

由 `feeds`、`search`、`get_hot_feeds`（MCP）返回。

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | `int` | 微博 MID。可作为 `comments` / `get_comments` 的输入。 |
| `text` | `str` | 微博正文的 HTML 富文本，可能含链接、表情或 `br` 标签。 |
| `source` | `str` | 发布来源，例如客户端、网页或设备名称。 |
| `created_at` | `str` | 微博接口提供的发布时间字符串，未强制转换为 ISO 8601。 |
| `user` | `UserProfile \| dict` | 作者资料。正常微博为 `UserProfile`；上游未提供作者时为 `{}`。CLI 的 `feeds` 与 `search` 默认省略该字段，使用 `--include-profile` 才输出。 |
| `comments_count` | `int` | 评论数。 |
| `attitudes_count` | `int` | 点赞数。 |
| `reposts_count` | `int` | 转发数。 |
| `raw_text` | `str` | 上游提供的纯文本正文；不可用时为空字符串。 |
| `region_name` | `str` | 发布地区描述；未提供时为空字符串。 |
| `pics` | `list[Picture]` | 图片元数据数组。CLI 的 `feeds` 与 `search` 默认输出，使用 `--no-include-pics` 可省略整个字段。 |
| `videos` | `dict` | 视频播放地址对象；非视频微博时为 `{}`。详见下文。 |

### `Picture`：图片对象

`pics` 中每个元素具有以下形状：

| 字段 | 类型 | 含义 |
|---|---|---|
| `thumbnail` | `str` | 缩略图 URL。 |
| `large` | `str` | 大图 URL。 |

### `videos`：视频对象

`videos` 没有固定的全部字段集合；它只会为微博接口实际提供的播放地址写入下列键。键存在但值为空字符串，表示上游未给出对应清晰度 URL。

| 字段 | 类型 | 含义 |
|---|---|---|
| `stream_url` | `str` | 标准视频流 URL。 |
| `stream_url_hd` | `str` | 高清视频流 URL。 |
| `mp4_720p_mp4` | `str` | 720p MP4 URL。 |
| `mp4_hd_mp4` | `str` | 高清 MP4 URL。 |
| `mp4_ld_mp4` | `str` | 低清 MP4 URL。 |

## `CommentItem`：评论

由 `comments` / `get_comments` 返回。

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | `int` | 评论 ID。 |
| `text` | `str` | 评论正文，可能为 HTML 富文本。 |
| `created_at` | `str` | 评论创建时间字符串。 |
| `source` | `str` | 评论发布来源；缺失时为空字符串。 |
| `user` | `UserProfile` | 评论作者资料。 |
| `reply_id` | `int \| null` | 被回复评论的 ID；非回复评论时为 `null`。 |
| `reply_text` | `str` | 被回复评论的文本；非回复评论时为空字符串。 |

## `TrendingItem`：热搜条目

由 `trending` / `get_trendings` 返回。

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | `int` | 当前列表中的从零开始排名，不是微博主题 ID。 |
| `trending` | `int` | 从热搜展示文本提取的热度数字；缺失或不可解析时为 `0`。 |
| `description` | `str` | 热搜词或描述。 |
| `url` | `str` | 热搜主题的微博跳转 URL；缺失时为空字符串。 |

## `Topic`：话题搜索结果

`topics` / `search_topics` 当前返回普通对象，而非 Pydantic 模型。

| 字段 | 类型 | 含义 |
|---|---|---|
| `title` | `str` | 话题标题。 |
| `desc1` | `str` | 第一行说明文本；可能为空字符串。 |
| `desc2` | `str` | 第二行说明文本；可能为空字符串。 |
| `url` | `str` | 话题跳转 URL；可能为空字符串。 |

## `PagedFeeds`：内部分页模型

该模型用于 crawler 内部翻页，不会直接由当前 CLI 命令或 MCP 工具返回。

| 字段 | 类型 | 含义 |
|---|---|---|
| `SinceId` | `int \| str` | 用于请求下一页的游标；没有下一页时通常为空字符串。 |
| `Feeds` | `list[FeedItem]` | 当前页已转换的微博数组。 |

## 命令与返回类型

| CLI 命令 | MCP 工具 | 返回类型 |
|---|---|---|
| `profile <uid>` | `get_profile` | `UserProfile` |
| `feeds <uid>` | `get_feeds` | `list[FeedItem]` |
| — | `get_hot_feeds` | `list[FeedItem]` |
| `search <keyword>` | `search_content` | `list[FeedItem]` |
| `users <keyword>` | `search_users` | `list[UserProfile]` |
| `topics <keyword>` | `search_topics` | `list[Topic]` |
| `trending` | `get_trendings` | `list[TrendingItem]` |
| `comments <feed_id>` | `get_comments` | `list[CommentItem]` |
| `followers <uid>` | `get_followers` | `list[UserProfile]` |
| `fans <uid>` | `get_fans` | `list[UserProfile]` |
