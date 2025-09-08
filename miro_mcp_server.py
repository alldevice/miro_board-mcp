#!/usr/bin/env python3
"""
Universal Miro Server for Claude.ai (MCP) and OpenWebUI (Filters)
"""

import os
import json
import asyncio
from typing import Optional, Dict, List, Any
from datetime import datetime
import httpx
from dotenv import load_dotenv
import logging
import uuid

load_dotenv()

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Universal Miro Server", version="2.0.0")

# CORS for all clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# CORE MIRO LOGIC (Single source of truth - modify Miro functionality here)
# =============================================================================

class MiroCore:
    """Core Miro functionality - all Miro API logic in one place"""
    
    def __init__(self):
        self.access_token = os.environ.get("MIRO_ACCESS_TOKEN")
        self.base_url = "https://api.miro.com/v2"
        
        if not self.access_token:
            logger.warning("MIRO_ACCESS_TOKEN not set - Miro functionality will be limited")
    
    async def fetch_all_items(self, board_id: str) -> List[Dict]:
        """Fetch all items from a MIRO board"""
        if not self.access_token:
            raise ValueError("MIRO_ACCESS_TOKEN environment variable is required")
            
        items = []
        cursor = None
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                params = {"limit": 50}
                if cursor:
                    params["cursor"] = cursor
                
                response = await client.get(
                    f"{self.base_url}/boards/{board_id}/items",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Accept": "application/json"
                    },
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                items.extend(data.get("data", []))
                cursor = data.get("cursor")
                
                if not cursor:
                    break
        
        return items
    
    async def fetch_all_connectors(self, board_id: str) -> List[Dict]:
        """Fetch all connectors from a MIRO board"""
        if not self.access_token:
            raise ValueError("MIRO_ACCESS_TOKEN environment variable is required")
            
        connectors = []
        cursor = None
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                params = {"limit": 50}
                if cursor:
                    params["cursor"] = cursor
                
                response = await client.get(
                    f"{self.base_url}/boards/{board_id}/connectors",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Accept": "application/json"
                    },
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                connectors.extend(data.get("data", []))
                cursor = data.get("cursor")
                
                if not cursor:
                    break
        
        return connectors
    
    def simplify_item(self, item: Dict) -> Dict:
        """Simplify item structure for easier processing"""
        data = item.get("data", {})
        style = item.get("style", {})
        
        text = (data.get("content") or 
                data.get("title") or 
                data.get("text") or 
                "")
        
        return {
            "id": item.get("id"),
            "type": item.get("type"),
            "text": text,
            "position": item.get("position"),
            "style": {
                "color": style.get("fillColor") or style.get("color"),
                "shape": data.get("shape")
            },
            "tags": item.get("tags", []),
            "createdBy": item.get("createdBy", {}).get("id") if item.get("createdBy") else None,
            "modifiedAt": item.get("modifiedAt")
        }
    
    def simplify_connector(self, connector: Dict) -> Dict:
        """Simplify connector structure"""
        captions = connector.get("captions", [])
        caption_text = captions[0].get("content", "") if captions else ""
        
        return {
            "id": connector.get("id"),
            "from": connector.get("startItem", {}).get("id") if connector.get("startItem") else None,
            "to": connector.get("endItem", {}).get("id") if connector.get("endItem") else None,
            "label": caption_text,
            "style": connector.get("style", {}).get("lineType", "default")
        }
    
    def build_simple_graph(self, items: List[Dict], connectors: List[Dict]) -> Dict:
        """Build adjacency list representation"""
        graph = {}
        
        for item in items:
            data = item.get("data", {})
            text = (data.get("content") or 
                   data.get("title") or 
                   data.get("text") or 
                   "")
            
            graph[item.get("id")] = {
                "text": text,
                "type": item.get("type"),
                "connections": {
                    "outgoing": [],
                    "incoming": []
                }
            }
        
        for conn in connectors:
            start_id = conn.get("startItem", {}).get("id") if conn.get("startItem") else None
            end_id = conn.get("endItem", {}).get("id") if conn.get("endItem") else None
            captions = conn.get("captions", [])
            label = captions[0].get("content", "") if captions else ""
            
            if start_id and end_id:
                if start_id in graph:
                    graph[start_id]["connections"]["outgoing"].append({
                        "to": end_id,
                        "label": label
                    })
                if end_id in graph:
                    graph[end_id]["connections"]["incoming"].append({
                        "from": start_id,
                        "label": label
                    })
        
        return graph
    
    async def get_board_content(
        self, 
        board_id: str, 
        bounds: Optional[Dict] = None, 
        include_types: Optional[List[str]] = None
    ) -> Dict:
        """Get all items and connections from a MIRO board region"""
        
        items, connectors = await asyncio.gather(
            self.fetch_all_items(board_id),
            self.fetch_all_connectors(board_id)
        )
        
        filtered_items = items
        
        if bounds:
            filtered_items = [
                item for item in items
                if item.get("position") and
                   bounds["left"] <= item["position"].get("x", 0) <= bounds["right"] and
                   bounds["top"] <= item["position"].get("y", 0) <= bounds["bottom"]
            ]
        
        if include_types:
            filtered_items = [
                item for item in filtered_items
                if item.get("type") in include_types
            ]
        
        item_ids = {item.get("id") for item in filtered_items}
        relevant_connectors = [
            conn for conn in connectors
            if (conn.get("startItem", {}).get("id") in item_ids or
                conn.get("endItem", {}).get("id") in item_ids)
        ]
        
        return {
            "metadata": {
                "boardId": board_id,
                "itemCount": len(filtered_items),
                "connectorCount": len(relevant_connectors),
                "bounds": bounds or "full board",
                "timestamp": datetime.now().isoformat()
            },
            "items": [self.simplify_item(item) for item in filtered_items],
            "connections": [self.simplify_connector(conn) for conn in relevant_connectors],
            "graph": self.build_simple_graph(filtered_items, relevant_connectors)
        }
    
    async def get_connected_path(
        self, 
        board_id: str, 
        start_item_id: str, 
        max_depth: int = 5
    ) -> Dict:
        """Get items connected to a starting item"""
        
        connectors = await self.fetch_all_connectors(board_id)
        
        visited = {start_item_id}
        queue = [{"id": start_item_id, "depth": 0}]
        paths = []
        
        while queue and queue[0]["depth"] < max_depth:
            current = queue.pop(0)
            
            connections = [
                conn for conn in connectors
                if (conn.get("startItem", {}).get("id") == current["id"] or
                    conn.get("endItem", {}).get("id") == current["id"])
            ]
            
            for conn in connections:
                start_id = conn.get("startItem", {}).get("id") if conn.get("startItem") else None
                end_id = conn.get("endItem", {}).get("id") if conn.get("endItem") else None
                
                next_id = end_id if start_id == current["id"] else start_id
                
                if next_id and next_id not in visited:
                    visited.add(next_id)
                    queue.append({"id": next_id, "depth": current["depth"] + 1})
                    
                    captions = conn.get("captions", [])
                    label = captions[0].get("content", "") if captions else ""
                    
                    paths.append({
                        "from": current["id"],
                        "to": next_id,
                        "label": label,
                        "depth": current["depth"] + 1
                    })
        
        all_items = await self.fetch_all_items(board_id)
        visited_items = [item for item in all_items if item.get("id") in visited]
        
        return {
            "startItem": start_item_id,
            "traversalDepth": max_depth,
            "items": [self.simplify_item(item) for item in visited_items],
            "paths": paths,
            "summary": {
                "totalItems": len(visited_items),
                "totalConnections": len(paths),
                "maxDepthReached": max([p["depth"] for p in paths], default=0)
            }
        }
    
    async def search_items(
        self, 
        board_id: str, 
        search_text: str, 
        case_sensitive: bool = False
    ) -> Dict:
        """Search for items containing specific text"""
        
        items = await self.fetch_all_items(board_id)
        
        search = search_text if case_sensitive else search_text.lower()
        
        matching_items = []
        for item in items:
            data = item.get("data", {})
            text = (data.get("content") or 
                   data.get("title") or 
                   data.get("text") or 
                   "")
            
            compare_text = text if case_sensitive else text.lower()
            
            if search in compare_text:
                matching_items.append(item)
        
        return {
            "query": search_text,
            "caseSensitive": case_sensitive,
            "resultCount": len(matching_items),
            "items": [self.simplify_item(item) for item in matching_items]
        }

# Create single instance
miro_core = MiroCore()

# =============================================================================
# MCP ADAPTER FOR CLAUDE.AI
# =============================================================================

# Store SSE connections
connections: Dict[str, asyncio.Queue] = {}

async def handle_mcp_message(message: dict) -> Optional[dict]:
    """Process MCP protocol messages for Claude.ai"""
    method = message.get("method")
    msg_id = message.get("id")
    params = message.get("params", {})
    
    logger.info(f"MCP Processing: {method} (id: {msg_id})")
    
    if msg_id is None:
        logger.info(f"MCP Notification: {method}")
        return None
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "miro-board-reader",
                    "version": "2.0.0"
                }
            }
        }
    
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": [
                    {
                        "name": "get_miro_region",
                        "description": "Get all items and connections from a MIRO board region",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "boardId": {"type": "string", "description": "MIRO board ID from URL"},
                                "bounds": {
                                    "type": "object",
                                    "properties": {
                                        "left": {"type": "number"},
                                        "right": {"type": "number"},
                                        "top": {"type": "number"},
                                        "bottom": {"type": "number"}
                                    }
                                },
                                "includeTypes": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "required": ["boardId"]
                        }
                    },
                    {
                        "name": "get_miro_connected_path",
                        "description": "Get items connected to a starting item",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "boardId": {"type": "string"},
                                "startItemId": {"type": "string"},
                                "maxDepth": {"type": "integer", "default": 5}
                            },
                            "required": ["boardId", "startItemId"]
                        }
                    },
                    {
                        "name": "search_miro_items",
                        "description": "Search for items by text content",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "boardId": {"type": "string"},
                                "searchText": {"type": "string"},
                                "caseSensitive": {"type": "boolean", "default": False}
                            },
                            "required": ["boardId", "searchText"]
                        }
                    }
                ]
            }
        }
    
    elif method == "tools/call":
        try:
            name = params.get("name")
            arguments = params.get("arguments", {})
            
            logger.info(f"MCP Tool call: {name}")
            
            # Route to core Miro logic
            if name == "get_miro_region":
                result = await miro_core.get_board_content(
                    arguments["boardId"],
                    arguments.get("bounds"),
                    arguments.get("includeTypes")
                )
            elif name == "get_miro_connected_path":
                result = await miro_core.get_connected_path(
                    arguments["boardId"],
                    arguments["startItemId"],
                    arguments.get("maxDepth", 5)
                )
            elif name == "search_miro_items":
                result = await miro_core.search_items(
                    arguments["boardId"],
                    arguments["searchText"],
                    arguments.get("caseSensitive", False)
                )
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32602, "message": f"Unknown tool: {name}"}
                }
            
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }]
                }
            }
        except Exception as e:
            logger.error(f"MCP Tool error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32603, "message": str(e)}
            }
    
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"}
    }

# =============================================================================
# CLAUDE.AI ENDPOINTS (MCP/SSE)
# =============================================================================

@app.get("/sse")
@app.get("/claude/sse")  # Alternative clear endpoint
async def sse_get():
    """SSE endpoint for Claude.ai persistent connection"""
    connection_id = str(uuid.uuid4())
    queue = asyncio.Queue()
    connections[connection_id] = queue
    
    async def event_generator():
        try:
            logger.info(f"Claude SSE connection: {connection_id}")
            yield f"data: {json.dumps({'type': 'connection', 'id': connection_id})}\n\n"
            
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    
        except asyncio.CancelledError:
            logger.info(f"Claude SSE cancelled: {connection_id}")
        finally:
            connections.pop(connection_id, None)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/sse")
@app.post("/claude/sse")  # Alternative clear endpoint
async def sse_post(request: Request):
    """SSE endpoint for Claude.ai messages"""
    try:
        body = await request.body()
        message = json.loads(body) if body else {}
        
        response = await handle_mcp_message(message)
        
        async def event_generator():
            if response:
                yield f"data: {json.dumps(response)}\n\n"
            await asyncio.sleep(0.1)
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"Claude SSE error: {e}")
        return Response(status_code=500)

# =============================================================================
# OPENWEBUI FILTER ENDPOINTS
# =============================================================================

@app.post("/filter/miro/analyze")
@app.post("/openwebui/filter/analyze")  # Alternative clear endpoint
async def filter_analyze_board(request: Request):
    """
    OpenWebUI Filter: Analyze MIRO board
    Expected format: {"board_id": "...", "command": "...", "params": {...}}
    """
    try:
        data = await request.json()
        board_id = data.get("board_id")
        command = data.get("command", "full_board")
        params = data.get("params", {})
        
        if not board_id:
            raise HTTPException(status_code=400, detail="board_id is required")
        
        # Execute based on command
        if command == "full_board":
            result = await miro_core.get_board_content(
                board_id,
                params.get("bounds"),
                params.get("include_types")
            )
        elif command == "connected_path":
            if not params.get("start_item_id"):
                raise HTTPException(status_code=400, detail="start_item_id required for connected_path")
            result = await miro_core.get_connected_path(
                board_id,
                params["start_item_id"],
                params.get("max_depth", 5)
            )
        elif command == "search":
            if not params.get("search_text"):
                raise HTTPException(status_code=400, detail="search_text required for search")
            result = await miro_core.search_items(
                board_id,
                params["search_text"],
                params.get("case_sensitive", False)
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown command: {command}")
        
        return JSONResponse(content={
            "success": True,
            "data": result,
            "command": command
        })
        
    except Exception as e:
        logger.error(f"Filter error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/filter/miro/tools")
@app.get("/openwebui/filter/tools")  # Alternative clear endpoint
async def filter_list_tools():
    """List available MIRO tools for OpenWebUI"""
    return {
        "tools": [
            {
                "name": "analyze_board",
                "endpoint": "/filter/miro/analyze",
                "commands": [
                    {
                        "command": "full_board",
                        "description": "Get entire board content",
                        "params": {
                            "bounds": "optional: {left, right, top, bottom}",
                            "include_types": "optional: array of item types"
                        }
                    },
                    {
                        "command": "connected_path",
                        "description": "Trace connections from an item",
                        "params": {
                            "start_item_id": "required: starting item ID",
                            "max_depth": "optional: traversal depth (default 5)"
                        }
                    },
                    {
                        "command": "search",
                        "description": "Search items by text",
                        "params": {
                            "search_text": "required: text to search",
                            "case_sensitive": "optional: boolean (default false)"
                        }
                    }
                ]
            }
        ]
    }

# =============================================================================
# DIRECT API ENDPOINTS (Human-friendly)
# =============================================================================

@app.get("/api/miro/board/{board_id}")
async def api_get_board(
    board_id: str,
    left: Optional[float] = None,
    right: Optional[float] = None,
    top: Optional[float] = None,
    bottom: Optional[float] = None,
    types: Optional[str] = None
):
    """Direct API: Get MIRO board content"""
    try:
        bounds = None
        if all(x is not None for x in [left, right, top, bottom]):
            bounds = {"left": left, "right": right, "top": top, "bottom": bottom}
        
        include_types = types.split(",") if types else None
        
        result = await miro_core.get_board_content(board_id, bounds, include_types)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/miro/board/{board_id}/search")
async def api_search_board(
    board_id: str,
    q: str,
    case_sensitive: bool = False
):
    """Direct API: Search MIRO board"""
    try:
        result = await miro_core.search_items(board_id, q, case_sensitive)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/miro/board/{board_id}/connections/{item_id}")
async def api_get_connections(
    board_id: str,
    item_id: str,
    depth: int = 5
):
    """Direct API: Get connected items"""
    try:
        result = await miro_core.get_connected_path(board_id, item_id, depth)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Universal Miro Server",
        "version": "2.0.0",
        "endpoints": {
            "claude_ai": {
                "sse": "/sse or /claude/sse",
                "description": "MCP protocol for Claude.ai"
            },
            "openwebui": {
                "filter": "/filter/miro/analyze or /openwebui/filter/analyze",
                "tools": "/filter/miro/tools or /openwebui/filter/tools",
                "description": "Filter endpoints for OpenWebUI"
            },
            "direct_api": {
                "board": "/api/miro/board/{board_id}",
                "search": "/api/miro/board/{board_id}/search",
                "connections": "/api/miro/board/{board_id}/connections/{item_id}",
                "description": "RESTful API for direct access"
            },
            "health": "/health",
            "test": "/test"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    has_token = bool(os.environ.get("MIRO_ACCESS_TOKEN"))
    return {
        "status": "healthy",
        "miro_configured": has_token,
        "active_connections": len(connections),
        "interfaces": {
            "mcp": "active",
            "filter": "active",
            "api": "active"
        }
    }

@app.get("/test")
async def test():
    """Test endpoint with usage examples"""
    return {
        "claude_ai_example": {
            "connection": "Add https://your-server/sse as custom connector in Claude.ai",
            "usage": "Ask Claude to analyze MIRO board [board_id]"
        },
        "openwebui_filter_example": {
            "setup": "Add server URL to OpenWebUI filters",
            "request": {
                "board_id": "your_board_id",
                "command": "full_board",
                "params": {}
            }
        },
        "direct_api_example": {
            "get_board": "GET /api/miro/board/YOUR_BOARD_ID",
            "search": "GET /api/miro/board/YOUR_BOARD_ID/search?q=customer",
            "connections": "GET /api/miro/board/YOUR_BOARD_ID/connections/ITEM_ID?depth=3"
        }
    }

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    
    print("=" * 60)
    print("Universal Miro Server")
    print("=" * 60)
    print(f"Port: {port}")
    print(f"MIRO_ACCESS_TOKEN: {'Set' if os.environ.get('MIRO_ACCESS_TOKEN') else 'Not set'}")
    print("")
    print("Interfaces:")
    print(f"  Claude.ai (MCP): http://0.0.0.0:{port}/sse")
    print(f"  OpenWebUI (Filter): http://0.0.0.0:{port}/filter/miro/analyze")
    print(f"  Direct API: http://0.0.0.0:{port}/api/miro/board/{{board_id}}")
    print(f"  Health: http://0.0.0.0:{port}/health")
    print(f"  Documentation: http://0.0.0.0:{port}/")
    print("")
    print("Setup Instructions:")
    print("  1. Set MIRO_ACCESS_TOKEN in .env file")
    print("  2. For Claude.ai: Add /sse endpoint as custom connector")
    print("  3. For OpenWebUI: Configure filter with /filter/miro/analyze")
    print("  4. For direct use: Access /api/miro/board/{board_id}")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")