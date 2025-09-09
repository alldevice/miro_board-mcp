# OpenWebUI Filter Setup Guide

Complete guide for integrating Universal MIRO Server with OpenWebUI using the Filter API.

## Overview

The OpenWebUI filter allows you to access MIRO boards directly within your OpenWebUI chat interface, enabling seamless board analysis during conversations.

## Prerequisites

- OpenWebUI instance (v0.1.0 or higher)
- Universal MIRO Server running and accessible
- Admin access to OpenWebUI

## Installation Steps

### Step 1: Access OpenWebUI Admin

1. Log in to your OpenWebUI instance
2. Navigate to **Settings** (gear icon)
3. Go to **Admin Settings** → **Filters**

### Step 2: Create New Filter

1. Click **"Add Filter"** or **"New Filter"**
2. Give it a name: `MIRO Board Reader`
3. Set priority: `10` (or higher for precedence)

### Step 3: Install Filter Code

1. Copy the entire content from `miro_mcp_filter.py`
2. Paste into the filter code editor
3. **Important**: Update the server URL in the Valves class:

```python
class Valves(BaseModel):
    miro_server_url: str = Field(
        default="https://your-server.com",  # Change this!
        description="Your Miro Server URL"
    )
```

For local testing:
```python
default="http://localhost:8001"
```

For production:
```python
default="https://miromcp.duckdns.org"
```

### Step 4: Configure Filter Settings

1. After saving, click on the filter settings (gear icon)
2. Configure the valves:
   - **enabled**: `true`
   - **priority**: `10`
   - **miro_server_url**: Your server URL
   - **max_items**: `100` (adjust as needed)
   - **max_connections**: `50` (adjust as needed)

### Step 5: Enable for Models

1. Go to **Models** section
2. Select the model you want to use
3. In **Filters** section, enable "MIRO Board Reader"
4. Save changes

## Usage Instructions

### Basic Commands

The filter automatically detects MIRO board requests. Use these patterns:

#### 1. Get Full Board
```
Analyze MIRO board [XXXXXXXXXX]

Get all items from board [board_id]

Show me board: XXXXXXXXXX
```

#### 2. Search Board
```
Search for "customer" in board [XXXXXXXXXX]

Find "TODO" in board [board_id]

Look for 'project timeline' in [board_id]
```

#### 3. Get Specific Types
```
Show only shapes from board [board_id]

Get sticky notes from [XXXXXXXXXX]

Filter only sticky_note, card items from [board_id]
```

#### 4. Trace Connections
```
Show connections from item: item_123 in board [board_id]

Trace path from item_456 with depth: 3

Get connected items starting at item_id in [board_id]
```

#### 5. Get Board Region
```
Get region from board [board_id] bounds: left: 0, right: 1000, top: 0, bottom: 1000

Show items in region left: -500, right: 500 from [board_id]
```

## How It Works

### Detection Flow

1. **Message Interception**: Filter checks each message for MIRO patterns
2. **Request Parsing**: Extracts board ID and command type
3. **Server Communication**: Sends request to MIRO server
4. **Data Injection**: Adds MIRO data as system message
5. **AI Processing**: Model processes with full board context

### Request Patterns

The filter recognizes these patterns:

```python
# Board ID patterns
[board_id]           # Square brackets
board: board_id      # With "board:" prefix
miro.com/app/board/  # From URL

# Command patterns
"search"/"find"      → Search command
"connection"/"path"  → Connection tracing
"region"/"bounds"    → Regional extraction
"only"/"filter"      → Type filtering
```

## Advanced Configuration

### Custom Valves

Edit filter settings for fine-tuning:

```python
class Valves(BaseModel):
    priority: int = 0  # Higher = processed first
    miro_server_url: str = "https://your-server.com"
    enabled: bool = True
    max_items: int = 100  # Limit items shown
    max_connections: int = 50  # Limit connections shown
```

### Multiple Servers

For different environments:

```python
def __init__(self):
    self.valves = self.Valves()
    # Dynamic server selection
    import os
    if os.getenv("ENVIRONMENT") == "production":
        self.valves.miro_server_url = "https://prod-server.com"
    else:
        self.valves.miro_server_url = "http://localhost:8001"
```

## Troubleshooting

### Filter Not Working

**"Filter not triggering"**
- Check filter is enabled for your model
- Verify priority is set (higher = better)
- Ensure board ID is in correct format `[board_id]`

**"No data returned"**
- Check server URL is correct
- Verify server is running: `curl https://your-server/health`
- Check OpenWebUI logs for errors

### Connection Issues

**"Failed to connect to server"**
```python
# Add debugging to filter
print(f"[Miro Filter] Connecting to: {self.valves.miro_server_url}")
print(f"[Miro Filter] Request: {request}")
```

**"Timeout errors"**
```python
# Increase timeout in filter
async with aiohttp.ClientSession() as session:
    async with session.post(url, json=request, timeout=60) as response:
        # ...
```

### Data Issues

**"Items not showing"**
- Check `max_items` valve setting
- Verify MIRO token has correct permissions
- Board might be too large (pagination needed)

**"✓ Miro data loaded" but no data**
- Server might be returning empty results
- Check server logs: `sudo journalctl -u miro-mcp -f`
- Verify board ID is correct

## Performance Optimization

### Large Boards

For boards with many items:

1. **Increase limits**:
```python
max_items: int = Field(default=200)
max_connections: int = Field(default=100)
```

2. **Use type filtering**:
```
Show only sticky_note from board [large_board_id]
```

3. **Use regions**:
```
Get items from left: 0, right: 1000 in board [board_id]
```

### Caching

The filter includes basic caching:

```python
def __init__(self):
    self.valves = self.Valves()
    self.item_cache = {}  # Caches items for connection lookup
```

## Testing

### Test Filter Installation

1. Send a test message:
```
Test: Get board [test_board_id]
```

2. Check OpenWebUI logs for filter activity
3. Verify "✓ Miro data loaded" appears

### Test Server Connection

From OpenWebUI server:
```bash
curl -X POST https://your-miro-server/filter/miro/analyze \
  -H "Content-Type: application/json" \
  -d '{"board_id":"test","command":"full_board","params":{}}'
```

### Debug Mode

Add debug output to filter:

```python
async def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
    print(f"[DEBUG] Inlet called with: {body.get('messages', [])[-1] if body.get('messages') else 'No messages'}")
    # ... rest of code
```

## Examples

### Project Management
```
User: Analyze my sprint board [XXXXXXXXXX] and list all 
incomplete tasks