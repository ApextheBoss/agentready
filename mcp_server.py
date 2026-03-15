"""
AgentReady MCP Server — Expose website agent-readiness scanning as an MCP tool.
Other AI agents can discover and use this to check if websites are ready for them.
"""

import asyncio
import json
import sys
from scanner import scan


async def handle_request(request: dict) -> dict:
    """Handle JSON-RPC request."""
    method = request.get("method", "")
    req_id = request.get("id")
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "agentready",
                    "version": "0.1.0"
                }
            }
        }
    
    elif method == "notifications/initialized":
        return None  # No response for notifications
    
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "scan_website",
                        "description": "Score how well a website serves AI agents. Returns a 0-100 score, letter grade (A-F), and detailed checks for llms.txt, robots.txt AI crawler rules, structured data, content extractability, and more.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "url": {
                                    "type": "string",
                                    "description": "The URL to scan (e.g. https://example.com)"
                                }
                            },
                            "required": ["url"]
                        }
                    }
                ]
            }
        }
    
    elif method == "tools/call":
        tool_name = request.get("params", {}).get("name")
        args = request.get("params", {}).get("arguments", {})
        
        if tool_name == "scan_website":
            url = args.get("url", "")
            if not url:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": "Error: URL is required"}],
                        "isError": True
                    }
                }
            
            try:
                result = await scan(url)
                data = result.to_dict()
                
                # Format as readable text
                lines = [
                    f"# AgentReady Score: {data['overall_score']}/100 (Grade: {data['grade']})",
                    f"URL: {data['url']}",
                    f"Scan time: {data['scan_time_ms']}ms",
                    "",
                    "## Checks:"
                ]
                
                for check in data['checks']:
                    icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}.get(check['status'], "?")
                    lines.append(f"- {icon} **{check['name']}**: {check['score']}/{check['max_score']} — {check['detail']}")
                    if check.get('recommendation'):
                        lines.append(f"  → {check['recommendation']}")
                
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": "\n".join(lines)}]
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error scanning {url}: {str(e)}"}],
                        "isError": True
                    }
                }
        
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
        }
    
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Unknown method: {method}"}
    }


async def main():
    """Run MCP server over stdio."""
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
    
    writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(
        asyncio.streams.FlowControlMixin, sys.stdout
    )
    writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, asyncio.get_event_loop())
    
    while True:
        # Read Content-Length header
        header = b""
        while True:
            line = await reader.readline()
            if line == b"\r\n" or line == b"\n":
                break
            header += line
        
        # Parse content length
        content_length = 0
        for h in header.decode().split("\n"):
            if h.lower().startswith("content-length:"):
                content_length = int(h.split(":")[1].strip())
        
        if content_length == 0:
            continue
        
        # Read body
        body = await reader.readexactly(content_length)
        request = json.loads(body.decode())
        
        response = await handle_request(request)
        
        if response is None:
            continue
        
        # Write response
        response_bytes = json.dumps(response).encode()
        header = f"Content-Length: {len(response_bytes)}\r\n\r\n"
        writer.write(header.encode() + response_bytes)
        await writer.drain()


if __name__ == "__main__":
    asyncio.run(main())
