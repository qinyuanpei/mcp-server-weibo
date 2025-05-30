from mcp.server.fastmcp import FastMCP, Context
from .weibo import WeiboCrawler

# Initialize FastMCP server with name "Weibo"
mcp = FastMCP("Weibo")

# Create an instance of WeiboCrawler for handling Weibo API operations
crawler = WeiboCrawler()

@mcp.tool()
async def search_users(keyword: str, ctx: Context, limit: int) -> list[dict]:
    """
    Search for Weibo users based on a keyword.
    
    Args:
        keyword (str): Search term to find users
        ctx (Context): MCP context object
        limit (int): Maximum number of users to return
        
    Returns:
        list[dict]: List of dictionaries containing user information
    """
    return await crawler.search_weibo_users(keyword, limit)

@mcp.tool()
async def get_profile(uid: int, ctx: Context) -> dict:
    """
    Get a Weibo user's profile information.
    
    Args:
        uid (): The unique identifier of the Weibo user
        ctx (Context): MCP context object
        
    Returns:
        dict: Dictionary containing user profile information
    """
    return await crawler.extract_weibo_profile(uid)

@mcp.tool()
async def get_feeds(uid: int, ctx: Context, limit: int) -> list[dict]:
    """
    Get a Weibo user's feeds (posts).
    
    Args:
        uid (int): The unique identifier of the Weibo user
        ctx (Context): MCP context object
        limit (int): Maximum number of feeds to return, None for no limit
        
    Returns:
        list[dict]: List of dictionaries containing feed information
    """
    return await crawler.extract_weibo_feeds(str(uid), limit)

if __name__ == "__main__":
    # Run the MCP server using standard input/output for communication
    mcp.run(transport='stdio')
    