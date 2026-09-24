import os
import asyncio
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse

# 1. Fix the ImportError: Import 'mcp' instead of 'server'
from analytics_mcp.server import mcp

# 2. Use Streamable HTTP transport for Gemini Enterprise compatibility
from mcp.server.streamable_http import StreamableHttpTransport

# Initialize the Streamable HTTP transport on the required endpoint
transport = StreamableHttpTransport("/mcp")

async def handle_mcp(request):
    # Bind the server to the transport
    asyncio.create_task(mcp.run(transport, mcp.create_initialization_options()))
    # Streamable HTTP handles both initialization and messages through this single handler
    return await transport.handle_request(request)

# 3. Add the required lightweight health endpoint
async def health_check(request):
    return JSONResponse({"status": "ok"})

# 4. Bind the routes for Gemini Enterprise and the health check
app = Starlette(routes=[
    Route("/mcp", endpoint=handle_mcp, methods=["GET", "POST"]),
    Route("/health", endpoint=health_check, methods=["GET"])
])

if __name__ == "__main__":
    # Cloud Run compatibility: Bind to 0.0.0.0 and read the PORT variable
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
