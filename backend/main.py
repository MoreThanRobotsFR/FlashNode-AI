from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging

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

app = FastAPI(
    title="FlashNode-AI API",
    description="Station de programmation et test matériel",
    version="1.0.0"
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

@app.get("/")
def read_root():
    return {"message": "Welcome to FlashNode-AI API"}

# Run the app directly if executed (for dev)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
