#!/usr/bin/env python
"""
Weibo CLI - Command line interface for Weibo operations
"""

import asyncio
import json
import sys

import click

from mcp_server_weibo.weibo import WeiboCrawler

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


@click.group()
@click.version_option(version="1.3.2")
def cli():
    """Weibo CLI - Interact with Weibo from the command line"""
    pass


def print_json(value):
    """Print one valid JSON document to stdout."""
    print(json.dumps(value, ensure_ascii=False, indent=2))


def create_cli_crawler():
    """Create a crawler that may reuse this CLI user's QR-login session."""
    return WeiboCrawler(load_persisted_session=True)


@cli.command()
@click.option(
    "--timeout",
    default=240,
    show_default=True,
    type=click.IntRange(30, 600),
    help="Seconds to wait for QR scan confirmation",
)
def login(timeout):
    """Log in by scanning a QR code and save the local session."""

    async def run():
        result = await create_cli_crawler().qr_login(timeout)
        print_json(result)

    asyncio.run(run())


@cli.command()
def session():
    """Show the current local CLI login session, if it is valid."""

    async def run():
        print_json(await create_cli_crawler().get_session())

    asyncio.run(run())


@cli.command()
@click.argument("uid", type=int)
@click.option("--limit", "-n", default=15, help="Number of feeds to fetch")
@click.option(
    "--include-pics/--no-include-pics",
    default=True,
    help="Include picture metadata in output",
)
@click.option(
    "--include-profile/--no-include-profile",
    default=False,
    help="Include author profile in output",
)
def feeds(uid, limit, include_pics, include_profile):
    """Get user feeds by UID"""

    async def run():
        crawler = create_cli_crawler()
        results = await crawler.get_feeds(uid, limit)
        excluded_fields = set()
        if not include_pics:
            excluded_fields.add("pics")
        if not include_profile:
            excluded_fields.add("user")
        print_json([item.model_dump(exclude=excluded_fields) for item in results])

    asyncio.run(run())


@cli.command()
@click.argument("keyword")
@click.option("--limit", "-n", default=15, help="Number of results to return")
@click.option("--page", "-p", default=1, help="Page number")
@click.option(
    "--include-pics/--no-include-pics",
    default=True,
    help="Include picture metadata in output",
)
@click.option(
    "--include-profile/--no-include-profile",
    default=False,
    help="Include author profile in output",
)
def search(keyword, limit, page, include_pics, include_profile):
    """Search Weibo content by keyword"""

    async def run():
        crawler = create_cli_crawler()
        results = await crawler.search_content(keyword, limit, page)
        excluded_fields = set()
        if not include_pics:
            excluded_fields.add("pics")
        if not include_profile:
            excluded_fields.add("user")
        print_json([item.model_dump(exclude=excluded_fields) for item in results])

    asyncio.run(run())


@cli.command()
@click.argument("keyword")
@click.option("--limit", "-n", default=5, help="Number of results to return")
@click.option("--page", "-p", default=1, help="Page number")
def users(keyword, limit, page):
    """Search Weibo users by keyword"""

    async def run():
        crawler = create_cli_crawler()
        results = await crawler.search_users(keyword, limit, page)
        print_json([item.model_dump() for item in results])

    asyncio.run(run())


@cli.command()
@click.argument("keyword")
@click.option("--limit", "-n", default=15, help="Number of results to return")
@click.option("--page", "-p", default=1, help="Page number")
def topics(keyword, limit, page):
    """Search Weibo topics by keyword"""

    async def run():
        crawler = create_cli_crawler()
        results = await crawler.search_topics(keyword, limit, page)
        print_json(results)

    asyncio.run(run())


@cli.command()
@click.option("--limit", "-n", default=15, help="Number of trending items to return")
def trending(limit):
    """Get Weibo trending hot searches"""

    async def run():
        crawler = create_cli_crawler()
        results = await crawler.get_trendings(limit)
        print_json([item.model_dump() for item in results])

    asyncio.run(run())


@cli.command()
@click.argument("uid", type=int)
def profile(uid):
    """Get user profile by UID"""

    async def run():
        crawler = create_cli_crawler()
        result = await crawler.get_profile(uid)
        print_json(result.model_dump() if hasattr(result, "model_dump") else result)

    asyncio.run(run())


@cli.command()
@click.argument("feed_id", type=str)
@click.option("--page", "-p", default=1, help="Page number")
def comments(feed_id, page):
    """Get comments for a Weibo post"""

    async def run():
        crawler = create_cli_crawler()
        results = await crawler.get_comments(feed_id, page)
        print_json([item.model_dump() for item in results])

    asyncio.run(run())


@cli.command()
@click.argument("uid", type=int)
@click.option("--limit", "-n", default=15, help="Number of followers to return")
@click.option("--page", "-p", default=1, help="Page number")
def followers(uid, limit, page):
    """Get user's followers"""

    async def run():
        crawler = create_cli_crawler()
        results = await crawler.get_followers(uid, limit, page)
        print_json([item.model_dump() for item in results])

    asyncio.run(run())


@cli.command()
@click.argument("uid", type=int)
@click.option("--limit", "-n", default=15, help="Number of fans to return")
@click.option("--page", "-p", default=1, help="Page number")
def fans(uid, limit, page):
    """Get user's fans"""

    async def run():
        crawler = create_cli_crawler()
        results = await crawler.get_fans(uid, limit, page)
        print_json([item.model_dump() for item in results])

    asyncio.run(run())


if __name__ == "__main__":
    cli()
