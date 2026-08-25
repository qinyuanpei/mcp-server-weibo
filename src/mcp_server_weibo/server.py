from fastmcp import FastMCP, Context
from .weibo import WeiboCrawler
from typing import Annotated
from pydantic import Field
import argparse
import os

# Initialize FastMCP server with name "Weibo"
mcp = FastMCP("Weibo")

# Global crawler instance (initialized in main to handle cookie config first)
_crawler = None

def get_crawler():
    """Get or create the WeiboCrawler instance."""
    global _crawler
    if _crawler is None:
        _crawler = WeiboCrawler()
    return _crawler

@mcp.tool()
async def search_users(
    ctx: Context, 
    keyword: Annotated[str, Field(description="Search term to find users")], 
    limit: Annotated[int, Field(description="Maximum number of users to return, defaults to 5", default=5)] = 5,
    page: Annotated[int, Field(description="Page number for pagination, defaults to 1", default=1)] = 1
    ) -> list[dict]:
    """
    Search for Weibo users based on a keyword.
        
    Returns:
        list[dict]: List of dictionaries containing user information
    """
    return await get_crawler().search_users(keyword, limit, page)

@mcp.tool()
async def get_profile(
    uid: Annotated[int, Field(description="The unique identifier of the Weibo user")],
    ctx: Context
    ) -> dict:
    """
    Get a Weibo user's profile information.

    Returns:
        dict: Dictionary containing user profile information
    """
    return await get_crawler().get_profile(uid)

@mcp.tool()
async def get_feeds(
    ctx: Context, 
    uid: Annotated[int, Field(description="The unique identifier of the Weibo user")], 
    limit: Annotated[int, Field(description="Maximum number of feeds to return, defaults to 15", default=15)] = 15,
    ) -> list[dict]:
    """
    Get a Weibo user's feeds
        
    Returns:
        list[dict]: List of dictionaries containing feeds
    """
    return await get_crawler().get_feeds(str(uid), limit)

@mcp.tool()
async def get_hot_feeds(
    ctx: Context, 
    uid: Annotated[int, Field(description="The unique identifier of the Weibo user")], 
    limit: Annotated[int, Field(description="Maximum number of feeds to return, defaults to 15", default=15)] = 15,
    ) -> list[dict]:
    """
    Get a Weibo user's hot feeds
        
    Returns:
        list[dict]: List of dictionaries containing hot feeds
    """
    return await get_crawler().get_hot_feeds(uid, limit)

@mcp.tool()
async def get_trendings(
    ctx: Context, 
    limit: Annotated[int, Field(description="Maximum number of hot search items to return, defaults to 15", default=15)] = 15
    ) -> list[dict]:
    """
    Get the current hot search topics on Weibo.
        
    Returns:
        list[dict]: List of dictionaries containing hot search items
    """
    return await get_crawler().get_trendings(limit)

@mcp.tool()
async def search_content(
    ctx: Context, 
    keyword: Annotated[str, Field(description="Search term to find content")], 
    limit: Annotated[int, Field(description="Maximum number of results to return, defaults to 15", default=15)] = 15, 
    page: Annotated[int, Field(description="Page number for pagination, defaults to 1", default=1)] = 1
    ) -> list[dict]:
    """
    Search for content on Weibo based on a keyword.
        
    Returns:
        list[dict]: List of dictionaries containing search results
    """
    return await get_crawler().search_content(keyword, limit, page)

@mcp.tool
async def search_topics(
    ctx: Context, 
    keyword: Annotated[str, Field(description="Search term to find content")], 
    limit: Annotated[int, Field(description="Maximum number of results to return, defaults to 15", default=15)] = 15, 
    page: Annotated[int, Field(description="Page number for pagination, defaults to 1", default=1)] = 1
) -> list[dict]:
    """
    Search for topics on Weibo based on a keyword.
        
    Returns:
        list[dict]: List of dictionaries containing search results
    """
    return await get_crawler().search_topics(keyword, limit, page)

@mcp.tool()
async def get_followers(
    ctx: Context, 
    uid: Annotated[int, Field(description="The unique identifier of the Weibo user")], 
    limit: Annotated[int, Field(description="Maximum number of followers to return, defaults to 15", default=15)] = 15,
    page: Annotated[int, Field(description="Page number for pagination, defaults to 1", default=1)] = 1
    ) -> list[dict]:
    """
    Get a Weibo user's followers.
        
    Returns:
        list[dict]: List of dictionaries containing follower information
    """
    return await get_crawler().get_followers(uid, limit, page)

@mcp.tool()
async def get_fans(
    ctx: Context, 
    uid: Annotated[int, Field(description="The unique identifier of the Weibo user")], 
    limit: Annotated[int, Field(description="Maximum number of fans to return, defaults to 15", default=15)] = 15,
    page: Annotated[int, Field(description="Page number for pagination, defaults to 1", default=1)] = 1
    ) -> list[dict]:
    """
    Get a Weibo user's fans.
        
    Returns:
        list[dict]: List of dictionaries containing fan information
    """
    return await get_crawler().get_fans(uid, limit, page)

@mcp.tool()
async def get_comments(
    ctx: Context, 
    feed_id: Annotated[int, Field(description="The unique identifier of the Weibo post")], 
    page: Annotated[int, Field(description="Page number for pagination, defaults to 1", default=1)] = 1
    ) -> list[dict]:
    """
    Get comments for a specific Weibo post.
        
    Returns:
        list[dict]: List of dictionaries containing comments
    """
    return await get_crawler().get_comments(feed_id, page)

def run_as_streamable_http():
    """
    Run the MCP server using streamable-http transport, allowing custom port configuration via the PORT environment variable.
    """
    port = int(os.environ.get("PORT", 4200))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)

def run_as_stdio():
    mcp.run(transport="stdio")

def main():
    """
    Entry point for CLI.
    """
    parser = argparse.ArgumentParser(description="Weibo MCP Server")
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["stdio", "http"],
        default="stdio",
        help="Server mode: 'stdio' or 'http' (default: stdio)"
    )
    args = parser.parse_args()

    if args.mode == "http":
        run_as_streamable_http()
    else:
        run_as_stdio()


if __name__ == "__main__":
    main()
