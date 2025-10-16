import os
import aiohttp
import gspread
import logging
import ssl
from typing import Dict, Any, List
from src.config import settings

logger = logging.getLogger(__name__)

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

class GoogleSheetsService:
    def __init__(self):
        self.credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "google_credentials.json")
    
    async def read_spreadsheet(self, spreadsheet_id: str, range_name: str) -> Dict[str, Any]:
        try:
            gc = gspread.service_account(filename=self.credentials_path)
            
            spreadsheet = gc.open_by_key(spreadsheet_id)
            
            if '!' in range_name:
                sheet_name, cell_range = range_name.split('!')
                worksheet = spreadsheet.worksheet(sheet_name)
                data = worksheet.get(cell_range)
            else:
                worksheet = spreadsheet.sheet1
                data = worksheet.get(range_name)
            
            return {
                "status": "success",
                "data": data
            }
            
        except gspread.SpreadsheetNotFound:
            return {
                "status": "error",
                "message": f"Spreadsheet with ID {spreadsheet_id} not found"
            }
        except gspread.WorksheetNotFound:
            return {
                "status": "error", 
                "message": f"Worksheet in range '{range_name}' not found"
            }
        except gspread.APIError as e:
            return {
                "status": "error",
                "message": f"Google Sheets API error: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}"
            }
    
    async def update_spreadsheet(self, spreadsheet_id: str, range_name: str, values: List[List[str]]) -> Dict[str, Any]:
        try:
            gc = gspread.service_account(filename=self.credentials_path)
            spreadsheet = gc.open_by_key(spreadsheet_id)
            
            if '!' in range_name:
                sheet_name, cell_range = range_name.split('!')
                worksheet = spreadsheet.worksheet(sheet_name)
                worksheet.update(cell_range, values)
            else:
                worksheet = spreadsheet.sheet1
                worksheet.update(range_name, values)
            
            return {
                "status": "success",
                "data": "Updated successfully"
            }
            
        except Exception as e:
            return {
                "status": "error", 
                "message": str(e)
            }

class GitHubService:
    
    def __init__(self):
        self.token = settings.mcp.github_token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    async def get_user_profile(self, username: str) -> Dict[str, Any]:
        try:
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    f"{self.base_url}/users/{username}",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "success",
                            "data": {
                                "login": data.get("login"),
                                "name": data.get("name"),
                                "company": data.get("company"),
                                "blog": data.get("blog"),
                                "location": data.get("location"),
                                "email": data.get("email"),
                                "hireable": data.get("hireable"),
                                "bio": data.get("bio"),
                                "public_repos": data.get("public_repos"),
                                "followers": data.get("followers"),
                                "following": data.get("following"),
                                "created_at": data.get("created_at"),
                                "updated_at": data.get("updated_at")
                            }
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "status": "error",
                            "error": f"HTTP {response.status}: {error_text}"
                        }
        except Exception as e:
            logger.error(f"Error fetching GitHub user profile: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def search_repositories(self, query: str, language: str = None, sort: str = "stars") -> Dict[str, Any]:
        try:
            search_query = query
            if language:
                search_query += f" language:{language}"
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    f"{self.base_url}/search/repositories",
                    params={"q": search_query, "sort": sort, "per_page": 5},
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        repos = []
                        for item in data.get("items", []):
                            repos.append({
                                "name": item.get("name"),
                                "full_name": item.get("full_name"),
                                "html_url": item.get("html_url"),
                                "description": item.get("description"),
                                "language": item.get("language"),
                                "stargazers_count": item.get("stargazers_count"),
                                "forks_count": item.get("forks_count"),
                                "updated_at": item.get("updated_at")
                            })
                        return {
                            "status": "success",
                            "data": repos
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "status": "error",
                            "error": f"HTTP {response.status}: {error_text}"
                        }
        except Exception as e:
            logger.error(f"Error searching GitHub repositories: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def check_connection(self) -> bool:
        try:
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    f"{self.base_url}/user",
                    headers=self.headers
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"GitHub connection check failed: {e}")
            return False

class WebSearchService:
    """Сервис веб-поиска через DuckDuckGo"""
    
    def __init__(self):
        self.base_url = "https://api.duckduckgo.com"
        logger.info("WebSearchService initialized with DuckDuckGo")
    
    async def search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Поиск через DuckDuckGo API"""
        try:
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_results(data, query)
                    else:
                        return {
                            "status": "error",
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _format_results(self, data: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Форматирует результаты DuckDuckGo"""
        results = []
        
        if data.get("AbstractText"):
            results.append({
                "title": data.get("Heading", "Search Result"),
                "snippet": data.get("AbstractText"),
                "link": data.get("AbstractURL", "")
            })
        
        for topic in data.get("RelatedTopics", [])[:3]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "title": topic.get("Text", "").split("·")[0].strip(),
                    "snippet": topic.get("Text", ""),
                    "link": topic.get("FirstURL", "")
                })
        
        if not results:
            results.append({
                "title": f"Результаты для: {query}",
                "snippet": "Попробуйте уточнить запрос для получения более точных результатов.",
                "link": ""
            })
        
        return {
            "status": "success",
            "data": results[:5],
            "query_time": 1.0,
            "provider": "duckduckgo"
        }
    
    async def check_connection(self) -> bool:
        return True

async def check_mcp_services() -> Dict[str, bool]:
    """Проверяет доступность MCP серверов через HTTP запросы"""
    services_status = {}
    
    services_to_check = {
        "github": "http://mcp_github:8001/health",
        "web_search": "http://mcp_web_search:8002/health",
        "google_sheets": "http://mcp_sheets:8003/health"
    }
    
    for service_name, url in services_to_check.items():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    services_status[service_name] = response.status == 200
        except Exception as e:
            logger.warning(f"MCP service {service_name} check failed: {e}")
            services_status[service_name] = False
    
    return services_status
