from typing import Union
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """
    Data model for a Weibo user's profile information.

    Attributes:
        id (int): User's unique identifier
        screen_name (str): User's display name
        profile_image_url (str): URL to user's profile image
        profile_url (str): URL to user's Weibo profile page
        description (str): User's profile description
        follow_count (int): Number of users the user is following
        followers_count (str): Number of followers (as string)
        avatar_hd (str): URL to user's high-resolution avatar image
        verified (bool): Whether the user is verified
        verified_reason (str): Reason for verification
        gender (str): User's gender
    """

    id: int = Field()
    screen_name: str = Field()
    profile_image_url: str = Field()
    profile_url: str = Field()
    description: str = Field()
    follow_count: int = Field()
    followers_count: str = Field()
    avatar_hd: str = Field()
    verified: bool = Field()
    verified_reason: str = Field()
    gender: str = Field()


class FeedItem(BaseModel):
    """
    Data model for a single Weibo feed item.

    Attributes:
        id (int): Unique identifier for the feed item
        text (str): Content of the feed item
        source (str): Source of the feed (e.g., app or web)
        created_at (str): Timestamp when the feed was created
        user (Union[dict, UserProfile]): User information associated with the feed
        comments_count (int): Number of comments on the feed
        attitudes_count (int): Number of likes on the feed
        reposts_count (int): Number of reposts of the feed
        raw_text (str): Raw text content of the feed
        region_name (str): Region information
        pics (list[dict]): List of pictures in the feed
        videos (dict): Video information in the feed
    """

    id: int = Field()
    text: str = Field()
    source: str = Field()
    created_at: str = Field()
    user: Union[dict, UserProfile] = Field()
    comments_count: int = Field()
    attitudes_count: int = Field()
    reposts_count: int = Field()
    raw_text: str = Field()
    region_name: str = Field()
    pics: list[dict] = Field()
    videos: dict = Field()


class PagedFeeds(BaseModel):
    """
    Data model for paginated Weibo feeds.

    Attributes:
        SinceId (Union[int, str]): ID of the last feed for pagination
        Feeds (list[FeedItem]): List of Weibo feed entries
    """

    SinceId: Union[int, str] = Field()
    Feeds: list[FeedItem] = Field()


class TrendingItem(BaseModel):
    """
    Data model for a single hot search item on Weibo.

    Attributes:
        id (int): Rank of the search item
        trending (int): Popularity value of the hot search item
        description (str): The description of hot search item
        url (str): URL to the hot search item
    """

    id: int = Field()
    trending: int = Field()
    description: str = Field()
    url: str


class CommentItem(BaseModel):
    """
    Data model for a single comment on a Weibo post.

    Attributes:
        id (int): Unique identifier for the comment
        text (str): Content of the comment
        created_at (str): Timestamp when the comment was created
        user (UserProfile): User information associated with the comment
        like_count (int): Number of likes on the comment
        reply_count (int): Number of replies to the comment
    """

    id: int = Field()
    text: str = Field()
    created_at: str = Field()
    source: str = Field()
    user: UserProfile = Field()
    reply_id: Union[int, None] = Field(default=None)
    reply_text: str = Field(default="")
