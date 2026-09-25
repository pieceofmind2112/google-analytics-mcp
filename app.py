import os
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse

# 1. Import your actual FastMCP instance!
# REPLACE 'mcp_server' with the variable name you assigned to FastMCP(...) in server.py
from analytics_mcp.server import mcp_server 

# 2. Add the required lightweight health endpoint
async def health_check(request):
    return JSONResponse({"status": "ok"})

# 3. Bind the routes and mount the FastMCP ASGI app
app = Starlette(routes=[
    Route("/health", endpoint=health_check, methods=["GET"]),
    Mount("/mcp", app=mcp_server.get_asgi_app())
])

if __name__ == "__main__":
    # Cloud Run compatibility: Bind to 0.0.0.0 and read the PORT variable
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
