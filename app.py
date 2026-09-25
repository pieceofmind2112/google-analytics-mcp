import os
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse

# 1. Import your server object
from analytics_mcp.server import mcp

# 2. Add the required lightweight health endpoint
async def health_check(request):
    return JSONResponse({"status": "ok"})

# 3. Bind the routes and mount the official MCP streamable HTTP app
app = Starlette(routes=[
    Route("/health", endpoint=health_check, methods=["GET"]),
    # The MCP SDK automatically handles the Streamable HTTP transport here
Mount("/mcp", app=mcp.get_asgi_app())
])

if __name__ == "__main__":
    # Cloud Run compatibility: Bind to 0.0.0.0 and read the PORT variable
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
