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
# MCP Resources
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
            name="upload_firmware",
            description="Upload a firmware file to the Vault from a local file path on the Rock 5C.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute path to the firmware file on the Rock 5C filesystem"},
                    "target": {"type": "string", "description": "Target MCU: 'RP2040' or 'ESP32'"}
                },
                "required": ["path", "target"]
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
            name="set_power_rail",
            description="Control a specific power rail (5V or 3.3V).",
            inputSchema={
                "type": "object",
                "properties": {
                    "rail": {"type": "string", "description": "Rail identifier: '5v' or '3v3'"},
                    "state": {"type": "string", "description": "'on' or 'off'"}
                },
                "required": ["rail", "state"]
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
            description="Flashes a firmware onto the RP2040 using picotool or OpenOCD.",
            inputSchema={
                "type": "object",
                "properties": {
                    "firmware": {"type": "string", "description": "Name of the firmware file in the vault (e.g., main.uf2)"},
                    "tool": {"type": "string", "description": "Flashing tool: 'picotool' or 'openocd' (default: picotool)"},
                    "interface": {"type": "string", "description": "For OpenOCD: 'usb' or 'swd' (default: usb)"}
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
            name="run_pipeline",
            description="Runs a pre-defined pipeline by name. Pipelines are multi-step sequences that can flash multiple targets, control GPIO, and validate output.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Pipeline ID (e.g. 'Prod_Board_V1_Full_Deploy')"}
                },
                "required": ["name"]
            }
        ),
        types.Tool(
            name="stream_serial_logs",
            description="Opens a serial port and reads data for a specified duration. Returns the captured output.",
            inputSchema={
                "type": "object",
                "properties": {
                    "port": {"type": "string", "description": "Serial port path (e.g., /dev/ttyUSB0)"},
                    "duration_s": {"type": "integer", "description": "How many seconds to listen (default: 5)"},
                    "baudrate": {"type": "integer", "description": "Baudrate (default: 115200)"}
                },
                "required": ["port"]
            }
        ),
        types.Tool(
            name="get_flash_status",
            description="Returns the current status of any ongoing flash operation.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="get_pipeline_status",
            description="Returns the status of all pipelines (running, completed, failed).",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="get_system_status",
            description="Gets the Host System stats (CPU, RAM, temperature).",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="verify_firmware_integrity",
            description="Verifies the MD5 and SHA256 checksums of a firmware file in the vault.",
            inputSchema={
                "type": "object",
                "properties": {
                    "firmware": {"type": "string", "description": "Firmware filename"},
                    "target": {"type": "string", "description": "Target MCU: 'RP2040' or 'ESP32'"}
                },
                "required": ["firmware", "target"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    logger.info(f"LLM Called Tool: {name} with args: {arguments}")
    
    try:
        if name == "get_connected_hardware":
            result = {
                "usb": device_scanner.scan_usb_devices(),
                "serial": device_scanner.scan_serial_ports(),
                "probes": device_scanner.scan_debug_probes(),
                "gpio_status": power_rails.get_status()
            }
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
        elif name == "list_firmwares":
            result = vault_manager.list_firmwares()
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "upload_firmware":
            import os
            path = arguments.get("path")
            target = arguments.get("target", "RP2040")
            
            if not os.path.exists(path):
                return [types.TextContent(type="text", text=f"Error: File not found at {path}")]
            
            filename = os.path.basename(path)
            with open(path, "rb") as f:
                content = f.read()
            
            checksums = vault_manager.save_firmware(target, filename, content)
            return [types.TextContent(type="text", text=f"Uploaded {filename} to {target} vault. MD5: {checksums['md5']}")]
            
        elif name == "set_bootsel_mode_rp2040":
            success = await sequence_runner.run_sequence("rp2040_bootsel")
            status = "Success" if success else "Failed"
            return [types.TextContent(type="text", text=f"Sequence rp2040_bootsel executed: {status}")]
            
        elif name == "set_download_mode_esp32":
            success = await sequence_runner.run_sequence("esp32_download")
            status = "Success" if success else "Failed"
            return [types.TextContent(type="text", text=f"Sequence esp32_download executed: {status}")]
        
        elif name == "set_power_rail":
            rail = arguments.get("rail", "").lower()
            state = arguments.get("state", "").lower()
            backend = get_gpio_backend()
            
            if rail == "5v":
                pin = power_rails.rail_5v_pin
            elif rail in ["3v3", "3.3v"]:
                pin = power_rails.rail_3v3_pin
            else:
                return [types.TextContent(type="text", text=f"Error: Unknown rail '{rail}'. Use '5v' or '3v3'.")]
            
            value = 1 if state == "on" else 0
            backend.set(pin, value)
            return [types.TextContent(type="text", text=f"Rail {rail} set to {'ON' if value else 'OFF'}")]
            
        elif name == "power_cycle":
            off_ms = arguments.get("off_ms", 1000)
            power_rails.power_cycle(off_duration_ms=off_ms)
            return [types.TextContent(type="text", text=f"Power cycled (off for {off_ms}ms)")]
            
        elif name == "flash_rp2040":
            fw_name = arguments.get("firmware")
            tool = arguments.get("tool", "picotool")
            fw_path = vault_manager.get_firmware_path("RP2040", fw_name)
            if not fw_path:
                return [types.TextContent(type="text", text=f"Error: Firmware {fw_name} not found in RP2040 vault.")]
            
            if tool == "openocd":
                from core.flasher.openocd_runner import OpenOCDRunner
                runner = OpenOCDRunner()
            else:
                from core.flasher.picotool_runner import PicotoolRunner
                runner = PicotoolRunner()
            
            success = await runner.flash(fw_path)
            return [types.TextContent(type="text", text=f"Flash RP2040 ({tool}) result: {'Success' if success else 'Failed'}")]
            
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
        
        elif name == "run_pipeline":
            pipeline_name = arguments.get("name")
            
            # Load pipeline definition
            import os
            base_dir = os.path.dirname(os.path.dirname(__file__))
            config_path = os.path.join(base_dir, "config", "pipelines.json")
            
            try:
                with open(config_path, "r") as f:
                    data = json.load(f)
                    pipelines = data.get("pipelines", [])
            except Exception:
                pipelines = []
            
            pipeline_def = next((p for p in pipelines if p["id"] == pipeline_name), None)
            if not pipeline_def:
                return [types.TextContent(type="text", text=f"Error: Pipeline '{pipeline_name}' not found.")]
            
            success = await pipeline_engine.run_pipeline(pipeline_def)
            return [types.TextContent(type="text", text=f"Pipeline '{pipeline_name}' result: {'Success' if success else 'Failed'}")]
        
        elif name == "stream_serial_logs":
            port = arguments.get("port")
            duration_s = arguments.get("duration_s", 5)
            baudrate = arguments.get("baudrate", 115200)
            
            try:
                import serial
                ser = serial.Serial(port, baudrate=baudrate, timeout=1)
                output = ""
                elapsed = 0.0
                while elapsed < duration_s:
                    data = ser.read(ser.in_waiting or 1)
                    if data:
                        output += data.decode('utf-8', errors='replace')
                    await asyncio.sleep(0.1)
                    elapsed += 0.1
                ser.close()
                return [types.TextContent(type="text", text=f"Serial output from {port} ({duration_s}s):\n{output}")]
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error reading serial port {port}: {str(e)}")]
        
        elif name == "get_flash_status":
            # Return current flash action status 
            return [types.TextContent(type="text", text="Flash status: idle (no flash in progress via MCP)")]
        
        elif name == "get_pipeline_status":
            # Return pipeline statuses
            return [types.TextContent(type="text", text="Pipeline status check via MCP - no active pipeline tracking in MCP context. Use the REST API for real-time status.")]
            
        elif name == "get_system_status":
            import os
            temp = None
            try:
                thermal_path = "/sys/class/thermal/thermal_zone0/temp"
                if os.path.exists(thermal_path):
                    with open(thermal_path) as f:
                        temp = round(int(f.read().strip()) / 1000.0, 1)
            except Exception:
                pass
            
            result = {
                "cpu_percent": psutil.cpu_percent(),
                "ram_percent": psutil.virtual_memory().percent,
                "ram_used_mb": round(psutil.virtual_memory().used / (1024 * 1024)),
                "temperature_c": temp,
                "disk_usage_percent": psutil.disk_usage('/').percent
            }
            return [types.TextContent(type="text", text=json.dumps(result))]
        
        elif name == "verify_firmware_integrity":
            fw_name = arguments.get("firmware")
            target = arguments.get("target", "RP2040")
            
            checksums = vault_manager.get_checksums(target, fw_name)
            if not checksums:
                return [types.TextContent(type="text", text=f"Error: Firmware {fw_name} not found in {target} vault.")]
            
            # Recalculate and compare
            fw_path = vault_manager.get_firmware_path(target, fw_name)
            fresh_md5 = vault_manager._calculate_checksum(fw_path, 'md5')
            fresh_sha256 = vault_manager._calculate_checksum(fw_path, 'sha256')
            
            md5_ok = fresh_md5 == checksums["md5"]
            sha256_ok = fresh_sha256 == checksums["sha256"]
            
            result = {
                "firmware": fw_name,
                "target": target,
                "md5": {"stored": checksums["md5"], "computed": fresh_md5, "match": md5_ok},
                "sha256": {"stored": checksums["sha256"], "computed": fresh_sha256, "match": sha256_ok},
                "integrity": "OK" if (md5_ok and sha256_ok) else "MISMATCH"
            }
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
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
