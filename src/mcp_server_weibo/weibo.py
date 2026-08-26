import asyncio
import json
import httpx
import logging
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import qrcode

from mcp_server_weibo.consts import (
    COMMENTS_URL,
    DEFAULT_HEADERS,
    FEEDS_URL,
    DEFAULT_COOKIE_FILE,
    PASSPORT_HEADERS,
    PROFILE_URL,
    SEARCH_URL,
)
from mcp_server_weibo.converters import to_comment_item, to_feed_item, to_topic_item, to_trending_item, to_user_profile
from mcp_server_weibo.schemas import PagedFeeds, TrendingItem, FeedItem, UserProfile, CommentItem


class WeiboCrawler:
    """
    A crawler class for extracting data from Weibo (Chinese social media platform).
    Provides functionality to fetch user profiles, feeds, and search for users.

    Access cookies are generated automatically through Weibo's visitor passport.
    An optional QR-code login can persist an authenticated session locally.
    """
    def __init__(
        self,
        transport: httpx.AsyncBaseTransport | None = None,
        cookie_file: str | Path | None = None,
        load_persisted_session: bool = False,
    ):
        self.logger = logging.getLogger(__name__)
        self._cookie_file = Path(cookie_file) if cookie_file is not None else DEFAULT_COOKIE_FILE
        self.cookies = self._load_cookies() if load_persisted_session else None
        self._transport = transport
        self._cookie_lock = asyncio.Lock()

    def _create_client(
        self,
        *,
        cookies: dict | httpx.Cookies | None = None,
        follow_redirects: bool = False,
        headers: dict | None = None,
    ) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            cookies=cookies,
            follow_redirects=follow_redirects,
            headers=headers,
            trust_env=False,
            transport=self._transport,
        )

    def _load_cookies(self) -> httpx.Cookies | None:
        """Load a QR-login session created by this application, if available."""
        try:
            payload = json.loads(self._cookie_file.read_text(encoding="utf-8"))
            cookies = payload.get("cookies", payload)
            if isinstance(cookies, list):
                return self._cookies_from_records(cookies)
            # Compatibility with session files written by versions before 1.2.2.
            return httpx.Cookies(cookies) if isinstance(cookies, dict) and cookies else None
        except (OSError, ValueError, TypeError):
            return None

    def _save_cookies(self, cookies: httpx.Cookies) -> None:
        """Atomically save the local QR-login session with restrictive POSIX permissions."""
        self._cookie_file.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{self._cookie_file.name}.", dir=self._cookie_file.parent
        )
        try:
            if os.name != "nt":
                os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as temporary_file:
                json.dump({"cookies": self._cookie_records(cookies)}, temporary_file, ensure_ascii=False)
            os.replace(temporary_name, self._cookie_file)
        except Exception:
            try:
                os.close(fd)
            except OSError:
                pass
            try:
                os.unlink(temporary_name)
            except OSError:
                pass
            raise

    @staticmethod
    def _cookie_value(cookies: httpx.Cookies, name: str) -> str | None:
        for cookie in cookies.jar:
            if cookie.name == name:
                return cookie.value
        return None

    @staticmethod
    def _cookie_records(cookies: httpx.Cookies) -> list[dict[str, str]]:
        """Serialize cookies while preserving their domain and path scope."""
        return [
            {
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path,
            }
            for cookie in cookies.jar
        ]

    @staticmethod
    def _cookies_from_records(records: list[dict[str, str]]) -> httpx.Cookies:
        cookies = httpx.Cookies()
        for record in records:
            if not all(isinstance(record.get(key), str) for key in ("name", "value", "domain", "path")):
                raise ValueError("Invalid cookie record")
            cookies.set(record["name"], record["value"], domain=record["domain"], path=record["path"])
        return cookies

    @classmethod
    def _copy_cookies(cls, cookies: httpx.Cookies) -> httpx.Cookies:
        return cls._cookies_from_records(cls._cookie_records(cookies))

    async def _session_for_cookies(self, cookies: httpx.Cookies) -> dict | None:
        try:
            async with self._create_client(cookies=cookies) as client:
                response = await client.get("https://m.weibo.cn/api/config", headers=DEFAULT_HEADERS)
                response.raise_for_status()
                data = response.json().get("data", {})
                if data.get("login") and data.get("uid"):
                    session_cookies = self._copy_cookies(cookies)
                    if data.get("st"):
                        session_cookies.set("XSRF-TOKEN", str(data["st"]), domain="m.weibo.cn", path="/")
                    return {"uid": str(data["uid"]), "cookies": session_cookies}
        except (httpx.HTTPError, ValueError, TypeError):
            return None
        return None

    async def get_session(self) -> dict | None:
        """Return the authenticated local session, if the saved cookies remain valid."""
        if not self.cookies:
            return None
        session = await self._session_for_cookies(self.cookies)
        if session:
            self.cookies = session["cookies"]
            return {"login": True, "uid": session["uid"]}
        return None

    async def qr_login(self, timeout: int = 240) -> dict:
        """Log in through a user-confirmed QR scan and save the resulting session locally.

        QR protocol adapted from RicterZ/mcp-server-weibo (MIT License).
        """
        if timeout < 30 or timeout > 600:
            raise ValueError("timeout must be between 30 and 600 seconds")

        async with self._create_client(follow_redirects=True, headers=PASSPORT_HEADERS) as client:
            signin = await client.get(
                "https://passport.weibo.com/sso/signin",
                params={"entry": "miniblog", "source": "miniblog", "url": "https://weibo.com/"},
            )
            signin.raise_for_status()
            csrf_token = self._cookie_value(client.cookies, "X-CSRF-TOKEN")
            if csrf_token:
                client.headers["X-CSRF-TOKEN"] = csrf_token

            image = await client.get(
                "https://passport.weibo.com/sso/v2/qrcode/image",
                params={"entry": "miniblog", "size": "180"},
            )
            image.raise_for_status()
            image_data = image.json()
            if image_data.get("retcode") != 20000000:
                raise RuntimeError(f"Unable to request login QR code: {image_data}")
            qr_data = image_data.get("data", {})
            qrid = qr_data.get("qrid")
            if not qrid:
                raise RuntimeError("Login QR response did not include qrid")

            image_url = qr_data.get("image", "")
            scan_url = parse_qs(urlparse(image_url).query).get("data", [None])[0]
            scan_url = scan_url or f"https://passport.weibo.cn/signin/qrcode/scan?qr={qrid}"
            print("Scan this QR code with the Weibo app and confirm the login:")
            code = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, border=1)
            code.add_data(scan_url)
            code.print_ascii(invert=True)

            deadline = asyncio.get_running_loop().time() + timeout
            scanned = False
            while asyncio.get_running_loop().time() < deadline:
                check = await client.get(
                    "https://passport.weibo.com/sso/v2/qrcode/check",
                    params={"entry": "miniblog", "qrid": qrid, "rid": "", "ver": "20250520"},
                )
                check.raise_for_status()
                check_data = check.json()
                retcode = check_data.get("retcode")
                if retcode == 20000000:
                    data = check_data.get("data", {})
                    if data.get("url"):
                        login = await client.get(data["url"])
                    elif data.get("alt"):
                        login = await client.get(
                            "https://passport.weibo.com/sso/v2/login",
                            params={"entry": "miniblog", "alt": data["alt"], "returntype": "META"},
                        )
                    else:
                        raise RuntimeError("QR login confirmation did not include a login URL")
                    login.raise_for_status()
                    session = await self._session_for_cookies(client.cookies)
                    if not session:
                        raise RuntimeError("Weibo did not return a valid authenticated session")
                    self.cookies = session["cookies"]
                    self._save_cookies(self.cookies)
                    return {"login": True, "uid": session["uid"]}
                if retcode == 50114002 and not scanned:
                    print("QR code scanned; confirm the login in the Weibo app.")
                    scanned = True
                elif retcode == 50114004:
                    raise RuntimeError("QR code expired; run login again to request a new code")
                elif retcode != 50114001:
                    raise RuntimeError(f"Unexpected QR login status: {check_data}")
                await asyncio.sleep(2)

        raise TimeoutError("Timed out waiting for QR login confirmation")

    @staticmethod
    def _is_auth_failure(response: httpx.Response) -> bool:
        if response.status_code in (401, 403):
            return True
        if response.status_code in (301, 302, 303, 307, 308):
            location = response.headers.get("location", "").lower()
            return "passport.weibo.com" in location
        if response.status_code != 200:
            return False

        try:
            payload = response.json()
        except ValueError:
            return False

        if not isinstance(payload, dict):
            return False

        message = " ".join(
            str(payload.get(key, ""))
            for key in ("msg", "message", "error", "error_msg")
        ).lower()
        return any(marker in message for marker in ("登录", "登陆", "cookie", "visitor", "auth"))

    async def _invalidate_cookies(self, stale_cookies: httpx.Cookies | None) -> None:
        async with self._cookie_lock:
            if self.cookies is stale_cookies:
                self.cookies = None

    async def _get_json(self, client: httpx.AsyncClient, url: str) -> dict:
        response = await client.get(url, headers=DEFAULT_HEADERS)
        if self._is_auth_failure(response):
            stale_cookies = self.cookies
            await self._invalidate_cookies(stale_cookies)
            await self._ensure_cookies()
            client.cookies = self._copy_cookies(self.cookies)
            response = await client.get(url, headers=DEFAULT_HEADERS)
        response.raise_for_status()
        return response.json()
    
    async def _validate_cookies(self, cookies: httpx.Cookies) -> bool:
        try:
            async with self._create_client(cookies=cookies, follow_redirects=False) as client:
                response = await client.get("https://m.weibo.cn/", headers=DEFAULT_HEADERS)
                response.raise_for_status()
                location = response.headers.get("location", "")
                if response.status_code in (301, 302, 303, 307, 308) and "passport.weibo.com" in location:
                    return False
                return True
        except httpx.HTTPError:
            return False
        
    async def _ensure_cookies(self) -> dict:
        if self.cookies:
            return self.cookies

        async with self._cookie_lock:
            if self.cookies:
                return self.cookies

            for attempt in range(2):
                try:
                    async with self._create_client() as client:
                        response = await client.post(
                            "https://visitor.passport.weibo.cn/visitor/genvisitor2",
                            data={
                                "cb": "visitor_callback",
                                "from": "weibo",
                                "tid": "",
                                "return_url": "https://m.weibo.cn/",
                            },
                            headers={"User-Agent": DEFAULT_HEADERS.get("User-Agent", "")},
                        )
                        response.raise_for_status()
                        match = re.search(r"visitor_callback\((.*)\)", response.text)
                        if not match:
                            raise ValueError("Invalid visitor passport response")

                        payload = json.loads(match.group(1))
                        data = payload.get("data", {})
                        sub = data.get("sub")
                        subp = data.get("subp")
                        if not sub or not subp:
                            raise ValueError("Missing SUB/SUBP in visitor passport response")

                        generated = httpx.Cookies({"SUB": sub, "SUBP": subp})
                        if not await self._validate_cookies(generated):
                            raise ValueError("Generated visitor cookies are invalid")
                        self.cookies = generated
                        return self.cookies
                except (httpx.HTTPError, json.JSONDecodeError, ValueError):
                    self.logger.error("Unable to initialize Weibo visitor cookies", exc_info=True)
                    self.cookies = None
                    if attempt == 1:
                        raise


    async def get_profile(self, uid: int) -> UserProfile:
        """
        Extract user profile information from Weibo.

        Args:
            uid (int): The unique identifier of the Weibo user

        Returns:
            UserProfile: User profile information or empty dict if extraction fails
        """
        await self._ensure_cookies()
        async with self._create_client(cookies=self.cookies) as client:
            try:
                result = await self._get_json(client, PROFILE_URL.format(userId=uid))
                return to_user_profile(result["data"]["userInfo"])
            except (httpx.HTTPError, ValueError, KeyError, TypeError):
                self.logger.error(
                    f"Unable to extract profile for uid '{str(uid)}'", exc_info=True)
                return {}

    async def get_feeds(self, uid: int, limit: int=15) -> list[FeedItem]:
        """
        Extract user's Weibo feeds (posts) with pagination support.

        Args:
            uid (int): The unique identifier of the Weibo user
            limit (int): Maximum number of feeds to extract, defaults to 15

        Returns:
            list[FeedItem]: List of user's Weibo feeds
        """
        feeds=[]
        sinceId=''
        await self._ensure_cookies()
        async with self._create_client(cookies=self.cookies) as client:
            containerId=await self._get_container_id(client, uid)

            while len(feeds) < limit:
                pagedFeeds=await self._extract_feeds(client, uid, containerId, sinceId)
                if not pagedFeeds.Feeds:
                    break

                feeds.extend(pagedFeeds.Feeds)
                sinceId=pagedFeeds.SinceId
                if not sinceId:
                    break

        return feeds[:limit]

    async def get_hot_feeds(self, uid: int, limit: int=15) -> list[FeedItem]:
        """
        Extract hot feeds

        Args:
            uid (int): The unique identifier of the Weibo user
            limit (int): Maximum number of hot feeds to extract, defaults to 15

        Returns:
            list[FeedItem]: List of hot feeds from the user's profile
        """
        await self._ensure_cookies()
        async with self._create_client(cookies=self.cookies) as client:
            try:
                params={
                    'containerid': f'231002{str(uid)}_-_HOTMBLOG',
                    'type': 'uid',
                    'value': uid,
                }
                encoded_params=urlencode(params)

                result = await self._get_json(client, f'{SEARCH_URL}?{encoded_params}')
                cards=list(
                    filter(lambda x: x['card_type'] == 9, result["data"]["cards"]))
                feeds=[to_feed_item(item['mblog']) for item in cards]
                return feeds[:limit]
            except (httpx.HTTPError, ValueError, KeyError, TypeError):
                self.logger.error(
                    f"Unable to extract hot feeds for uid '{str(uid)}'", exc_info=True)
                return []

    async def search_users(self, keyword: str, limit: int=5, page: int=1) -> list[UserProfile]:
        """
        Search for Weibo users based on a keyword.

        Args:
            keyword (str): Search term to find users
            limit (int): Maximum number of users to return, defaults to 5

        Returns:
            list[UserProfile]: List of UserProfile objects containing user information
        """
        await self._ensure_cookies()
        async with self._create_client(cookies=self.cookies) as client:
            try:
                params={
                    'containerid': f'100103type=3&q={keyword}',
                    'page_type': 'searchall',
                    'page': page,
                }
                encoded_params=urlencode(params)

                result = await self._get_json(client, f'{SEARCH_URL}?{encoded_params}')
                cards=result["data"]["cards"]
                if len(cards) < 2:
                    return []
                else:
                    cardGroup=cards[1]['card_group']
                    return [to_user_profile(item['user']) for item in cardGroup][:limit]
            except (httpx.HTTPError, ValueError, KeyError, TypeError):
                self.logger.error(
                    f"Unable to search users for keyword '{keyword}'", exc_info=True)
                return []

    
    async def get_trendings(self, limit: int=15) -> list[TrendingItem]:
        """
        Get a list of hot search items from Weibo.

        Args:
            limit (int): Maximum number of hot search items to return, defaults to 15

        Returns:
            list[HotSearchItem]: List of HotSearchItem objects containing hot search information
        """
        try:
            params={
                'containerid': f'106003type=25&t=3&disable_hot=1&filter_type=realtimehot',
            }
            encoded_params=urlencode(params)

            await self._ensure_cookies()
            async with self._create_client(cookies=self.cookies) as client:
                data = await self._get_json(client, f'{SEARCH_URL}?{encoded_params}')
                cards=data.get('data', {}).get('cards', [])
                if not cards:
                    return []

                hot_search_card=next((card for card in cards if 'card_group' in card and isinstance(
                    card['card_group'], list)), None)
                if not hot_search_card or 'card_group' not in hot_search_card:
                    return []

                items=[item for item in hot_search_card['card_group']
                    if item.get('desc')]
                trending_items=list(map(lambda pair: to_trending_item(
                    {**pair[1], 'id': pair[0]}), enumerate(items[:limit])))
                return trending_items
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            self.logger.error(
                'Unable to fetch Weibo hot search list', exc_info=True)
            return []

    async def search_content(self, keyword: str, limit: int=15, page: int=1) -> list[FeedItem]:
        """
        Search Weibo content (posts) by keyword.

        Args:
            keyword (str): The search keyword
            limit (int): Maximum number of content results to return, defaults to 15
            page (int, optional): The starting page number, defaults to 1

        Returns:
            list[FeedItem]: List of FeedItem objects containing content search results
        """
        results=[]
        current_page=page
        try:
            await self._ensure_cookies()
            while len(results) < limit:
                params={
                    'containerid': f'100103type=1&q={keyword}',
                    'page_type': 'searchall',
                    'page': current_page,
                }
                encoded_params=urlencode(params)

                async with self._create_client(cookies=self.cookies) as client:
                    data = await self._get_json(client, f'{SEARCH_URL}?{encoded_params}')

                cards=data.get('data', {}).get('cards', [])
                content_cards=[]
                for card in cards:
                    if not isinstance(card, dict):
                        continue
                    if card.get('card_type') == 9:
                        content_cards.append(card)
                    elif 'card_group' in card and isinstance(card['card_group'], list):
                        content_group=[
                            item for item in card['card_group']
                            if isinstance(item, dict) and item.get('card_type') == 9]
                        content_cards.extend(content_group)

                if not content_cards:
                    break

                for card in content_cards:
                    if len(results) >= limit:
                        break

                    mblog=card.get('mblog')
                    if not isinstance(mblog, dict) or mblog.get('id') is None:
                        continue

                    try:
                        results.append(to_feed_item(mblog))
                    except (ValueError, KeyError, TypeError):
                        self.logger.warning("Skipping malformed Weibo search card", exc_info=True)

                current_page += 1
                cardlist_info=data.get('data', {}).get('cardlistInfo', {})
                if not cardlist_info.get('page') or str(cardlist_info.get('page')) == '1':
                    break
            return results[:limit]
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            self.logger.error(
                f"Unable to search Weibo content for keyword '{keyword}'", exc_info=True)
            return []

    async def search_topics(self, keyword: str, limit: int=15, page: int=1) -> list[dict]:
        """
        Search Weibo topics by keyword.

        Args:
            keyword (str): The search keyword
            limit (int): Maximum number of topic results to return, defaults to 15
            page (int, optional): The starting page number, defaults to 1

        Returns:
            list[dict: List of dict containing topic search results
        """
        await self._ensure_cookies()
        async with self._create_client(cookies=self.cookies) as client:
            try:
                params={
                    'containerid': f'100103type=38&q={keyword}',
                    'page_type': 'searchall',
                    'page': page,
                }
                encoded_params=urlencode(params)

                result = await self._get_json(client, f'{SEARCH_URL}?{encoded_params}')
                cards=result.get("data", {}).get("cards", [])
                for card in cards:
                    card_group=card.get('card_group')
                    if card_group:
                        return [to_topic_item(item) for item in card_group][:limit]
                return []
            except (httpx.HTTPError, ValueError, KeyError, TypeError):
                self.logger.error(
                    f"Unable to search topics for keyword '{keyword}'", exc_info=True)
                return []

    async def get_comments(self, feed_id: str, page: int=1) -> list[CommentItem]:
        """
        Get comments for a specific Weibo post.

        Args:
            feed_id (str): The ID of the Weibo post
            page (int): The page number for pagination, defaults to 1

        Returns:
            list[CommentItem]: List of comments for the specified Weibo post
        """
        try:
            await self._ensure_cookies()
            async with self._create_client(cookies=self.cookies) as client:
                url=COMMENTS_URL.format(feed_id=feed_id, page=page)
                data = await self._get_json(client, url)
                comments=data.get('data', {}).get('data', [])
                return [to_comment_item(comment) for comment in comments]
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            self.logger.error(
                f"Unable to fetch comments for feed_id '{feed_id}'", exc_info=True)
            return []

    async def get_followers(self, uid: int, limit: int=15, page: int=1) -> list[UserProfile]:
        """
        Get followers of a specific Weibo user.

        Args:
            uid (int): The unique identifier of the Weibo user
            limit (int): Maximum number of followers to return, defaults to 15
            page (int): The page number for pagination, defaults to 1

        Returns:
            list[UserProfile]: List of UserProfile objects containing follower information
        """
        await self._ensure_cookies()
        async with self._create_client(cookies=self.cookies) as client:
            try:
                params={
                    'containerid': f'231051_-_followers_-_{str(uid)}',
                    'page': page,
                }
                encoded_params=urlencode(params)

                result = await self._get_json(client, f'{SEARCH_URL}?{encoded_params}')
                cards=result["data"]["cards"]
                if len(cards) < 1:
                    return []
                else:
                    cardGroup=cards[-1]['card_group']
                    return [to_user_profile(item['user']) for item in cardGroup][:limit]
            except (httpx.HTTPError, ValueError, KeyError, TypeError):
                self.logger.error(
                    f"Unable to get followers for uid '{str(uid)}'", exc_info=True)
                return []

    async def get_fans(self, uid: int, limit: int=15, page: int=1) -> list[UserProfile]:
        """
        Get fans of a specific Weibo user.

        Args:
            uid (int): The unique identifier of the Weibo user
            limit (int): Maximum number of fans to return, defaults to 15
            page (int): The page number for pagination, defaults to 1

        Returns:
            list[UserProfile]: List of UserProfile objects containing fan information
        """
        await self._ensure_cookies()
        async with self._create_client(cookies=self.cookies) as client:
            try:
                params={
                    'containerid': f'231051_-_fans_-_{str(uid)}',
                    'page': page,
                }
                encoded_params=urlencode(params)

                result = await self._get_json(client, f'{SEARCH_URL}?{encoded_params}')
                cards=result["data"]["cards"]
                if len(cards) < 1:
                    return []
                else:
                    cardGroup=cards[-1]['card_group']
                    return [to_user_profile(item['user']) for item in cardGroup][:limit]
            except (httpx.HTTPError, ValueError, KeyError, TypeError):
                self.logger.error(
                    f"Unable to get fans for uid '{str(uid)}'", exc_info=True)
                return []

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
            data = await self._get_json(client, PROFILE_URL.format(userId=str(uid)))
            tabs_info=data.get("data", {}).get(
                "tabsInfo", {}).get("tabs", [])
            for tab in tabs_info:
                if tab.get("tabKey") == "weibo":
                    return tab.get("containerid")
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            self.logger.error(
                f"Unable to extract containerId for uid '{str(uid)}'", exc_info=True)
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
            url=FEEDS_URL.format(userId=str(
                uid), containerId=container_id, sinceId=since_id)
            data = await self._get_json(client, url)

            new_since_id=data.get("data", {}).get(
                "cardlistInfo", {}).get("since_id", "")
            cards=data.get("data", {}).get("cards", [])
            feeds=[]
            for card in cards:
                mblog = card.get("mblog")
                if not isinstance(mblog, dict) or mblog.get("id") is None:
                    continue
                try:
                    feeds.append(to_feed_item(mblog))
                except (ValueError, KeyError, TypeError):
                    self.logger.warning("Skipping malformed Weibo feed card", exc_info=True)

            return PagedFeeds(SinceId=new_since_id, Feeds=feeds)
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            self.logger.error(
                f"Unable to extract feeds for uid '{str(uid)}'", exc_info=True)
            return PagedFeeds(SinceId="", Feeds=[])
