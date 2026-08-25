#!/usr/bin/env python
"""
Weibo CLI - Command line interface for Weibo operations
"""
import asyncio
import json
import click
from mcp_server_weibo.weibo import WeiboCrawler

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Weibo CLI - Interact with Weibo from the command line"""
    pass


@cli.command()
@click.argument('uid', type=int)
@click.option('--limit', '-n', default=15, help='Number of feeds to fetch')
@click.option('--include-pics/--no-include-pics', default=True, help='Include picture metadata in output')
@click.option('--include-profile/--no-include-profile', default=False, help='Include author profile in output')
def feeds(uid, limit, include_pics, include_profile):
    """Get user feeds by UID"""
    async def run():
        crawler = WeiboCrawler()
        results = await crawler.get_feeds(uid, limit)
        excluded_fields = set()
        if not include_pics:
            excluded_fields.add('pics')
        if not include_profile:
            excluded_fields.add('user')
        for item in results:
            print(json.dumps(item.model_dump(exclude=excluded_fields), ensure_ascii=False, indent=2))
    asyncio.run(run())

@cli.command()
@click.argument('keyword')
@click.option('--limit', '-n', default=15, help='Number of results to return')
@click.option('--page', '-p', default=1, help='Page number')
def search(keyword, limit, page):
    """Search Weibo content by keyword"""
    async def run():
        crawler = WeiboCrawler()
        results = await crawler.search_content(keyword, limit, page)
        for item in results:
            print(json.dumps(item.model_dump(), ensure_ascii=False, indent=2))
    asyncio.run(run())


@cli.command()
@click.argument('keyword')
@click.option('--limit', '-n', default=5, help='Number of results to return')
@click.option('--page', '-p', default=1, help='Page number')
def users(keyword, limit, page):
    """Search Weibo users by keyword"""
    async def run():
        crawler = WeiboCrawler()
        results = await crawler.search_users(keyword, limit, page)
        for item in results:
            print(json.dumps(item.model_dump(), ensure_ascii=False, indent=2))
    asyncio.run(run())


@cli.command()
@click.argument('keyword')
@click.option('--limit', '-n', default=15, help='Number of results to return')
@click.option('--page', '-p', default=1, help='Page number')
def topics(keyword, limit, page):
    """Search Weibo topics by keyword"""
    async def run():
        crawler = WeiboCrawler()
        results = await crawler.search_topics(keyword, limit, page)
        for item in results:
            print(json.dumps(item, ensure_ascii=False, indent=2))
    asyncio.run(run())


@cli.command()
@click.option('--limit', '-n', default=15, help='Number of trending items to return')
def trending(limit):
    """Get Weibo trending hot searches"""
    async def run():
        crawler = WeiboCrawler()
        results = await crawler.get_trendings(limit)
        for item in results:
            print(json.dumps(item.model_dump(), ensure_ascii=False, indent=2))
    asyncio.run(run())


@cli.command()
@click.argument('uid', type=int)
def profile(uid):
    """Get user profile by UID"""
    async def run():
        crawler = WeiboCrawler()
        result = await crawler.get_profile(uid)
        print(json.dumps(result.model_dump() if hasattr(result, 'model_dump') else result, ensure_ascii=False, indent=2))
    asyncio.run(run())


@cli.command()
@click.argument('feed_id', type=str)
@click.option('--page', '-p', default=1, help='Page number')
def comments(feed_id, page):
    """Get comments for a Weibo post"""
    async def run():
        crawler = WeiboCrawler()
        results = await crawler.get_comments(feed_id, page)
        for item in results:
            print(json.dumps(item.model_dump(), ensure_ascii=False, indent=2))
    asyncio.run(run())


@cli.command()
@click.argument('uid', type=int)
@click.option('--limit', '-n', default=15, help='Number of followers to return')
@click.option('--page', '-p', default=1, help='Page number')
def followers(uid, limit, page):
    """Get user's followers"""
    async def run():
        crawler = WeiboCrawler()
        results = await crawler.get_followers(uid, limit, page)
        for item in results:
            print(json.dumps(item.model_dump(), ensure_ascii=False, indent=2))
    asyncio.run(run())


@cli.command()
@click.argument('uid', type=int)
@click.option('--limit', '-n', default=15, help='Number of fans to return')
@click.option('--page', '-p', default=1, help='Page number')
def fans(uid, limit, page):
    """Get user's fans"""
    async def run():
        crawler = WeiboCrawler()
        results = await crawler.get_fans(uid, limit, page)
        for item in results:
            print(json.dumps(item.model_dump(), ensure_ascii=False, indent=2))
    asyncio.run(run())


if __name__ == '__main__':
    cli()
