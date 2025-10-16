import sys
import asyncio
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.types import NotificationOptions
from src.mcp.services import GitHubMCPServer, WebSearchMCPServer, GoogleSheetsMCPServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    if len(sys.argv) < 2:
        print("Usage: python src/mcp/main.py <server_type>")
        print("Available server types: github, web_search, sheets")
        sys.exit(1)
    
    server_type = sys.argv[1]
    
    if server_type == "github":
        from src.mcp.services import GitHubService
        service = GitHubService()
        if not service.token:
            print("GITHUB_TOKEN not set, GitHub server cannot start")
            return
        server_instance = GitHubMCPServer()
    elif server_type == "web_search":
        from src.mcp.services import WebSearchService
        service = WebSearchService()
        if not service.api_key:
            print("WEB_SEARCH_API_KEY not set, Web Search server cannot start")
            return
        server_instance = WebSearchMCPServer()
    elif server_type == "sheets":
        from src.mcp.services import GoogleSheetsService
        service = GoogleSheetsService()
        server_instance = GoogleSheetsMCPServer()
    else:
        print(f"Unknown server type: {server_type}")
        sys.exit(1)
    
    logger.info(f"Starting {server_type} MCP server")
    
    notification_options = NotificationOptions(tools_changed=False)
    
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=server_instance.name,
                server_version="0.1.0",
                capabilities=server_instance.server.get_capabilities(
                    notification_options=notification_options,
                    experimental_capabilities=None
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
