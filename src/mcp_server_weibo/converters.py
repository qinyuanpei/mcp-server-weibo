"""Conversion helpers for normalizing Weibo API responses."""

import re

from mcp_server_weibo.schemas import CommentItem, FeedItem, TrendingItem, UserProfile


def to_trending_item(item: dict) -> TrendingItem:
    """Convert a raw hot-search item to a TrendingItem."""
    extr_values = re.findall(r"\d+", str(item.get("desc_extr")))
    return TrendingItem(
        id=item["id"],
        trending=int(extr_values[0]) if extr_values else 0,
        description=item["desc"],
        url=item.get("scheme", ""),
    )


def to_feed_item(mblog: dict) -> FeedItem:
    """Convert a raw Weibo post to a FeedItem."""
    source_pics = [pic for pic in mblog.get("pics", []) if "url" in pic]
    pics = [
        {"thumbnail": pic["url"], "large": pic["large"]["url"]}
        for pic in source_pics
    ]

    videos = {}
    page_info = mblog.get("page_info")
    if page_info and page_info.get("type") == "video":
        if "media_info" in page_info:
            videos["stream_url"] = page_info["media_info"].get("stream_url", "")
            videos["stream_url_hd"] = page_info["media_info"].get("stream_url_hd", "")
        elif "urls" in page_info:
            videos["mp4_720p_mp4"] = page_info["urls"].get("mp4_720p_mp4", "")
            videos["mp4_hd_mp4"] = page_info["urls"].get("mp4_hd_mp4", "")
            videos["mp4_ld_mp4"] = page_info["urls"].get("mp4_ld_mp4", "")

    user = to_user_profile(mblog["user"]) if mblog.get("user") else {}
    return FeedItem(
        id=mblog.get("id"),
        text=mblog.get("text"),
        source=mblog.get("source"),
        created_at=mblog.get("created_at"),
        user=user,
        comments_count=mblog.get("comments_count", 0),
        attitudes_count=mblog.get("attitudes_count", 0),
        reposts_count=mblog.get("reposts_count", 0),
        raw_text=mblog.get("raw_text", ""),
        region_name=mblog.get("region_name", ""),
        pics=pics,
        videos=videos,
    )


def to_user_profile(user: dict) -> UserProfile:
    """Convert raw user data to a UserProfile."""
    return UserProfile(
        id=user["id"],
        screen_name=user["screen_name"],
        profile_image_url=user["profile_image_url"],
        profile_url=user["profile_url"],
        description=user.get("description", ""),
        follow_count=user.get("follow_count", 0),
        followers_count=user.get("followers_count", ""),
        avatar_hd=user.get("avatar_hd", ""),
        verified=user.get("verified", False),
        verified_reason=user.get("verified_reason", ""),
        gender=user.get("gender", ""),
    )


def to_topic_item(item: dict) -> dict:
    """Convert raw topic data to the public topic shape."""
    return {
        "title": item["title_sub"],
        "desc1": item.get("desc1", ""),
        "desc2": item.get("desc2", ""),
        "url": item.get("scheme", ""),
    }


def to_comment_item(item: dict) -> CommentItem:
    """Convert raw comment data to a CommentItem."""
    return CommentItem(
        id=item.get("id"),
        text=item.get("text"),
        created_at=item.get("created_at"),
        user=to_user_profile(item.get("user", {})),
        source=item.get("source", ""),
        reply_id=item.get("reply_id"),
        reply_text=item.get("reply_text", ""),
    )
