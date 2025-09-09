# API Reference

Complete reference for all Universal MIRO Server endpoints.

## Base URLs

- **Local Development**: `http://localhost:8001`
- **Production**: `https://your-domain.com`

## Authentication

MIRO authentication is handled server-side via `MIRO_ACCESS_TOKEN` in environment variables. No client authentication required for server endpoints.

## Endpoints Overview

| Endpoint | Method | Protocol | Purpose |
|----------|--------|----------|---------|
| `/sse` | GET/POST | MCP/SSE | Claude.ai integration |
| `/filter/miro/analyze` | POST | JSON | OpenWebUI filter |
| `/api/miro/board/{id}` | GET | REST | Get board content |
| `/api/miro/board/{id}/search` | GET | REST | Search board |
| `/api/miro/board/{id}/connections/{item_id}` | GET | REST | Get connections |
| `/health` | GET | JSON | Health check |
| `/` | GET | JSON | Service info |

## MCP Protocol Endpoints (Claude.ai)

### SSE Connection
```
GET /sse
Accept: text/event-stream
```

Establishes Server-Sent Events connection for MCP protocol.

**Response**: Event stream
```
data: {"type": "connection", "id": "uuid"}
```

### MCP Messages
```
POST /sse
Content-Type: application/json
```

**Request Body**:
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_miro_region",
    "arguments": {
      "boardId": "board_id",
      "bounds": {
        "left": -1000,
        "right": 1000,
        "top": -1000,
        "bottom": 1000
      }
    }
  },
  "id": 1
}
```

## Filter API Endpoints (OpenWebUI)

### Analyze Board
```
POST /filter/miro/analyze
Content-Type: application/json
```

**Request Body**:
```json
{
  "board_id": "XXXXXXXXXX",
  "command": "full_board",
  "params": {}
}
```

#### Available Commands

##### 1. full_board
Get entire board or filtered content.

**Parameters**:
```json
{
  "bounds": {
    "left": -1000,
    "right": 1000,
    "top": -1000,
    "bottom": 1000
  },
  "include_types": ["sticky_note", "shape", "text"]
}
```

##### 2. search
Search for items by text content.

**Parameters**:
```json
{
  "search_text": "customer",
  "case_sensitive": false
}
```

##### 3. connected_path
Trace connections from a starting item.

**Parameters**:
```json
{
  "start_item_id": "item_123",
  "max_depth": 5
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "metadata": {
      "boardId": "XXXXXXXXXX",
      "itemCount": 42,
      "connectorCount": 15
    },
    "items": [...],
    "connections": [...],
    "graph": {...}
  }
}
```

## REST API Endpoints

### Get Board Content
```
GET /api/miro/board/{board_id}
```

**Parameters**:
- `left` (float, optional): Left boundary
- `right` (float, optional): Right boundary  
- `top` (float, optional): Top boundary
- `bottom` (float, optional): Bottom boundary
- `types` (string, optional): Comma-separated item types

**Example**:
```bash
curl "https://server.com/api/miro/board/XXXXXXXXXX?types=sticky_note,shape"
```

**Response**:
```json
{
  "metadata": {
    "boardId": "XXXXXXXXXX",
    "itemCount": 25,
    "connectorCount": 10,
    "timestamp": "2025-01-15T10:00:00Z"
  },
  "items": [
    {
      "id": "item_123",
      "type": "sticky_note",
      "text": "Customer feedback",
      "position": {"x": 100, "y": 200},
      "style": {
        "color": "#FFE500"
      }
    }
  ],
  "connections": [
    {
      "id": "conn_456",
      "from": "item_123",
      "to": "item_789",
      "label": "relates to"
    }
  ]
}
```

### Search Board
```
GET /api/miro/board/{board_id}/search
```

**Parameters**:
- `q` (string, required): Search query
- `case_sensitive` (boolean, optional): Case-sensitive search

**Example**:
```bash
curl "https://server.com/api/miro/board/XXXXXXXXXX/search?q=customer"
```

### Get Connected Items
```
GET /api/miro/board/{board_id}/connections/{item_id}
```

**Parameters**:
- `depth` (integer, optional): Max traversal depth (default: 5)

**Example**:
```bash
curl "https://server.com/api/miro/board/XXXXXXXXXX/connections/item_123?depth=3"
```

## Utility Endpoints

### Health Check
```
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "miro_configured": true,
  "active_connections": 2,
  "interfaces": {
    "mcp": "active",
    "filter": "active",
    "api": "active"
  }
}
```

### Service Info
```
GET /
```

**Response**:
```json
{
  "service": "Universal Miro Server",
  "version": "2.0.0",
  "endpoints": {
    "claude_ai": {
      "sse": "/sse",
      "description": "MCP protocol for Claude.ai"
    },
    "openwebui": {
      "filter": "/filter/miro/analyze",
      "description": "Filter endpoints for OpenWebUI"
    }
  }
}
```

## Data Models

### Item Object
```typescript
{
  id: string
  type: "sticky_note" | "shape" | "text" | "card" | "frame"
  text: string
  position: {x: number, y: number}
  style: {
    color?: string
    shape?: string
  }
  tags: string[]
  createdBy?: string
  modifiedAt?: string
}
```

### Connection Object
```typescript
{
  id: string
  from: string  // Item ID
  to: string    // Item ID
  label?: string
  style?: string
}
```

### Graph Node
```typescript
{
  [itemId: string]: {
    text: string
    type: string
    connections: {
      outgoing: Array<{to: string, label?: string}>
      incoming: Array<{from: string, label?: string}>
    }
  }
}
```

## Error Responses

### Standard Error Format
```json
{
  "success": false,
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

### Common Error Codes
- `400` - Bad Request (missing parameters)
- `401` - Unauthorized (invalid MIRO token)
- `404` - Not Found (board/item not found)
- `429` - Rate Limited
- `500` - Internal Server Error

## Rate Limiting

MIRO API has rate limits:
- 100 requests per minute per token
- 10,000 requests per day per token

The server handles pagination automatically for large boards.

## WebSocket/SSE Considerations

For SSE connections:
- Keep-alive sent every 30 seconds
- Connection timeout: 86400 seconds (24 hours)
- Automatic reconnection recommended on client side

## Examples

### cURL Examples
```bash
# Get board
curl https://server.com/api/miro/board/BOARD_ID

# Search
curl "https://server.com/api/miro/board/BOARD_ID/search?q=todo"

# Get region
curl "https://server.com/api/miro/board/BOARD_ID?left=0&right=1000&top=0&bottom=1000"

# Filter specific types
curl "https://server.com/api/miro/board/BOARD_ID?types=sticky_note,shape"
```

### Python Examples
```python
import httpx
import asyncio

async def get_board(board_id):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://server.com/api/miro/board/{board_id}"
        )
        return response.json()

async def search_board(board_id, query):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://server.com/api/miro/board/{board_id}/search",
            params={"q": query}
        )
        return response.json()

# Run
board_data = asyncio.run(get_board("XXXXXXXXXX"))
search_results = asyncio.run(search_board("XXXXXXXXXX", "customer"))
```