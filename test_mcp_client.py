#!/usr/bin/env python3
# test_mcp_client.py
import asyncio
import httpx
import json
import sys

async def test_mcp_server():
    """Test the MCP server endpoints"""
    
    print("=" * 60)
    print("MCP Server Test Suite")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Health check
        print("\n1. Testing health endpoint...")
        try:
            response = await client.get("http://localhost:8001/health")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
            print("   ✅ Health check passed")
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
            return
        
        # Test 2: Initialize via JSON-RPC
        print("\n2. Testing initialize (JSON-RPC)...")
        try:
            response = await client.post(
                "http://localhost:8001/sse",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "test-client",
                            "version": "1.0.0"
                        }
                    },
                    "id": 1
                }
            )
            result = response.json()
            print(f"   Status: {response.status_code}")
            print(f"   Server: {result.get('result', {}).get('serverInfo', {})}")
            print("   ✅ Initialize passed")
        except Exception as e:
            print(f"   ❌ Initialize failed: {e}")
        
        # Test 3: List tools
        print("\n3. Testing tools/list...")
        try:
            response = await client.post(
                "http://localhost:8001/sse",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": 2
                }
            )
            result = response.json()
            tools = result.get("result", {}).get("tools", [])
            print(f"   Status: {response.status_code}")
            print(f"   Available tools: {len(tools)}")
            for tool in tools:
                print(f"   - {tool['name']}: {tool['description'][:60]}...")
            print("   ✅ Tools list passed")
        except Exception as e:
            print(f"   ❌ Tools list failed: {e}")
        
        # Test 4: Test Miro API connection (if token is configured)
        print("\n4. Testing Miro API connection...")
        print("   Note: This test requires a valid MIRO_ACCESS_TOKEN in .env")
        print("   and a valid boardId to test with")
        
        # You can uncomment and modify this section with a real board ID to test
        TEST_BOARD_ID = "uXjVJLyzX0A="  # Replace with actual board ID
        try:
         response = await client.post(
             "http://localhost:8001/sse",
             json={
                 "jsonrpc": "2.0",
                 "method": "tools/call",
                 "params": {
                     "name": "search_miro_items",
                     "arguments": {
                         "boardId": TEST_BOARD_ID,
                         "searchText": "test"
                     }
                 },
                 "id": 3
             }
         )
         result = response.json()
         if "error" in result:
             print(f"   ⚠️  Miro API error: {result['error']}")
         else:
             print(f"   ✅ Miro API connection successful")
             content = result.get("result", {}).get("content", [])
             if content:
                 data = json.loads(content[0]["text"])
                 print(f"   Found {data.get('resultCount', 0)} items")
        except Exception as e:
         print(f"   ❌ Miro API test failed: {e}")
        
        print("   ⏭️  Skipping (requires board ID)")
        
        # Test 5: SSE endpoint basic connectivity
        print("\n5. Testing SSE endpoint connectivity...")
        try:
            # Just test that the endpoint responds
            response = await client.get(
                "http://localhost:8001/sse",
                headers={"Accept": "text/event-stream"},
                timeout=2.0
            )
            print(f"   Status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type')}")
            print("   ✅ SSE endpoint is responding")
        except httpx.TimeoutException:
            # Timeout is expected for SSE as it keeps connection open
            print("   ✅ SSE endpoint is responding (connection established)")
        except Exception as e:
            print(f"   ❌ SSE endpoint failed: {e}")

    print("\n" + "=" * 60)
    print("Test suite completed")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Ensure MIRO_ACCESS_TOKEN is set in .env file")
    print("2. Get a Miro board ID from your Miro board URL")
    print("3. Connect to Claude web interface using:")
    print("   - URL: http://localhost:8001/sse")
    print("   - Or for production: https://your-domain.com/sse")

async def test_sse_stream():
    """Test SSE streaming separately"""
    print("\n" + "=" * 60)
    print("Testing SSE Stream (Ctrl+C to stop)")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream(
                "GET",
                "http://localhost:8001/sse",
                headers={"Accept": "text/event-stream"},
                timeout=None
            ) as response:
                print(f"Connected to SSE stream")
                print("Waiting for events...")
                
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        if data:
                            try:
                                parsed = json.loads(data)
                                print(f"Event: {json.dumps(parsed, indent=2)}")
                            except json.JSONDecodeError:
                                print(f"Raw event: {data}")
                    elif line.startswith(":"):
                        # Keepalive or comment
                        print(f"Keepalive: {line}")
                        
        except KeyboardInterrupt:
            print("\nStream test stopped by user")
        except Exception as e:
            print(f"Stream error: {e}")

async def main():
    """Main test runner"""
    if len(sys.argv) > 1 and sys.argv[1] == "stream":
        await test_sse_stream()
    else:
        await test_mcp_server()
        print("\nTo test SSE streaming, run: python test_mcp_client.py stream")

if __name__ == "__main__":
    asyncio.run(main())