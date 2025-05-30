from typing import Union
from pydantic import BaseModel, Field

class PagedFeeds(BaseModel):
    """
    Data model for paginated Weibo feeds.
    
    Attributes:
        SinceId (Union[int, str]): ID of the last feed for pagination
        Feeds (list[dict]): List of Weibo feed entries
    """
    SinceId: Union[int, str] = Field()
    Feeds: list[dict] = Field()

class SearchResult(BaseModel):
    """
    Data model for Weibo user search results.
    
    Attributes:
        id (int): User's unique identifier
        nickName (str): User's display name
        avatarHD (str): URL to user's high-resolution avatar image
        description (str): User's profile description
    """
    id: int = Field()
    nickName: str = Field()
    avatarHD: str = Field()
    description: str = Field()