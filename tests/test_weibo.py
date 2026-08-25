"""Offline unit tests for WeiboCrawler."""

import asyncio

import httpx
import pytest

from mcp_server_weibo.weibo import WeiboCrawler


def user(uid: int = 1) -> dict:
    return {
        "id": uid,
        "screen_name": "tester",
        "profile_image_url": "https://example.test/avatar.jpg",
        "profile_url": "https://m.weibo.cn/u/1",
    }


def feed(feed_id: int) -> dict:
    return {
        "id": feed_id,
        "text": "post",
        "source": "web",
        "created_at": "today",
        "user": user(),
    }


def crawler_for(handler) -> WeiboCrawler:
    return WeiboCrawler(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_ensure_cookies_generates_visitor_cookie_automatically():
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "visitor.passport.weibo.cn":
            return httpx.Response(200, text='visitor_callback({"data":{"sub":"sub-value","subp":"subp-value"}})')
        assert request.url.host == "m.weibo.cn"
        return httpx.Response(200)

    crawler = crawler_for(handler)
    await crawler._ensure_cookies()

    assert crawler.cookies == {"SUB": "sub-value", "SUBP": "subp-value"}


@pytest.mark.asyncio
async def test_concurrent_requests_share_one_cookie_generation():
    visitor_requests = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal visitor_requests
        if request.url.host == "visitor.passport.weibo.cn":
            visitor_requests += 1
            await asyncio.sleep(0.01)
            return httpx.Response(200, text='visitor_callback({"data":{"sub":"a","subp":"b"}})')
        return httpx.Response(200)

    crawler = crawler_for(handler)
    await asyncio.gather(*(crawler._ensure_cookies() for _ in range(10)))

    assert visitor_requests == 1


@pytest.mark.asyncio
async def test_get_feeds_honors_limit_when_page_contains_more_items():
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "visitor.passport.weibo.cn":
            return httpx.Response(200, text='visitor_callback({"data":{"sub":"a","subp":"b"}})')
        if request.url.path == "/":
            return httpx.Response(200)
        if request.url.params.get("containerid") is None:
            return httpx.Response(200, json={"data": {"tabsInfo": {"tabs": [{"tabKey": "weibo", "containerid": "1005051"}]}}})
        return httpx.Response(200, json={"data": {"cardlistInfo": {"since_id": ""}, "cards": [{"mblog": feed(1)}, {"mblog": feed(2)}]}})

    result = await crawler_for(handler).get_feeds(1, limit=1)

    assert [item.id for item in result] == [1]


@pytest.mark.asyncio
async def test_profile_returns_empty_dict_for_http_error():
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "visitor.passport.weibo.cn":
            return httpx.Response(200, text='visitor_callback({"data":{"sub":"a","subp":"b"}})')
        if request.url.path == "/":
            return httpx.Response(200)
        return httpx.Response(503, json={"error": "unavailable"})

    assert await crawler_for(handler).get_profile(1) == {}


@pytest.mark.asyncio
async def test_login_redirect_refreshes_cookie_and_retries_once():
    visitor_requests = 0
    profile_requests = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal visitor_requests, profile_requests
        if request.url.host == "visitor.passport.weibo.cn":
            visitor_requests += 1
            return httpx.Response(200, text=f'visitor_callback({{"data":{{"sub":"sub-{visitor_requests}","subp":"b"}}}})')
        if request.url.path == "/":
            return httpx.Response(200)
        profile_requests += 1
        if profile_requests == 1:
            return httpx.Response(302, headers={"Location": "https://passport.weibo.com/sso/signin"})
        return httpx.Response(200, json={"data": {"userInfo": user()}})

    result = await crawler_for(handler).get_profile(1)

    assert result.id == 1
    assert profile_requests == 2
    assert visitor_requests == 2


@pytest.mark.asyncio
async def test_rate_limit_does_not_refresh_cookie():
    visitor_requests = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal visitor_requests
        if request.url.host == "visitor.passport.weibo.cn":
            visitor_requests += 1
            return httpx.Response(200, text='visitor_callback({"data":{"sub":"a","subp":"b"}})')
        if request.url.path == "/":
            return httpx.Response(200)
        return httpx.Response(429, headers={"Retry-After": "60"})

    assert await crawler_for(handler).get_profile(1) == {}
    assert visitor_requests == 1


@pytest.mark.asyncio
async def test_search_users_returns_empty_list_for_invalid_json():
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "visitor.passport.weibo.cn":
            return httpx.Response(200, text='visitor_callback({"data":{"sub":"a","subp":"b"}})')
        if request.url.path == "/":
            return httpx.Response(200)
        return httpx.Response(200, content=b"not json")

    assert await crawler_for(handler).search_users("tester") == []
