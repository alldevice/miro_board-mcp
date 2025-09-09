# MIRO Board MCP Server

A self-hosted MCP (Model Context Protocol) server that bridges Claude.ai and OpenWebUI with MIRO boards.

## Features
- 🤖 Claude.ai integration via MCP protocol
- 🔌 OpenWebUI filter support
- 📊 Direct API access to MIRO boards
- 🔍 Search and navigation capabilities

## Quick Start
...

## Project Structure
miro-board-mcp/
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
├── .env.example          # Template for environment variables
├── docs/
│   ├── SETUP.md         # Detailed setup instructions
│   ├── API.md           # API documentation
│   └── EXAMPLES.md      # Usage examples
├── src/
│   ├── __init__.py
│   ├── miro_core.py     # Extract MiroCore class
│   ├── mcp_server.py    # MCP protocol handling
│   └── filter_server.py # OpenWebUI filter
├── tests/
│   └── test_mcp_client.py
├── scripts/
│   └── start_server.sh  # Startup script
└── docker/
    ├── Dockerfile
    └── docker-compose.yml

## Architecture
[Diagram showing OpenWebUI ↔ Server ↔ MIRO]

## Installation
...

## Configuration
...

## Usage Examples
...