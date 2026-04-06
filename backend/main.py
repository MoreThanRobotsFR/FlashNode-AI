from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import logging
import os
import sys
import subprocess
from contextlib import asynccontextmanager

# Load environment variables from .env file FIRST
load_dotenv()

# We can import our modules locally after env load
from core.gpio.factory import get_gpio_backend

# Import Routers
from api.v1.firmware import router as firmware_router
from api.v1.devices import router as devices_router
from api.v1.actions import router as actions_router
from api.v1.pipeline import router as pipeline_router
from api.v1.gpio import router as gpio_router
from api.v1.debug import router as debug_router
from api.v1.system import router as system_router

# Import WS
from ws.flash_ws import router as flash_ws_router
from ws.serial_ws import router as serial_ws_router
from ws.devices_ws import router as devices_ws_router
from ws.system_ws import router as system_ws_router
from ws.pipeline_ws import router as pipeline_ws_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the MCP Server as a background process
    logger.info("Starting MCP Server in SSE HTTP mode...")
    mcp_path = os.path.join(os.path.dirname(__file__), "mcp_server.py")
    
    # We pass the same python executable so it runs in the same environment (e.g. venv)
    mcp_process = subprocess.Popen(
        [sys.executable, mcp_path, "--sse"],
        env=os.environ.copy()
    )
    logger.info(f"MCP Server started with PID {mcp_process.pid} on port 8001")
    
    yield  # The main FastAPI backend runs here
    
    # Shutdown the MCP Server when FastAPI shuts down
    logger.info("Shutting down MCP Server...")
    mcp_process.terminate()
    try:
        mcp_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        logger.warning("MCP Server did not terminate gracefully, killing it...")
        mcp_process.kill()

app = FastAPI(
    title="FlashNode-AI API",
    description="Station de programmation et test matériel",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev. In prod, lock this down.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(firmware_router, prefix="/api/v1")
app.include_router(devices_router, prefix="/api/v1")
app.include_router(actions_router, prefix="/api/v1")
app.include_router(pipeline_router, prefix="/api/v1")
app.include_router(gpio_router, prefix="/api/v1")
app.include_router(debug_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")

# Include WS
app.include_router(flash_ws_router, prefix="/ws")
app.include_router(serial_ws_router, prefix="/ws")
app.include_router(devices_ws_router, prefix="/ws")
app.include_router(system_ws_router, prefix="/ws")
app.include_router(pipeline_ws_router, prefix="/ws")

# Initialize GPIO backend immediately to log which one is used
gpio_backend = get_gpio_backend()
logger.info(f"Initialized GPIO backend: {gpio_backend.__class__.__name__}")

# ---- Serve Frontend (Production) ----
# Look for built frontend in multiple possible locations
_frontend_dist = None
for _candidate in [
    os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist'),       # Dev: ../frontend/dist
    os.path.join(os.path.dirname(__file__), '..', 'frontend_dist'),           # Docker: ../frontend_dist
    '/opt/flashnode/frontend_dist',                                           # Systemd install
]:
    if os.path.isdir(_candidate):
        _frontend_dist = os.path.abspath(_candidate)
        break

if _frontend_dist:
    logger.info(f"Serving frontend from: {_frontend_dist}")
    # Serve static assets (js, css, images)
    app.mount("/assets", StaticFiles(directory=os.path.join(_frontend_dist, "assets")), name="frontend-assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(_frontend_dist, "index.html"))

    # SPA catch-all: any path that doesn't match /api or /ws returns index.html
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        # Don't intercept API or WS routes
        if full_path.startswith(("api/", "ws/", "docs", "openapi.json", "redoc")):
            return {"detail": "Not found"}
        # Try to serve a static file first
        static_file = os.path.join(_frontend_dist, full_path)
        if os.path.isfile(static_file):
            return FileResponse(static_file)
        # Fallback to index.html for SPA routing
        return FileResponse(os.path.join(_frontend_dist, "index.html"))
else:
    logger.info("No frontend build found. API-only mode.")

    @app.get("/")
    def read_root():
        return {"message": "Welcome to FlashNode-AI API", "docs": "/docs"}

# Run the app directly if executed (for dev)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
