import os
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse

# Import the FastMCP 'app' instance from coordinator.py
from analytics_mcp.coordinator import app as mcp_app

async def health_check(request):
    return JSONResponse({"status": "ok"})

# Mount the FastMCP ASGI application
app = Starlette(routes=[
    Route("/health", endpoint=health_check, methods=["GET"]),
    Mount("/mcp", app=mcp_app.streamable_http_app())
])

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
