# Quick Start Guide

Get Universal MIRO Server running locally in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- Git
- MIRO account with API access

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/alldevice/miro-board-mcp
cd miro-board-mcp
```

### 2. Setup Python Environment

#### Using venv (Standard)
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Using uv (Faster)
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create environment and install
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit .env file
nano .env  # or use your favorite editor
```

Add your MIRO access token:
```env
MIRO_ACCESS_TOKEN=your_actual_token_here
PORT=8001
LOG_LEVEL=INFO
```

### 4. Get MIRO Access Token

1. Go to https://miro.com/app/settings/user-profile/apps
2. Click "Create new app"
3. Give it a name (e.g., "MCP Server")
4. Copy the access token
5. Paste into `.env` file

### 5. Run the Server

```bash
python miro_mcp_server.py
```

You should see:
```
========================================
Universal Miro Server
========================================
Port: 8001
MIRO_ACCESS_TOKEN: Set
...
```

## Testing Your Setup

### Basic Health Check
```bash
curl http://localhost:8001/health
```

Expected response:
```json
{
  "status": "healthy",
  "miro_configured": true,
  "active_connections": 0
}
```

### Test with MIRO Board

1. Get a board ID from any MIRO board URL:
   - Example URL: `https://miro.com/app/board/XXXXXXXXXX/`
   - Board ID: `XXXXXXXXXX`

2. Test the API:
```bash
curl http://localhost:8001/api/miro/board/XXXXXXXXXX
```

### Run Test Suite
```bash
python test_mcp_client.py
```

## Connect to AI Services

### Local Claude.ai Testing
1. Use Claude Desktop App (if available)
2. Add MCP server: `http://localhost:8001/sse`

### Local OpenWebUI Testing
1. Install filter from `miro_mcp_filter.py`
2. Set server URL: `http://localhost:8001`

## Common Issues

### Port Already in Use
Change port in `.env`:
```env
PORT=8002
```

### MIRO Token Invalid
- Verify token in MIRO settings
- Check token has necessary permissions
- Regenerate if needed

### Dependencies Issues
```bash
# Clean install
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

## Next Steps

- ✅ [Connect to Claude.ai](CLAUDE_INTEGRATION.md)
- ✅ [Setup OpenWebUI Filter](OPENWEBUI_SETUP.md)
- ✅ [Deploy to Production](SETUP_GUIDE.md)
- ✅ [Explore API Endpoints](API_REFERENCE.md)

## Development Tips

### Enable Debug Logging
In `.env`:
```env
LOG_LEVEL=DEBUG
```

### Watch Logs
```bash
python miro_mcp_server.py 2>&1 | tee server.log
```

### Test Specific Board
```python
# Quick Python test
import httpx
import asyncio

async def test():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8001/api/miro/board/YOUR_BOARD_ID"
        )
        print(response.json())

asyncio.run(test())
```