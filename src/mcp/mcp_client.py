import asyncio
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Dict, Any, List, Optional
import logging
from src.config import settings

logger = logging.getLogger(__name__)

class MCPClient:
    
    def __init__(self):
        self.github = GitHubClient(settings.mcp.github_url)
        self.web_search = WebSearchClient(settings.mcp.web_search_url)
        self.sheets = GoogleSheetsClient(settings.mcp.sheets_url)
        
        logger.info(f"MCP Client initialized with URLs: "
                   f"GitHub: {settings.mcp.github_url}, "
                   f"WebSearch: {settings.mcp.web_search_url}, "
                   f"Sheets: {settings.mcp.sheets_url}")

class BaseMCPClient:
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _ensure_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        await self._ensure_session()
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with asyncio.timeout(10):
                async with self.session.post(
                    url,
                    json=data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"MCP request failed: {response.status} - {error_text}")
                        return {
                            "status": "error",
                            "error": f"HTTP {response.status}: {error_text}"
                        }
                        
        except asyncio.TimeoutError:
            logger.error(f"MCP service timeout: {self.base_url}")
            return {
                "status": "error", 
                "error": "Service timeout"
            }
        except aiohttp.ClientConnectorError as e:
            logger.error(f"MCP connection error to {url}: {e}")
            return {
                "status": "error", 
                "error": f"Connection failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected MCP error to {url}: {e}")
            return {
                "status": "error",
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        return await self._make_request("tools/call", {
            "name": name,
            "arguments": arguments
        })
    
    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

class GitHubClient(BaseMCPClient):
    
    async def get_user_profile(self, username: str) -> str:
        result = await self.call_tool("get_user_profile", {"username": username})
        
        if result.get("status") == "success" and "data" in result:
            data = result["data"]
            if data.get("status") == "success":
                profile_data = data["data"]
                return f"""
👤 GitHub Profile: {profile_data.get('login', 'N/A')}
📛 Name: {profile_data.get('name', 'N/A')}
🏢 Company: {profile_data.get('company', 'N/A')}
📍 Location: {profile_data.get('location', 'N/A')}
📊 Public Repos: {profile_data.get('public_repos', 0)}
👥 Followers: {profile_data.get('followers', 0)}
                """.strip()
        return f"❌ GitHub Error: {result.get('error', 'Unknown error')}"
    
    async def search_repositories(self, query: str) -> str:
        result = await self.call_tool("search_repositories", {"query": query})
        
        if result.get("status") == "success" and "data" in result:
            data = result["data"]
            if data.get("status") == "success":
                repos = data["data"]
                if not repos:
                    return "🔍 No repositories found"
                
                formatted = f"🔍 Found {len(repos)} repositories:\n\n"
                for i, repo in enumerate(repos[:3], 1):
                    formatted += f"{i}. **{repo.get('full_name', 'N/A')}**\n"
                    formatted += f"   📝 {repo.get('description', 'No description')}\n"
                    formatted += f"   ⭐ Stars: {repo.get('stargazers_count', 0)}\n\n"
                return formatted.strip()
        return f"❌ GitHub Search Error: {result.get('error', 'Unknown error')}"

class WebSearchClient(BaseMCPClient):
    
    async def search_web(self, query: str, num_results: int = 3) -> str:
        result = await self.call_tool("search_web", {
            "query": query,
            "num_results": num_results
        })
        
        if result.get("status") == "success" and "data" in result:
            data = result["data"]
            if data.get("status") == "success":
                search_data = data["data"]
                if not search_data:
                    return "🔍 No results found"
                
                formatted = f"🔍 Search results for '{query}':\n\n"
                for i, item in enumerate(search_data, 1):
                    title = item.get('title', 'No title')
                    snippet = item.get('snippet', 'No description')
                    if len(snippet) > 150:
                        snippet = snippet[:150] + "..."
                    
                    formatted += f"{i}. **{title}**\n"
                    formatted += f"   {snippet}\n\n"
                return formatted.strip()
        return f"❌ Search Error: {result.get('error', 'Unknown error')}"

class GoogleSheetsClient(BaseMCPClient):
    
    async def read_spreadsheet(self, spreadsheet_id: str, range_name: str) -> str:
        result = await self.call_tool("read_spreadsheet", {
            "spreadsheet_id": spreadsheet_id,
            "range_name": range_name
        })
        
        if result.get("status") == "success" and "data" in result:
            data = result["data"]
            if data.get("status") == "success":
                sheet_data = data["data"]
                if not sheet_data:
                    return "📊 Spreadsheet is empty"
                
                formatted = "📊 Spreadsheet Data:\n\n"
                for i, row in enumerate(sheet_data[:5]):
                    formatted += f"Row {i+1}: {', '.join(str(cell) for cell in row)}\n"
                return formatted.strip()
        return f"❌ Sheets Error: {result.get('error', 'Unknown error')}"

mcp_client = MCPClient()

async def close_mcp_clients():
    await mcp_client.github.close()
    await mcp_client.web_search.close() 
    await mcp_client.sheets.close()
