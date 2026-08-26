"""Offline unit tests for WeiboCrawler."""

import asyncio
import json

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


def test_loads_persisted_qr_session(tmp_path):
    cookie_file = tmp_path / "cookies.json"
    cookie_file.write_text(
        json.dumps({"cookies": {"SUB": "saved-session"}}), encoding="utf-8"
    )

    crawler = WeiboCrawler(cookie_file=cookie_file, load_persisted_session=True)

    assert crawler.cookies["SUB"] == "saved-session"


def test_default_crawler_does_not_load_cli_qr_session(tmp_path):
    cookie_file = tmp_path / "cookies.json"
    cookie_file.write_text(
        json.dumps({"cookies": {"SUB": "saved-session"}}), encoding="utf-8"
    )

    crawler = WeiboCrawler(cookie_file=cookie_file)

    assert crawler.cookies is None


def test_preserves_same_name_cookies_with_their_domains():
    cookies = httpx.Cookies()
    cookies.set("ALC", "first", domain="passport.weibo.com")
    cookies.set("ALC", "second", domain="weibo.com")

    records = WeiboCrawler._cookie_records(cookies)
    restored = WeiboCrawler._cookies_from_records(records)

    assert [
        (cookie.domain, cookie.value) for cookie in restored.jar if cookie.name == "ALC"
    ] == [
        ("passport.weibo.com", "first"),
        ("weibo.com", "second"),
    ]


@pytest.mark.asyncio
async def test_qr_login_saves_validated_session(tmp_path, monkeypatch):
    cookie_file = tmp_path / "cookies.json"

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/sso/signin":
            return httpx.Response(
                200, headers={"Set-Cookie": "X-CSRF-TOKEN=csrf; Path=/"}
            )
        if request.url.path == "/sso/v2/qrcode/image":
            return httpx.Response(
                200,
                json={
                    "retcode": 20000000,
                    "data": {
                        "qrid": "qr-id",
                        "image": "https://example.test/qr?data=https%3A%2F%2Fscan.test%2Fqr",
                    },
                },
            )
        if request.url.path == "/sso/v2/qrcode/check":
            return httpx.Response(
                200, json={"retcode": 20000000, "data": {"alt": "alt-token"}}
            )
        if request.url.path == "/sso/v2/login":
            return httpx.Response(
                200, headers={"Set-Cookie": "SUB=authenticated; Path=/"}
            )
        assert request.url.path == "/api/config"
        return httpx.Response(
            200, json={"data": {"login": True, "uid": "42", "st": "xsrf"}}
        )

    monkeypatch.setattr(
        "mcp_server_weibo.weibo.qrcode.QRCode.print_ascii",
        lambda *_args, **_kwargs: None,
    )
    crawler = WeiboCrawler(
        transport=httpx.MockTransport(handler), cookie_file=cookie_file
    )

    assert await crawler.qr_login(timeout=30) == {"login": True, "uid": "42"}
    assert crawler.cookies["SUB"] == "authenticated"
    assert crawler.cookies.get("XSRF-TOKEN", domain="m.weibo.cn", path="/") == "xsrf"
    saved = json.loads(cookie_file.read_text(encoding="utf-8"))["cookies"]
    assert any(
        record["name"] == "SUB" and record["value"] == "authenticated"
        for record in saved
    )


@pytest.mark.asyncio
async def test_ensure_cookies_generates_visitor_cookie_automatically():
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "visitor.passport.weibo.cn":
            return httpx.Response(
                200,
                text='visitor_callback({"data":{"sub":"sub-value","subp":"subp-value"}})',
            )
        assert request.url.host == "m.weibo.cn"
        return httpx.Response(200)

    crawler = crawler_for(handler)
    await crawler._ensure_cookies()

    assert dict(crawler.cookies) == {"SUB": "sub-value", "SUBP": "subp-value"}


@pytest.mark.asyncio
async def test_concurrent_requests_share_one_cookie_generation():
    visitor_requests = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal visitor_requests
        if request.url.host == "visitor.passport.weibo.cn":
            visitor_requests += 1
            await asyncio.sleep(0.01)
            return httpx.Response(
                200, text='visitor_callback({"data":{"sub":"a","subp":"b"}})'
            )
        return httpx.Response(200)

    crawler = crawler_for(handler)
    await asyncio.gather(*(crawler._ensure_cookies() for _ in range(10)))

    assert visitor_requests == 1


@pytest.mark.asyncio
async def test_get_feeds_honors_limit_when_page_contains_more_items():
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "visitor.passport.weibo.cn":
            return httpx.Response(
                200, text='visitor_callback({"data":{"sub":"a","subp":"b"}})'
            )
        if request.url.path == "/":
            return httpx.Response(200)
        if request.url.params.get("containerid") is None:
            return httpx.Response(
                200,
                json={
                    "data": {
                        "tabsInfo": {
                            "tabs": [{"tabKey": "weibo", "containerid": "1005051"}]
                        }
                    }
                },
            )
        return httpx.Response(
            200,
            json={
                "data": {
                    "cardlistInfo": {"since_id": ""},
                    "cards": [{"mblog": feed(1)}, {"mblog": feed(2)}],
                }
            },
        )

    result = await crawler_for(handler).get_feeds(1, limit=1)

    assert [item.id for item in result] == [1]


@pytest.mark.asyncio
async def test_get_feeds_skips_non_feed_cards_without_dropping_valid_feeds():
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "visitor.passport.weibo.cn":
            return httpx.Response(
                200, text='visitor_callback({"data":{"sub":"a","subp":"b"}})'
            )
        if request.url.path == "/":
            return httpx.Response(200)
        if request.url.params.get("containerid") is None:
            return httpx.Response(
                200,
                json={
                    "data": {
                        "tabsInfo": {
                            "tabs": [{"tabKey": "weibo", "containerid": "1005051"}]
                        }
                    }
                },
            )
        return httpx.Response(
            200,
            json={
                "data": {
                    "cardlistInfo": {"since_id": ""},
                    "cards": [
                        {"card_type": 8, "title": "profile header"},
                        {"card_type": 9, "mblog": feed(1)},
                        {"card_type": 11, "card_group": []},
                    ],
                }
            },
        )

    result = await crawler_for(handler).get_feeds(1)

    assert [item.id for item in result] == [1]


@pytest.mark.asyncio
async def test_search_skips_malformed_cards_without_dropping_valid_results():
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "visitor.passport.weibo.cn":
            return httpx.Response(
                200, text='visitor_callback({"data":{"sub":"a","subp":"b"}})'
            )
        if request.url.path == "/":
            return httpx.Response(200)
        return httpx.Response(
            200,
            json={
                "data": {
                    "cardlistInfo": {"page": "1"},
                    "cards": [
                        {"card_type": 9, "mblog": {"id": 99}},
                        {"card_type": 8, "title": "search header"},
                        {
                            "card_type": 11,
                            "card_group": [
                                "not-a-card",
                                {"card_type": 9, "mblog": feed(2)},
                            ],
                        },
                    ],
                }
            },
        )

    result = await crawler_for(handler).search_content("tester", limit=2)

    assert [item.id for item in result] == [2]


@pytest.mark.asyncio
async def test_profile_returns_empty_dict_for_http_error():
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "visitor.passport.weibo.cn":
            return httpx.Response(
                200, text='visitor_callback({"data":{"sub":"a","subp":"b"}})'
            )
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
            return httpx.Response(
                200,
                text=f'visitor_callback({{"data":{{"sub":"sub-{visitor_requests}","subp":"b"}}}})',
            )
        if request.url.path == "/":
            return httpx.Response(200)
        profile_requests += 1
        if profile_requests == 1:
            return httpx.Response(
                302, headers={"Location": "https://passport.weibo.com/sso/signin"}
            )
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
            return httpx.Response(
                200, text='visitor_callback({"data":{"sub":"a","subp":"b"}})'
            )
        if request.url.path == "/":
            return httpx.Response(200)
        return httpx.Response(429, headers={"Retry-After": "60"})

    assert await crawler_for(handler).get_profile(1) == {}
    assert visitor_requests == 1


@pytest.mark.asyncio
async def test_search_users_returns_empty_list_for_invalid_json():
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "visitor.passport.weibo.cn":
            return httpx.Response(
                200, text='visitor_callback({"data":{"sub":"a","subp":"b"}})'
            )
        if request.url.path == "/":
            return httpx.Response(200)
        return httpx.Response(200, content=b"not json")

    assert await crawler_for(handler).search_users("tester") == []
