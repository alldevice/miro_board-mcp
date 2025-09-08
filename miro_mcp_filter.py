"""
Miro Filter for OpenWebUI - Full Version with Shape Display
Updated to remove text truncation for full content display
"""

import re
import json
import aiohttp
import asyncio
from typing import Optional, Dict, List
from pydantic import BaseModel, Field


class Filter:
    class Valves(BaseModel):
        priority: int = Field(default=0)
        miro_server_url: str = Field(
            default="https://",
            description="Your Miro Server URL"
        )
        enabled: bool = Field(default=True)
        max_items: int = Field(default=100, description="Max items to display")
        max_connections: int = Field(default=50, description="Max connections to display")
    
    def __init__(self):
        self.valves = self.Valves()
        self.item_cache = {}
    
    async def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """Process incoming messages"""
        if not self.valves.enabled:
            return body
        
        try:
            messages = body.get("messages", [])
            if not messages:
                return body
            
            last_message = messages[-1]
            content = last_message.get("content", "")
            
            # Parse request
            request = self._parse_request(content)
            if not request:
                return body
            
            # Execute request
            result = await self._execute_request(request)
            if not result:
                return body
            
            # Inject as system message
            system_msg = {
                "role": "system", 
                "content": f"[Miro Board Data]\n{result}"
            }
            messages.insert(-1, system_msg)
            
            # Mark as processed
            messages[-1]["content"] = f"{content}\n\n✓ Miro data loaded"
            
        except Exception as e:
            print(f"[Miro Filter] Error: {e}")
        
        return body
    
    def _parse_request(self, content: str) -> Optional[Dict]:
        """Parse Miro request from message"""
        content_lower = content.lower()
        
        # Extract board ID
        board_match = re.search(
            r'\[([a-zA-Z0-9_\-=]+)\]|board[:\s]+([a-zA-Z0-9_\-=]+)|miro\.com/app/board/([a-zA-Z0-9_\-=]+)',
            content, re.IGNORECASE
        )
        
        if not board_match:
            return None
        
        board_id = board_match.group(1) or board_match.group(2) or board_match.group(3)
        
        # Detect command type
        
        # Search command
        if any(word in content_lower for word in ['search', 'find', 'look for']):
            search_match = re.search(
                r'(?:search|find|look\s+for)\s+(?:for\s+)?["\']([^"\']+)["\']|(?:search|find)\s+(?:for\s+)?(\w+)',
                content, re.IGNORECASE
            )
            if search_match:
                search_text = search_match.group(1) or search_match.group(2)
                return {
                    "board_id": board_id,
                    "command": "search",
                    "params": {"search_text": search_text}
                }
        
        # Connected path command
        if any(word in content_lower for word in ['connection', 'connected', 'path', 'trace']):
            item_match = re.search(
                r'(?:item|from|starting)[:\s]+([a-zA-Z0-9_\-]+)',
                content, re.IGNORECASE
            )
            if item_match:
                item_id = item_match.group(1)
                depth = 5
                depth_match = re.search(r'depth[:\s]+(\d+)', content, re.IGNORECASE)
                if depth_match:
                    depth = int(depth_match.group(1))
                return {
                    "board_id": board_id,
                    "command": "connected_path",
                    "params": {"start_item_id": item_id, "max_depth": depth}
                }
        
        # Region command
        if 'region' in content_lower or 'bounds' in content_lower:
            bounds_match = re.search(
                r'left[:\s]+([\d.-]+)[,\s]+right[:\s]+([\d.-]+)[,\s]+top[:\s]+([\d.-]+)[,\s]+bottom[:\s]+([\d.-]+)',
                content, re.IGNORECASE
            )
            if bounds_match:
                return {
                    "board_id": board_id,
                    "command": "full_board",
                    "params": {
                        "bounds": {
                            "left": float(bounds_match.group(1)),
                            "right": float(bounds_match.group(2)),
                            "top": float(bounds_match.group(3)),
                            "bottom": float(bounds_match.group(4))
                        }
                    }
                }
        
        # Type filter - check for "shapes" request
        if any(word in content_lower for word in ['shape', 'shapes']):
            return {
                "board_id": board_id,
                "command": "full_board",
                "params": {"include_types": ["shape"]}
            }
        
        # Type filter
        if 'only' in content_lower or 'filter' in content_lower:
            type_match = re.search(
                r'(?:only|filter)[:\s]+([a-zA-Z_,\s]+)(?:\s+items)?',
                content, re.IGNORECASE
            )
            if type_match:
                types = [t.strip() for t in type_match.group(1).split(',')]
                return {
                    "board_id": board_id,
                    "command": "full_board",
                    "params": {"include_types": types}
                }
        
        # Default: full board
        return {
            "board_id": board_id,
            "command": "full_board",
            "params": {}
        }
    
    async def _execute_request(self, request: Dict) -> Optional[str]:
        """Execute Miro server request"""
        try:
            url = f"{self.valves.miro_server_url}/filter/miro/analyze"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=request, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success") and data.get("data"):
                            return self._format_data(data["data"], request["command"])
                        else:
                            return f"Error: {data.get('error', 'Unknown error')}"
                    else:
                        return f"Server error: {response.status}"
        
        except asyncio.TimeoutError:
            return "Request timeout"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _format_data(self, data: Dict, command: str) -> str:
        """Format Miro data based on command"""
        if command == "search":
            return self._format_search(data)
        elif command == "connected_path":
            return self._format_connections(data)
        else:
            return self._format_board(data)
    
    def _format_board(self, data: Dict) -> str:
        """Format board data with shape information"""
        lines = []
        meta = data.get("metadata", {})
        
        lines.append(f"Board: {meta.get('boardId', 'Unknown')}")
        lines.append(f"Total Items: {meta.get('itemCount', 0)} | Connections: {meta.get('connectorCount', 0)}")
        
        if meta.get("bounds") != "full board":
            lines.append(f"Region: {meta.get('bounds')}")
        
        lines.append("")
        
        # Cache and format items
        items = data.get("items", [])
        if items:
            lines.append("=== ITEMS ===")
            
            # Group by type
            by_type = {}
            for item in items[:self.valves.max_items]:
                item_type = item.get("type", "unknown")
                if item_type not in by_type:
                    by_type[item_type] = []
                by_type[item_type].append(item)
                # Cache for connection lookup - use full ID
                self.item_cache[item["id"]] = item.get("text", "")
            
            for item_type, type_items in by_type.items():
                lines.append(f"\n{item_type.upper()} ({len(type_items)} items):")
                lines.append("-" * 40)
                
                # Special handling for shapes - show each one with full ID
                if item_type == "shape":
                    for idx, item in enumerate(type_items, 1):
                        item_id = item.get("id", "no-id")
                        shape = item.get("style", {}).get("shape", "unspecified")
                        text = item.get("text", "").strip()
                        
                        # Use full ID or significant portion
                        lines.append(f"{idx}. ID: {item_id}")
                        lines.append(f"   Shape Type: {shape}")
                        if text:
                            lines.append(f"   Text: {text}")
                        lines.append("")
                else:
                    # Regular items - show with better formatting
                    for idx, item in enumerate(type_items[:20], 1):
                        item_id = item.get("id", "no-id")
                        text = item.get("text", "").strip()
                        
                        if text:
                            lines.append(f"{idx}. {item_id}: {text}")
                        else:
                            lines.append(f"{idx}. {item_id}: (no text)")
            
            if len(items) > self.valves.max_items:
                lines.append(f"\n[{len(items) - self.valves.max_items} more items not shown]")
        
        # Format connections
        connections = data.get("connections", [])
        if connections:
            lines.append(f"\n=== CONNECTIONS ({len(connections)}) ===")
            
            for idx, conn in enumerate(connections[:self.valves.max_connections], 1):
                from_id = conn.get("from", "")
                to_id = conn.get("to", "")
                label = conn.get("label", "")
                
                from_text = self.item_cache.get(from_id, from_id)
                to_text = self.item_cache.get(to_id, to_id)
                
                if label:
                    lines.append(f"{idx}. {from_text} --[{label}]--> {to_text}")
                else:
                    lines.append(f"{idx}. {from_text} --> {to_text}")
            
            if len(connections) > self.valves.max_connections:
                lines.append(f"[{len(connections) - self.valves.max_connections} more connections not shown]")
        
        # Add graph summary if present
        graph = data.get("graph", {})
        if graph:
            lines.append(f"\nGraph Structure: {len(graph)} nodes")
            
            # Find root nodes
            roots = [nid for nid, node in graph.items() 
                    if not node.get("connections", {}).get("incoming")]
            if roots:
                lines.append(f"Root nodes: {len(roots)}")
        
        return "\n".join(lines)
    
    def _format_search(self, data: Dict) -> str:
        """Format search results with shape information"""
        lines = []
        
        lines.append(f"Search Query: '{data.get('query', '')}'")
        lines.append(f"Results Found: {data.get('resultCount', 0)}\n")
        
        items = data.get("items", [])
        for i, item in enumerate(items[:30], 1):
            text = item.get("text", "").strip()
            item_type = item.get("type", "unknown")
            item_id = item.get("id", "")
            shape = item.get("style", {}).get("shape")
            
            lines.append(f"{i}. Type: {item_type}")
            lines.append(f"   ID: {item_id}")
            
            if item_type == "shape" or shape:
                shape_info = shape or "unspecified"
                lines.append(f"   Shape: {shape_info}")
            
            if text:
                lines.append(f"   Text: {text}")
            
            lines.append("")
        
        if len(items) > 30:
            lines.append(f"[{len(items) - 30} more results not shown]")
        
        return "\n".join(lines)
    
    def _format_connections(self, data: Dict) -> str:
        """Format connection path with shape information"""
        lines = []
        summary = data.get("summary", {})
        
        lines.append(f"Connected Path from: {data.get('startItem', '')}")
        lines.append(f"Traversal Depth: {data.get('traversalDepth', 0)}")
        lines.append(f"Found: {summary.get('totalItems', 0)} items, {summary.get('totalConnections', 0)} connections")
        lines.append(f"Max depth reached: {summary.get('maxDepthReached', 0)}\n")
        
        # Show items with shape info
        items = data.get("items", [])
        if items:
            lines.append("=== CONNECTED ITEMS ===")
            for idx, item in enumerate(items[:50], 1):
                text = item.get("text", "").strip()
                item_type = item.get("type", "unknown")
                item_id = item.get("id", "")
                shape = item.get("style", {}).get("shape")
                
                lines.append(f"{idx}. ID: {item_id}")
                lines.append(f"   Type: {item_type}")
                
                if item_type == "shape" or shape:
                    shape_info = shape or "unspecified"
                    lines.append(f"   Shape: {shape_info}")
                
                if text:
                    lines.append(f"   Text: {text}")
                lines.append("")
        
        # Show paths
        paths = data.get("paths", [])
        if paths:
            lines.append("=== CONNECTION PATHS ===")
            by_depth = {}
            for path in paths:
                depth = path.get("depth", 0)
                if depth not in by_depth:
                    by_depth[depth] = []
                by_depth[depth].append(path)
            
            for depth in sorted(by_depth.keys())[:5]:
                lines.append(f"\nDepth {depth}:")
                for path in by_depth[depth][:10]:
                    lines.append(f"  {path['from']} --> {path['to']}")
        
        return "\n".join(lines)
    
    async def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        return body