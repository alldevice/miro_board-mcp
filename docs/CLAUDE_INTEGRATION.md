# Claude.ai Integration Guide

Complete guide for connecting Universal MIRO Server to Claude.ai using MCP (Model Context Protocol).

## Overview

The MCP integration allows Claude to directly access and analyze your MIRO boards through natural language commands.

## Setup Methods

### Method 1: Claude Web Interface (Recommended)

1. **Open Claude.ai**
   - Go to https://claude.ai
   - Sign in to your account

2. **Access MCP Settings**
   - Click on your profile/avatar (top right)
   - Select "Settings" or "Integrations"
   - Look for "MCP Servers" or "Custom Connectors"

3. **Add MCP Server**
   - Click "Add Server" or "New Connection"
   - Enter server URL:
     - Production: `https://your-domain.com/sse`
     - Local testing: `http://localhost:8001/sse`
   - Name: "MIRO Board Reader"
   - Click "Connect"

4. **Verify Connection**
   - You should see a green indicator
   - Claude will confirm the connection

### Method 2: Claude Desktop App

1. **Install Claude Desktop**
   - Download from Anthropic website
   - Install and sign in

2. **Configure MCP**
   - Open settings
   - Navigate to MCP/Integrations
   - Add server URL

## Available Tools

Once connected, Claude has access to three main tools:

### 1. get_miro_region
Retrieves items from a specific region of the board.

**Example prompts**:
```
Get all items from MIRO board [XXXXXXXXXX]

Show me the top-left section of board [board_id] 
(coordinates: left: -1000, right: 0, top: -1000, bottom: 0)

Get only sticky notes and shapes from board [board_id]
```

### 2. search_miro_items
Searches for items containing specific text.

**Example prompts**:
```
Search for "customer" in board [XXXXXXXXXX]

Find all items mentioning "TODO" in board [board_id]

Look for "project timeline" in my MIRO board [board_id] (case-sensitive)
```

### 3. get_miro_connected_path
Traces connections from a starting item.

**Example prompts**:
```
Show all items connected to item [item_123] in board [board_id]

Trace connections from [item_id] with depth of 3 in board [board_id]

Find the connection path starting from the main concept node [item_id]
```

## Usage Examples

### Basic Board Analysis
```
User: Analyze the MIRO board [XXXXXXXXXX] and create a summary

Claude: I'll analyze your MIRO board now...
[Uses get_miro_region tool]

Based on the board analysis, here's what I found:
- 42 sticky notes containing user feedback
- 15 process flow shapes connected in sequence
- 8 text annotations providing context
[...]
```

### Creating Documentation
```
User: Get all items from board [XXXXXXXXXX] and create a 
markdown table organizing them by type

Claude: I'll retrieve all items from your board and organize them...
[Uses get_miro_region tool]

| Type | Count | Key Items |
|------|-------|-----------|
| Sticky Notes | 25 | Customer feedback, Bug reports, Feature requests |
| Shapes | 15 | Process steps, Decision points |
| Connectors | 20 | Flow arrows, Relationships |
[...]
```

### Finding Specific Content
```
User: Search for all mentions of "deadline" in board [board_id] 
and list them with urgency

Claude: I'll search for all deadline mentions...
[Uses search_miro_items tool]

Found 5 items mentioning "deadline":
🔴 URGENT: "Project deadline - Jan 31" (Item #234)
🟡 SOON: "Design deadline - Feb 15" (Item #567)
[...]
```

### Tracing Workflows
```
User: Starting from the "Project Start" node, show me the 
complete workflow in board [board_id]

Claude: I'll trace the workflow from your starting point...
[Uses get_miro_connected_path tool]

Workflow path from "Project Start":
1. Project Start
   → 2. Requirements Gathering
      → 3. Design Phase
         → 4a. Development
         → 4b. Testing (parallel)
[...]
```

## Best Practices

### 1. Board ID Format
Always include board IDs in square brackets:
- ✅ Good: `[XXXXXXXXXX]`
- ❌ Bad: `XXXXXXXXXX`

### 2. Specific Requests
Be specific about what you want:
- ✅ Good: "Create a table of all sticky notes grouped by color"
- ❌ Vague: "Show me the board"

### 3. Large Boards
For large boards, use regions or filtering:
```
Get items from the planning section (left: 0, right: 2000) of board [id]
Show only sticky notes and cards from board [id]
```

### 4. Complex Analysis
Chain multiple requests for detailed analysis:
```
1. First, search for all "Phase" items in board [id]
2. Then, for each phase, show connected tasks
3. Finally, create a project timeline
```

## Troubleshooting

### Connection Issues

**"Failed to connect to MCP server"**
- Verify server is running: `curl https://your-server/health`
- Check SSL certificate is valid
- Ensure firewall allows HTTPS (port 443)

**"No tools available"**
- Server may not be properly initialized
- Try disconnecting and reconnecting
- Check server logs: `sudo journalctl -u miro-mcp -f`

### Performance Issues

**Slow responses**
- Large boards may take time to load
- Use filtering to reduce data: `include_types: ["sticky_note"]`
- Check server resources (CPU, memory)

**Timeout errors**
- Increase timeout in server configuration
- Use region-based queries for large boards
- Consider pagination for very large datasets

### Data Issues

**"Board not found"**
- Verify board ID is correct
- Check MIRO access token has permission
- Board might be private or deleted

**Missing items**
- Some item types might be filtered
- Check if items are in specified region
- Verify MIRO API permissions

## Advanced Features

### Custom Workflows
Create complex workflows by combining tools:

```python
# Pseudo-code for Claude's internal process
1. board_data = get_miro_region(board_id)
2. important_items = search_miro_items(board_id, "important")
3. for item in important_items:
     connections = get_miro_connected_path(board_id, item.id)
4. generate_report(board_data, important_items, connections)
```

### Batch Processing
Process multiple boards:
```
Analyze boards [board1], [board2], and [board3] and compare their structures
```

### Real-time Collaboration
While the server doesn't support real-time updates, you can:
```
Every 30 minutes, check board [id] for new items added today
```

## Security Considerations

1. **Token Security**: MIRO token is stored server-side, not exposed to Claude
2. **Read-only Access**: Current implementation is read-only
3. **SSL Required**: Always use HTTPS in production
4. **Access Control**: Consider implementing user authentication for multi-user setups

## Limitations

- **Read-only**: Cannot create or modify MIRO items
- **Rate Limits**: Subject to MIRO API rate limits
- **Large Boards**: May need pagination for boards with >1000 items
- **Real-time**: No live updates; requires manual refresh

## Tips for Effective Use

1. **Start Simple**: Begin with basic queries before complex analysis
2. **Use Examples**: Provide example output format to Claude
3. **Iterate**: Refine queries based on initial results
4. **Save Prompts**: Keep successful prompt patterns for reuse
5. **Combine Tools**: Use multiple tools for comprehensive analysis

## Example Conversation Flow

```
You: Hi Claude, I need help analyzing my project board

Claude: I'd be happy to help analyze your project board! 
Could you provide the MIRO board ID? It typically looks 
like [XXXXXXXXXX] and can be found in your board's URL.

You: The board ID is [XXXXXXXXXX]

Claude: Perfect! Let me analyze your board... 
[Retrieves board data]

I can see your board contains 47 items including sticky notes, 
shapes, and connections. Would you like me to:
1. Create a summary of all content
2. Search for specific items
3. Trace workflows and connections
4. Generate documentation

What would be most helpful?

You: Create a summary organized by project phases

Claude: I'll organize the content by project phases...
[Continues with detailed analysis]
```

## Support

For issues specific to Claude.ai integration:
1. Check [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Review server logs
3. Open an issue on GitHub
4. Contact Anthropic support for Claude-specific issues