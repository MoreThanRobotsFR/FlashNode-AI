import asyncio
import json
import logging
from typing import Any, Dict, List
import psutil

# MCP SDK Server
import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

# FlashNode-AI Core Modules
from core.device_scanner import device_scanner
from core.vault_manager import vault_manager
from core.gpio.power_rails import power_rails
from core.gpio.sequences import sequence_runner
from core.pipeline_engine import pipeline_engine
from core.gpio.factory import get_gpio_backend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

app = Server("flashnode-ai")

# -------------------------------------------------------------
# MCP Resources (If we wanted to expose logs as resources)
# -------------------------------------------------------------
@app.list_resources()
async def list_resources() -> list[types.Resource]:
    return []

# -------------------------------------------------------------
# MCP Tools
# -------------------------------------------------------------
@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_connected_hardware",
            description="List all physically connected USB devices, active serial COM ports, and the current state of power rails/GPIO.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="list_firmwares",
            description="Returns all firmwares currently stored in the Vault grouped by target.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="set_bootsel_mode_rp2040",
            description="Forces the RP2040 into BOOTSEL mode via GPIO manipulation.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="set_download_mode_esp32",
            description="Forces the ESP32 into ROM Download mode via EN and GPIO0 manipulation.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="power_cycle",
            description="Executes a complete power cycle of the target board (turns off 3V3 and 5V, waits, turns back on).",
            inputSchema={
                "type": "object",
                "properties": {
                    "off_ms": {"type": "integer", "description": "Time to stay off in milliseconds"}
                }
            }
        ),
        types.Tool(
            name="flash_rp2040",
            description="Flashes a firmware onto the RP2040 using picotool.",
            inputSchema={
                "type": "object",
                "properties": {
                    "firmware": {"type": "string", "description": "Name of the firmware file in the vault (e.g., main.uf2)"}
                },
                "required": ["firmware"]
            }
        ),
        types.Tool(
            name="flash_esp32",
            description="Flashes a firmware onto the ESP32 via esptool.",
            inputSchema={
                "type": "object",
                "properties": {
                    "firmware": {"type": "string", "description": "Name of the firmware file in the vault"},
                    "port": {"type": "string", "description": "Serial port (e.g. /dev/ttyUSB0)"},
                    "baud": {"type": "integer", "description": "Baudrate (default 921600)"}
                },
                "required": ["firmware", "port"]
            }
        ),
        types.Tool(
            name="get_system_status",
            description="Gets the Host System stats (CPU, RAM).",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
        # Add more tools like run_pipeline, verify checksums as needed
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    logger.info(f"LLM Called Tool: {name} with args: {arguments}")
    
    try:
        if name == "get_connected_hardware":
            result = {
                "usb": device_scanner.scan_usb_devices(),
                "serial": device_scanner.scan_serial_ports(),
                "gpio_status": power_rails.get_status()
            }
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
        elif name == "list_firmwares":
            result = vault_manager.list_firmwares()
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
        elif name == "set_bootsel_mode_rp2040":
            success = await sequence_runner.run_sequence("rp2040_bootsel")
            status = "Success" if success else "Failed"
            return [types.TextContent(type="text", text=f"Sequence rp2040_bootsel executed: {status}")]
            
        elif name == "set_download_mode_esp32":
            success = await sequence_runner.run_sequence("esp32_download")
            status = "Success" if success else "Failed"
            return [types.TextContent(type="text", text=f"Sequence esp32_download executed: {status}")]
            
        elif name == "power_cycle":
            off_ms = arguments.get("off_ms", 1000)
            power_rails.power_cycle(off_duration_ms=off_ms)
            return [types.TextContent(type="text", text=f"Power cycled (off for {off_ms}ms)")]
            
        elif name == "flash_rp2040":
            fw_name = arguments.get("firmware")
            fw_path = vault_manager.get_firmware_path("RP2040", fw_name)
            if not fw_path:
                return [types.TextContent(type="text", text=f"Error: Firmware {fw_name} not found in RP2040 vault.")]
            
            from core.flasher.picotool_runner import PicotoolRunner
            runner = PicotoolRunner()
            success = await runner.flash(fw_path)
            return [types.TextContent(type="text", text=f"Flash result: {'Success' if success else 'Failed'}")]
            
        elif name == "flash_esp32":
            fw_name = arguments.get("firmware")
            port = arguments.get("port")
            baud = arguments.get("baud", 921600)
            
            fw_path = vault_manager.get_firmware_path("ESP32", fw_name)
            if not fw_path:
                return [types.TextContent(type="text", text=f"Error: Firmware {fw_name} not found in ESP32 vault.")]
                
            from core.flasher.esptool_runner import EspToolRunner
            runner = EspToolRunner()
            success = await runner.flash(fw_path, port, baud)
            return [types.TextContent(type="text", text=f"Flash ESP32 result: {'Success' if success else 'Failed'}")]
            
        elif name == "get_system_status":
            result = {
                "cpu_percent": psutil.cpu_percent(),
                "ram_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent
            }
            return [types.TextContent(type="text", text=json.dumps(result))]
            
        else:
            return [types.TextContent(type="text", text=f"Unknown Tool: {name}")]
            
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [types.TextContent(type="text", text=f"Error executing tool {name}: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
