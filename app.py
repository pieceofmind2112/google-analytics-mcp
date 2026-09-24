import os
import asyncio
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import Response
from mcp.server.sse import SseServerTransport

# Import the existing MCP server instance from the package
from analytics_mcp.server import server

# Initialize the SSE transport for StreamableHTTP
sse = SseServerTransport("/messages")

async def handle_sse(request):
    asyncio.create_task(server.run(sse, server.create_initialization_options()))
    return await sse.handle_sse(request)

async def handle_messages(request):
    await sse.handle_post_message(request)
    return Response()

# Bind the routes for Gemini Enterprise to connect to
app = Starlette(routes=[
    Route("/sse", endpoint=handle_sse, methods=["GET"]),
    Route("/messages", endpoint=handle_messages, methods=["POST"])
])

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
