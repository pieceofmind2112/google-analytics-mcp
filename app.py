import os
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse

# Importing the instance named 'server' from your file
from analytics_mcp.server import server 

async def health_check(request):
    return JSONResponse({"status": "ok"})

app = Starlette(routes=[
    Route("/health", endpoint=health_check, methods=["GET"]),
    Mount("/mcp", app=server.get_asgi_app())
])

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
