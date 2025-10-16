from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import logging
from src.mcp.services import GitHubService, WebSearchService, GoogleSheetsService

logger = logging.getLogger(__name__)

class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any]

class ToolCallResponse(BaseModel):
    status: str
    data: Any = None
    error: str = None

app_github = FastAPI(title="GitHub MCP Server")
github_service = GitHubService()

@app_github.get("/health")
async def health():
    return {"status": "healthy"}

@app_github.get("/tools")
async def list_tools():
    return [
        {
            "name": "get_user_profile",
            "description": "Get GitHub user profile information",
            "inputSchema": {
                "type": "object",
                "properties": {"username": {"type": "string"}},
                "required": ["username"]
            }
        },
        {
            "name": "search_repositories", 
            "description": "Search GitHub repositories",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "language": {"type": "string"},
                    "sort": {"type": "string", "enum": ["stars", "forks", "updated"]}
                },
                "required": ["query"]
            }
        }
    ]

@app_github.post("/tools/call")
async def call_tool(request: ToolCallRequest):
    try:
        if request.name == "get_user_profile":
            username = request.arguments.get("username")
            result = await github_service.get_user_profile(username)
            return ToolCallResponse(status="success", data=result)
        elif request.name == "search_repositories":
            query = request.arguments.get("query")
            language = request.arguments.get("language")
            sort = request.arguments.get("sort", "stars")
            result = await github_service.search_repositories(query, language, sort)
            return ToolCallResponse(status="success", data=result)
        else:
            return ToolCallResponse(status="error", error=f"Unknown tool: {request.name}")
    except Exception as e:
        logger.error(f"GitHub tool error: {e}")
        return ToolCallResponse(status="error", error=str(e))

app_web_search = FastAPI(title="Web Search MCP Server")
web_search_service = WebSearchService()

@app_web_search.get("/health")
async def health():
    return {"status": "healthy"}

@app_web_search.get("/tools")
async def list_tools():
    return [
        {
            "name": "search_web",
            "description": "Search the web",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "num_results": {"type": "integer", "minimum": 1, "maximum": 10}
                },
                "required": ["query"]
            }
        }
    ]

@app_web_search.post("/tools/call")
async def call_tool(request: ToolCallRequest):
    try:
        if request.name == "search_web":
            query = request.arguments.get("query")
            num_results = request.arguments.get("num_results", 3)
            result = await web_search_service.search(query, num_results)
            return ToolCallResponse(status="success", data=result)
        else:
            return ToolCallResponse(status="error", error=f"Unknown tool: {request.name}")
    except Exception as e:
        logger.error(f"Web search tool error: {e}")
        return ToolCallResponse(status="error", error=str(e))

app_sheets = FastAPI(title="Google Sheets MCP Server")
sheets_service = GoogleSheetsService()

@app_sheets.get("/health")
async def health():
    return {"status": "healthy"}

@app_sheets.get("/tools")
async def list_tools():
    return [
        {
            "name": "read_spreadsheet",
            "description": "Read data from Google Sheets",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string"},
                    "range_name": {"type": "string"}
                },
                "required": ["spreadsheet_id", "range_name"]
            }
        },
        {
            "name": "update_spreadsheet",
            "description": "Update data in Google Sheets", 
            "inputSchema": {
                "type": "object",
                "properties": {
                    "spreadsheet_id": {"type": "string"},
                    "range_name": {"type": "string"},
                    "values": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}}
                },
                "required": ["spreadsheet_id", "range_name", "values"]
            }
        }
    ]

@app_sheets.post("/tools/call")
async def call_tool(request: ToolCallRequest):
    try:
        if request.name == "read_spreadsheet":
            spreadsheet_id = request.arguments.get("spreadsheet_id")
            range_name = request.arguments.get("range_name")
            result = await sheets_service.read_spreadsheet(spreadsheet_id, range_name)
            return ToolCallResponse(status="success", data=result)
        elif request.name == "update_spreadsheet":
            spreadsheet_id = request.arguments.get("spreadsheet_id") 
            range_name = request.arguments.get("range_name") 
            values = request.arguments.get("values")
            result = await sheets_service.update_spreadsheet(spreadsheet_id, range_name, values)
            return ToolCallResponse(status="success", data=result)
        else:
            return ToolCallResponse(status="error", error=f"Unknown tool: {request.name}")
    except Exception as e:
        logger.error(f"Google Sheets tool error: {e}")
        return ToolCallResponse(status="error", error=str(e))
