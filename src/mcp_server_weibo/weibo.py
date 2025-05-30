import httpx
import logging
from urllib.parse import urlencode
from .consts import DEFAULT_HEADERS, PROFILE_URL, FEEDS_URL
from .schemas import PagedFeeds, SearchResult

class WeiboCrawler:
    """
    A crawler class for extracting data from Weibo (Chinese social media platform).
    Provides functionality to fetch user profiles, feeds, and search for users.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def extract_weibo_profile(self, uid: int) -> dict:
        """
        Extract user profile information from Weibo.
        
        Args:
            uid (int): The unique identifier of the Weibo user
            
        Returns:
            dict: User profile information or empty dict if extraction fails
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(PROFILE_URL.format(userId=uid), headers=DEFAULT_HEADERS)
                result = response.json()
                return result["data"]["userInfo"]
            except httpx.HTTPError:
                self.logger.error(f"Unable to eextract profile for uid '{str(uid)}'", exc_info=True)
                return {}

    async def extract_weibo_feeds(self, uid: int, limit: int) -> list[dict]:
        """
        Extract user's Weibo feeds (posts) with pagination support.
        
        Args:
            uid (int): The unique identifier of the Weibo user
            limit (int): Maximum number of feeds to extract
            
        Returns:
            list: List of user's Weibo feeds
        """
        feeds = []
        sinceId = ''
        async with httpx.AsyncClient() as client:
            containerId = await self._get_container_id(client, uid)

            while len(feeds) < limit:
                pagedFeeds = await self._extract_feeds(client, uid, containerId, sinceId)
                if not pagedFeeds.Feeds:
                    break

                feeds.extend(pagedFeeds.Feeds)
                sinceId = pagedFeeds.SinceId
                if not sinceId:
                    break
                
        return feeds

    async def search_weibo_users(self, keyword: str, limit: int) -> list[SearchResult]:
        """
        Search for Weibo users based on a keyword.
        
        Args:
            keyword (str): Search term to find users
            limit (int): Maximum number of users to return
            
        Returns:
            list: List of SearchResult objects containing user information
        """
        async with httpx.AsyncClient() as client:
            try:
                params = {'containerid': f'100103type=3&q={keyword}&t=', 'page_type': 'searchall'}
                encoded_params = urlencode(params)

                response = await client.get(f'https://m.weibo.cn/api/container/getIndex?{encoded_params}', headers=DEFAULT_HEADERS)
                result = response.json()
                cards = result["data"]["cards"]
                if len(cards) < 2:
                    return []
                else:
                    cardGroup = cards[1]['card_group']
                    return [self._to_search_result(item['user']) for item in cardGroup][:limit]
            except httpx.HTTPError:
                self.logger.error(f"Unable to search users for keyword '{keyword}'", exc_info=True)
                return []

    def _to_search_result(self, user: dict) -> SearchResult:
        """
        Convert raw user data to SearchResult object.
        
        Args:
            user (dict): Raw user data from Weibo API
            
        Returns:
            SearchResult: Formatted user information
        """
        return SearchResult(
            id=user['id'], 
            nickName=user['screen_name'], 
            avatarHD=user['avatar_hd'],
            description=user['description']
        )
        
    async def _get_container_id(self, client, uid: int):
        """
        Get the container ID for a user's Weibo feed.
        
        Args:
            client (httpx.AsyncClient): HTTP client instance
            uid (int): The unique identifier of the Weibo user
            
        Returns:
            str: Container ID for the user's feed or None if extraction fails
        """
        try:
            response = await client.get(PROFILE_URL.format(userId=str(uid)), headers=DEFAULT_HEADERS)
            data = response.json()
            tabs_info = data.get("data", {}).get("tabsInfo", {}).get("tabs", [])
            for tab in tabs_info:
                if tab.get("tabKey") == "weibo":
                    return tab.get("containerid")
        except httpx.HTTPError:
            self.logger.error(f"Unable to extract containerId for uid '{str(uid)}'", exc_info=True)
            return None

    async def _extract_feeds(self, client, uid: int, container_id: str, since_id: str):
        """
        Extract a single page of Weibo feeds for a user.
        
        Args:
            client (httpx.AsyncClient): HTTP client instance
            uid (int): The unique identifier of the Weibo user
            container_id (str): Container ID for the user's feed
            since_id (str): ID of the last feed for pagination
            
        Returns:
            PagedFeeds: Object containing feeds and next page's since_id
        """
        try:
            url = FEEDS_URL.format(userId=str(uid), containerId=container_id, sinceId=since_id)
            response = await client.get(url, headers = DEFAULT_HEADERS)
            data = response.json()
            new_since_id = data.get("data", {}).get("cardlistInfo", {}).get("since_id", "")
            cards = data.get("data", {}).get("cards", [])
            mblogs = cards
            
            if mblogs:
                return PagedFeeds(SinceId=new_since_id, Feeds=mblogs)
            else:
                return PagedFeeds(SinceId=new_since_id, Feeds=[])
        except httpx.HTTPError:
            self.logger.error(f"Unable to extract feeds for uid '{str(uid)}'", exc_info=True)
            return PagedFeeds(SinceId=None, Feeds=[])
