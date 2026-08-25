# Schema Reference

This document describes the public JSON structures returned by `mcp-server-weibo`. Types use Python/Pydantic notation; CLI output is the JSON serialization of these models, and MCP tools return the same shapes.

Except for `profile`, most CLI commands return an array. Fields depend on data supplied by Weibo; this document covers the fields emitted by the current conversion layer.

## Type notation

| Notation | JSON type | Meaning |
|---|---|---|
| `int` | number | An integer identifier, count, or rank. |
| `str` | string | Text, URL, timestamp string, or platform-formatted count. |
| `bool` | boolean | A true/false value. |
| `list[T]` | array | An array whose elements have type `T`. |
| `dict` | object | An object without a further constrained schema. |
| `T \| null` | value or null | A nullable field. |

## `UserProfile`

Returned by `profile`, `users`, `followers`, and `fans`; it may also be nested in a feed or comment's `user` field.

| Field | Type | Meaning |
|---|---|---|
| `id` | `int` | Weibo user UID. |
| `screen_name` | `str` | Display name. |
| `profile_image_url` | `str` | Avatar thumbnail URL. |
| `profile_url` | `str` | Mobile profile-page URL. |
| `description` | `str` | Profile description; empty when absent. |
| `follow_count` | `int` | Number of accounts followed by this user. |
| `followers_count` | `str` | Follower count in Weibo's display format, such as `"456"` or `"1.2万"`. |
| `avatar_hd` | `str` | High-resolution avatar URL; may be empty. |
| `verified` | `bool` | Whether the account is verified. |
| `verified_reason` | `str` | Verification label; usually empty for an unverified account. |
| `gender` | `str` | Gender marker, commonly `"m"`, `"f"`, or an empty string. |

## `FeedItem`

Returned by `feeds`, `search`, and MCP `get_hot_feeds`.

| Field | Type | Meaning |
|---|---|---|
| `id` | `int` | Weibo MID. It can be passed to `comments` / `get_comments`. |
| `text` | `str` | HTML-rich post body; may contain links, emoji markup, and `br` tags. |
| `source` | `str` | Publishing source, such as an app, device, or web client. |
| `created_at` | `str` | Timestamp string supplied by Weibo; it is not normalized to ISO 8601. |
| `user` | `UserProfile \| dict` | Author profile. It is normally a `UserProfile`, or `{}` when upstream data has no author. CLI `feeds` and `search` omit it by default; use `--include-profile` to include it. |
| `comments_count` | `int` | Comment count. |
| `attitudes_count` | `int` | Like count. |
| `reposts_count` | `int` | Repost count. |
| `raw_text` | `str` | Upstream plain-text body; empty when unavailable. |
| `region_name` | `str` | Publishing-region description; empty when absent. |
| `pics` | `list[Picture]` | Picture metadata. CLI `feeds` and `search` include it by default; use `--no-include-pics` to omit the whole field. |
| `videos` | `dict` | Video playback object; `{}` for a non-video post. See below. |

### `Picture`

Each item in `pics` has this shape:

| Field | Type | Meaning |
|---|---|---|
| `thumbnail` | `str` | Thumbnail URL. |
| `large` | `str` | Large-image URL. |

### `videos`

`videos` has no single fixed key set. It contains only the playback URLs supplied by Weibo. A present key with an empty string means that the source did not provide that quality.

| Field | Type | Meaning |
|---|---|---|
| `stream_url` | `str` | Standard video-stream URL. |
| `stream_url_hd` | `str` | High-definition video-stream URL. |
| `mp4_720p_mp4` | `str` | 720p MP4 URL. |
| `mp4_hd_mp4` | `str` | HD MP4 URL. |
| `mp4_ld_mp4` | `str` | Low-definition MP4 URL. |

## `CommentItem`

Returned by `comments` / `get_comments`.

| Field | Type | Meaning |
|---|---|---|
| `id` | `int` | Comment ID. |
| `text` | `str` | Comment body, which may be HTML-rich text. |
| `created_at` | `str` | Comment creation-time string. |
| `source` | `str` | Publishing source; empty when absent. |
| `user` | `UserProfile` | Comment author profile. |
| `reply_id` | `int \| null` | ID of the comment being replied to; `null` for a top-level comment. |
| `reply_text` | `str` | Text of the replied-to comment; empty for a top-level comment. |

## `TrendingItem`

Returned by `trending` / `get_trendings`.

| Field | Type | Meaning |
|---|---|---|
| `id` | `int` | Zero-based rank in the current result list, not a Weibo topic ID. |
| `trending` | `int` | Popularity number extracted from the displayed trending text; `0` when unavailable or unparsable. |
| `description` | `str` | Trending term or description. |
| `url` | `str` | Weibo URL for the trend; empty when absent. |

## `Topic`

`topics` / `search_topics` currently returns ordinary objects rather than a Pydantic model.

| Field | Type | Meaning |
|---|---|---|
| `title` | `str` | Topic title. |
| `desc1` | `str` | First descriptive line; may be empty. |
| `desc2` | `str` | Second descriptive line; may be empty. |
| `url` | `str` | Topic URL; may be empty. |

## `PagedFeeds` (internal)

This model supports crawler pagination and is not returned directly by the current CLI or MCP tools.

| Field | Type | Meaning |
|---|---|---|
| `SinceId` | `int \| str` | Cursor for the next page; usually an empty string when there is no next page. |
| `Feeds` | `list[FeedItem]` | Converted feeds from the current page. |

## Command-to-schema mapping

| CLI command | MCP tool | Return type |
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
