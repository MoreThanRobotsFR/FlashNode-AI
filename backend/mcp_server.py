"""
FlashNode-AI — MCP Server
Model Context Protocol server exposing 15 tools for AI-driven hardware programming.

Supports two transport modes:
  - stdio  : For Claude Desktop launching the script locally
  - sse    : For remote network access (HTTP SSE on port 8001)

Usage:
  python mcp_server.py              # stdio mode (default)
  python mcp_server.py --sse        # SSE HTTP mode on port 8001
"""

import asyncio
import json
import logging
import os
import sys
import time as _time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure that the directory containing mcp_server.py is in the search path.
# This allows importing from 'core', etc., even if launched from the project root.
_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

import psutil

# MCP SDK
import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

# FlashNode-AI Core Modules
from core.device_scanner import device_scanner
from core.vault_manager import vault_manager
from core.history_db import history_db
from core.gpio.power_rails import power_rails
from core.gpio.sequences import sequence_runner
from core.pipeline_engine import pipeline_engine
from core.gpio.factory import get_gpio_backend

# Configure logging to use stderr so it doesn't pollute the stdio MCP transport (which uses stdout).
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("mcp_server")

app = Server("flashnode-ai")

# ─────────────────────────────────────────────────
# State tracking for flash and pipeline operations
# ─────────────────────────────────────────────────
_flash_state = {
    "status": "idle",      # idle | running | success | failed
    "tool": None,
    "target": None,
    "firmware": None,
    "progress": 0,
    "step": "",
    "started_at": None,
    "finished_at": None,
    "error": None,
}

_pipeline_state = {
    "status": "idle",      # idle | running | completed | failed | cancelled
    "pipeline_id": None,
    "current_step": 0,
    "total_steps": 0,
    "step_details": None,
    "started_at": None,
    "finished_at": None,
    "error": None,
}

_pipelines_cache = None


def _reset_flash_state():
    _flash_state.update({
        "status": "idle", "tool": None, "target": None, "firmware": None,
        "progress": 0, "step": "", "started_at": None, "finished_at": None, "error": None,
    })


def _reset_pipeline_state():
    _pipeline_state.update({
        "status": "idle", "pipeline_id": None, "current_step": 0, "total_steps": 0,
        "step_details": None, "started_at": None, "finished_at": None, "error": None,
    })


def _load_pipelines():
    """Load and cache pipelines.json"""
    global _pipelines_cache
    if _pipelines_cache is not None:
        return _pipelines_cache

    base_dir = os.path.dirname(os.path.dirname(__file__))
    config_path = os.path.join(base_dir, "config", "pipelines.json")
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
            _pipelines_cache = data.get("pipelines", [])
    except Exception:
        _pipelines_cache = []
    return _pipelines_cache


# Pipeline progress callback for state tracking
async def _pipeline_progress_callback(pipeline_id, step_idx, total, status, step_details):
    _pipeline_state["pipeline_id"] = pipeline_id
    _pipeline_state["current_step"] = step_idx
    _pipeline_state["total_steps"] = total
    _pipeline_state["status"] = status
    _pipeline_state["step_details"] = step_details
    if status in ("completed", "failed", "cancelled", "error"):
        _pipeline_state["finished_at"] = _time.time()


# ─────────────────────────────────────────────────
# MCP Resources (4 resources)
# ─────────────────────────────────────────────────
@app.list_resources()
async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri="flashnode://vault/firmwares",
            name="Firmware Vault",
            description="All firmware files stored in the vault, grouped by target (RP2040, ESP32).",
            mimeType="application/json"
        ),
        types.Resource(
            uri="flashnode://system/status",
            name="System Status",
            description="Current Rock 5C system metrics (CPU, RAM, temperature, uptime).",
            mimeType="application/json"
        ),
        types.Resource(
            uri="flashnode://gpio/status",
            name="GPIO & Power Rails Status",
            description="Current state of all GPIO pins and power rails.",
            mimeType="application/json"
        ),
        types.Resource(
            uri="flashnode://history",
            name="Operation History",
            description="Recent flash, pipeline, and GPIO operation history from the SQLite log.",
            mimeType="application/json"
        ),
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    if uri == "flashnode://vault/firmwares":
        return json.dumps(vault_manager.list_firmwares(), indent=2)
    elif uri == "flashnode://system/status":
        return json.dumps(await _get_system_data(), indent=2)
    elif uri == "flashnode://gpio/status":
        return json.dumps(power_rails.get_status(), indent=2)
    elif uri == "flashnode://history":
        return json.dumps(history_db.get_history(limit=50), indent=2)
    else:
        raise ValueError(f"Unknown resource: {uri}")


# ─────────────────────────────────────────────────
# MCP Tools — 17 tools
# ─────────────────────────────────────────────────
@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_connected_hardware",
            description="List all physically connected USB devices, active serial COM ports, debug probes, and the current state of power rails/GPIO. Includes gpio_backend field indicating 'mock' or 'libgpiod-v2'.",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="list_firmwares",
            description="Returns all firmwares currently stored in the Vault grouped by target (RP2040, ESP32).",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="upload_firmware",
            description="Upload a firmware file to the Vault from a local file path on the Rock 5C.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute path to the firmware file on the Rock 5C filesystem"},
                    "target": {"type": "string", "enum": ["RP2040", "ESP32"], "description": "Target MCU: 'RP2040' or 'ESP32'"}
                },
                "required": ["path", "target"]
            }
        ),
        types.Tool(
            name="delete_firmware",
            description="Permanently deletes a firmware file and its checksum sidecars from the Vault.",
            inputSchema={
                "type": "object",
                "properties": {
                    "firmware": {"type": "string", "description": "Firmware filename to delete"},
                    "target": {"type": "string", "enum": ["RP2040", "ESP32"], "description": "Target MCU vault to delete from"}
                },
                "required": ["firmware", "target"]
            }
        ),
        types.Tool(
            name="set_bootsel_mode_rp2040",
            description="Forces the RP2040 into BOOTSEL mode via GPIO manipulation (RESET low + BOOTSEL low, then release). Returns dry_run=true if running on mock GPIO.",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="set_download_mode_esp32",
            description="Forces the ESP32 into ROM Download mode via EN and GPIO0 manipulation. Returns dry_run=true if running on mock GPIO.",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="set_power_rail",
            description="Control a specific power rail (5V or 3.3V). Use this to turn on/off power to the target board.",
            inputSchema={
                "type": "object",
                "properties": {
                    "rail": {"type": "string", "enum": ["5v", "3v3"], "description": "Rail identifier: '5v' or '3v3'"},
                    "state": {"type": "string", "enum": ["on", "off"], "description": "'on' or 'off'"}
                },
                "required": ["rail", "state"]
            }
        ),
        types.Tool(
            name="power_cycle",
            description="Executes a complete power cycle of the target board (turns off 3.3V then 5V, waits, turns back on 5V then 3.3V).",
            inputSchema={
                "type": "object",
                "properties": {
                    "off_ms": {"type": "integer", "description": "Time to stay off in milliseconds (default: 1000)"}
                }
            }
        ),
        types.Tool(
            name="flash_rp2040",
            description="Flashes a firmware onto the RP2040 using picotool (USB) or OpenOCD (SWD via CMSIS-DAP probe). Pre-checks that the CLI tool is available.",
            inputSchema={
                "type": "object",
                "properties": {
                    "firmware": {"type": "string", "description": "Name of the firmware file in the vault (e.g., main.uf2)"},
                    "tool": {"type": "string", "enum": ["picotool", "openocd"], "description": "Flashing tool (default: picotool)"},
                    "interface": {"type": "string", "description": "For OpenOCD: 'usb' or 'swd' (default: usb)"}
                },
                "required": ["firmware"]
            }
        ),
        types.Tool(
            name="flash_esp32",
            description="Flashes a firmware onto the ESP32 via esptool over a serial port. Pre-checks that esptool.py is available.",
            inputSchema={
                "type": "object",
                "properties": {
                    "firmware": {"type": "string", "description": "Name of the firmware file in the vault"},
                    "port": {"type": "string", "description": "Serial port (e.g. /dev/ttyUSB0 or COM5)"},
                    "baud": {"type": "integer", "description": "Baudrate (default: 921600)"},
                    "chip": {"type": "string", "description": "ESP chip type (default: esp32)"},
                    "flash_address": {"type": "string", "description": "Flash address offset (default: 0x1000)"}
                },
                "required": ["firmware", "port"]
            }
        ),
        types.Tool(
            name="run_pipeline",
            description="Runs a pre-defined multi-step pipeline by name. Pipelines can flash multiple targets, control GPIO, and validate boot output.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Pipeline ID (e.g. 'Prod_Board_V1_Full_Deploy')"}
                },
                "required": ["name"]
            }
        ),
        types.Tool(
            name="reload_pipelines",
            description="Reloads the pipeline definitions from config/pipelines.json without restarting the server. Use this after editing pipelines at runtime.",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="stream_serial_logs",
            description="Opens a serial port and reads data for a specified duration. Returns the captured text output.",
            inputSchema={
                "type": "object",
                "properties": {
                    "port": {"type": "string", "description": "Serial port path (e.g., /dev/ttyUSB0 or COM5)"},
                    "duration_s": {"type": "integer", "description": "How many seconds to listen (default: 5, max: 30)"},
                    "baudrate": {"type": "integer", "description": "Baudrate (default: 115200)"}
                },
                "required": ["port"]
            }
        ),
        types.Tool(
            name="get_flash_status",
            description="Returns the current status of any ongoing flash operation, including real-time progress percentage and step details.",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="get_pipeline_status",
            description="Returns the real-time status of the last/current pipeline execution, including current step, total steps, and success/failure state.",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="get_system_status",
            description="Gets the Rock 5C host system stats: CPU usage, RAM usage, temperature, disk usage.",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="verify_firmware_integrity",
            description="Verifies the MD5 and SHA256 checksums of a firmware file in the vault by recalculating and comparing.",
            inputSchema={
                "type": "object",
                "properties": {
                    "firmware": {"type": "string", "description": "Firmware filename"},
                    "target": {"type": "string", "enum": ["RP2040", "ESP32"], "description": "Target MCU"}
                },
                "required": ["firmware", "target"]
            }
        ),
    ]


# ─────────────────────────────────────────────────
# Helper: system data
# ─────────────────────────────────────────────────
async def _get_system_data() -> dict:
    temp = None
    try:
        thermal_path = "/sys/class/thermal/thermal_zone0/temp"
        if os.path.exists(thermal_path):
            with open(thermal_path) as f:
                temp = round(int(f.read().strip()) / 1000.0, 1)
    except Exception:
        pass

    mem = psutil.virtual_memory()
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_used_mb": round(mem.used / (1024 * 1024)),
        "memory_total_mb": round(mem.total / (1024 * 1024)),
        "memory_percent": mem.percent,
        "temperature_c": temp,
        "disk_usage_percent": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent,
    }


# ─────────────────────────────────────────────────
# Helper: serial read (runs in thread to avoid blocking)
# ─────────────────────────────────────────────────
def _read_serial_sync(port: str, duration_s: int, baudrate: int) -> str:
    import serial
    ser = serial.Serial(port, baudrate=baudrate, timeout=1)
    output = ""
    start = _time.time()
    while (_time.time() - start) < duration_s:
        data = ser.read(ser.in_waiting or 1)
        if data:
            output += data.decode('utf-8', errors='replace')
    ser.close()
    return output


# ─────────────────────────────────────────────────
# Tool Handlers
# ─────────────────────────────────────────────────
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    logger.info(f"MCP Tool called: {name} | args: {arguments}")

    try:
        # ── Hardware Discovery ──
        if name == "get_connected_hardware":
            gpio_backend = get_gpio_backend()
            result = {
                "usb": device_scanner.scan_usb_devices(),
                "serial": device_scanner.scan_serial_ports(),
                "probes": device_scanner.scan_debug_probes(),
                "power_rails": power_rails.get_status(),
                "gpio_backend": getattr(gpio_backend, 'backend_name', 'unknown'),
                "gpio_is_mock": getattr(gpio_backend, 'is_mock', True),
            }
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        # ── Firmware Vault ──
        elif name == "list_firmwares":
            result = vault_manager.list_firmwares()
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "upload_firmware":
            path = arguments["path"]
            target = arguments["target"].upper()

            if not os.path.exists(path):
                return [types.TextContent(type="text", text=f"Error: File not found at {path}")]

            # Validate file extension
            valid_ext = ('.bin', '.uf2', '.elf', '.hex')
            if not path.lower().endswith(valid_ext):
                return [types.TextContent(type="text", text=f"Error: Invalid firmware file type. Accepted: {', '.join(valid_ext)}")]

            filename = os.path.basename(path)
            with open(path, "rb") as f:
                content = f.read()

            checksums = vault_manager.save_firmware(target, filename, content)
            size_kb = round(len(content) / 1024, 1)
            return [types.TextContent(type="text", text=f"Uploaded {filename} ({size_kb} KB) to {target} vault.\nMD5: {checksums['md5']}\nSHA256: {checksums['sha256']}")]

        elif name == "verify_firmware_integrity":
            fw_name = arguments["firmware"]
            target = arguments.get("target", "RP2040").upper()

            checksums = vault_manager.get_checksums(target, fw_name)
            if not checksums:
                return [types.TextContent(type="text", text=f"Error: Firmware {fw_name} not found in {target} vault.")]

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
                "integrity": "OK" if (md5_ok and sha256_ok) else "MISMATCH - file may be corrupted"
            }
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "delete_firmware":
            fw_name = arguments["firmware"]
            target = arguments["target"].upper()
            success = vault_manager.delete_firmware(target, fw_name)
            if success:
                return [types.TextContent(type="text", text=f"Deleted {fw_name} from {target} vault.")]
            else:
                return [types.TextContent(type="text", text=f"Error: Could not delete {fw_name} from {target} vault. File may not exist.")]

        # ── GPIO Control ──
        elif name == "set_bootsel_mode_rp2040":
            res = await sequence_runner.run_sequence("rp2040_bootsel")
            status = "Success - device should appear as USB mass storage" if res["success"] else f"Failed: {res.get('error', 'unknown error')}"
            return [types.TextContent(type="text", text=json.dumps({"status": status, "dry_run": res["dry_run"], "steps_executed": res["steps_executed"]}, indent=2))]

        elif name == "set_download_mode_esp32":
            res = await sequence_runner.run_sequence("esp32_download")
            status = "Success - ready for esptool flash" if res["success"] else f"Failed: {res.get('error', 'unknown error')}"
            return [types.TextContent(type="text", text=json.dumps({"status": status, "dry_run": res["dry_run"], "steps_executed": res["steps_executed"]}, indent=2))]

        elif name == "set_power_rail":
            rail = arguments["rail"].lower()
            state = arguments["state"].lower()

            if rail not in ("5v", "3v3"):
                return [types.TextContent(type="text", text=f"Error: Unknown rail '{rail}'. Use '5v' or '3v3'.")]

            is_on = state == "on"
            await power_rails.set_rail_async(rail, is_on)
            return [types.TextContent(type="text", text=f"Rail {rail.upper()} -> {'ON' if is_on else 'OFF'}")]

        elif name == "power_cycle":
            off_ms = arguments.get("off_ms", 1000)
            await power_rails.power_cycle_async(off_duration_ms=off_ms)
            return [types.TextContent(type="text", text=f"Power cycled successfully (off for {off_ms}ms). Both 5V and 3.3V rails are now ON.")]

        # ── Flash Operations ──
        elif name == "flash_rp2040":
            fw_name = arguments["firmware"]
            tool = arguments.get("tool", "picotool")

            fw_path = vault_manager.get_firmware_path("RP2040", fw_name)
            if not fw_path:
                return [types.TextContent(type="text", text=f"Error: Firmware '{fw_name}' not found in RP2040 vault. Use list_firmwares() to see available files.")]

            # Pre-check CLI tool availability
            from core.flasher.base import BaseFlasher
            cli_name = "openocd" if tool == "openocd" else "picotool"
            if not BaseFlasher.check_tool_available(cli_name):
                return [types.TextContent(type="text", text=f"Error: '{cli_name}' not found on PATH. Install it on the Rock 5C before flashing.")]

            # Update flash state + wire progress callback
            _flash_state.update({"status": "running", "tool": tool, "target": "RP2040", "firmware": fw_name, "progress": 0, "step": "", "started_at": _time.time(), "error": None})

            async def _on_progress_rp2040(pct: int, step: str):
                _flash_state["progress"] = pct
                _flash_state["step"] = step

            try:
                if tool == "openocd":
                    from core.flasher.openocd_runner import OpenOCDRunner
                    runner = OpenOCDRunner(on_progress=_on_progress_rp2040)
                else:
                    from core.flasher.picotool_runner import PicotoolRunner
                    runner = PicotoolRunner(on_progress=_on_progress_rp2040)

                success = await runner.flash(fw_path)
                _flash_state["status"] = "success" if success else "failed"
                _flash_state["progress"] = 100 if success else _flash_state["progress"]
                _flash_state["finished_at"] = _time.time()
                duration = round(_flash_state["finished_at"] - _flash_state["started_at"], 1)
                result_str = "Success" if success else "Failed"
                return [types.TextContent(type="text", text=f"Flash RP2040 ({tool}): {result_str} ({duration}s)")]
            except Exception as e:
                _flash_state.update({"status": "failed", "error": str(e), "finished_at": _time.time()})
                raise

        elif name == "flash_esp32":
            fw_name = arguments["firmware"]
            port = arguments["port"]
            baud = arguments.get("baud", 921600)
            chip = arguments.get("chip", "esp32")
            flash_address = arguments.get("flash_address", "0x1000")

            fw_path = vault_manager.get_firmware_path("ESP32", fw_name)
            if not fw_path:
                return [types.TextContent(type="text", text=f"Error: Firmware '{fw_name}' not found in ESP32 vault. Use list_firmwares() to see available files.")]

            # Pre-check CLI tool availability
            from core.flasher.base import BaseFlasher
            if not BaseFlasher.check_tool_available("esptool.py") and not BaseFlasher.check_tool_available("esptool"):
                return [types.TextContent(type="text", text="Error: 'esptool.py' not found on PATH. Install it with: pip install esptool")]

            _flash_state.update({"status": "running", "tool": "esptool", "target": "ESP32", "firmware": fw_name, "progress": 0, "step": "", "started_at": _time.time(), "error": None})

            async def _on_progress_esp32(pct: int, step: str):
                _flash_state["progress"] = pct
                _flash_state["step"] = step

            try:
                from core.flasher.esptool_runner import EspToolRunner
                runner = EspToolRunner(on_progress=_on_progress_esp32)
                success = await runner.flash(fw_path, port, baud, chip, flash_address)
                _flash_state["status"] = "success" if success else "failed"
                _flash_state["progress"] = 100 if success else _flash_state["progress"]
                _flash_state["finished_at"] = _time.time()
                duration = round(_flash_state["finished_at"] - _flash_state["started_at"], 1)
                result_str = "Success" if success else "Failed"
                return [types.TextContent(type="text", text=f"Flash ESP32 ({port}): {result_str} ({duration}s)")]
            except Exception as e:
                _flash_state.update({"status": "failed", "error": str(e), "finished_at": _time.time()})
                raise

        # ── Pipeline ──
        elif name == "run_pipeline":
            pipeline_name = arguments["name"]
            pipelines = _load_pipelines()

            pipeline_def = next((p for p in pipelines if p["id"] == pipeline_name), None)
            if not pipeline_def:
                available = [p["id"] for p in pipelines]
                return [types.TextContent(type="text", text=f"Error: Pipeline '{pipeline_name}' not found.\nAvailable pipelines: {', '.join(available) or 'none'}")]

            # Set up state tracking
            _pipeline_state.update({
                "status": "running", "pipeline_id": pipeline_name,
                "current_step": 0, "total_steps": len(pipeline_def.get("steps", [])),
                "started_at": _time.time(), "finished_at": None, "error": None,
            })

            # Wire up progress callback
            pipeline_engine.on_step_progress = _pipeline_progress_callback
            success = await pipeline_engine.run_pipeline(pipeline_def)
            _pipeline_state["finished_at"] = _time.time()
            duration = round(_pipeline_state["finished_at"] - _pipeline_state["started_at"], 1)

            result_str = "Completed successfully" if success else f"Failed at step {_pipeline_state['current_step']}"
            return [types.TextContent(type="text", text=f"Pipeline '{pipeline_name}': {result_str} ({duration}s)")]

        elif name == "reload_pipelines":
            global _pipelines_cache
            _pipelines_cache = None
            reloaded = _load_pipelines()
            return [types.TextContent(type="text", text=f"Pipelines reloaded. Found {len(reloaded)} pipeline(s): {', '.join(p['id'] for p in reloaded) or 'none'}")]

        # ── Serial Monitoring ──
        elif name == "stream_serial_logs":
            port = arguments["port"]
            duration_s = min(arguments.get("duration_s", 5), 30)  # Cap at 30s
            baudrate = arguments.get("baudrate", 115200)

            try:
                output = await asyncio.to_thread(_read_serial_sync, port, duration_s, baudrate)
                line_count = output.count('\n')
                return [types.TextContent(type="text", text=f"Serial output from {port} @ {baudrate}baud ({duration_s}s, {line_count} lines):\n\n{output}")]
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error reading serial port {port}: {str(e)}")]

        # ── Status Queries ──
        elif name == "get_flash_status":
            result = {
                "status": _flash_state["status"],
                "tool": _flash_state["tool"],
                "target": _flash_state["target"],
                "firmware": _flash_state["firmware"],
                "progress": _flash_state["progress"],
                "step": _flash_state["step"],
            }
            if _flash_state["started_at"]:
                elapsed = (_flash_state["finished_at"] or _time.time()) - _flash_state["started_at"]
                result["elapsed_s"] = round(elapsed, 1)
            if _flash_state["error"]:
                result["error"] = _flash_state["error"]
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_pipeline_status":
            result = {
                "status": _pipeline_state["status"],
                "pipeline_id": _pipeline_state["pipeline_id"],
                "current_step": _pipeline_state["current_step"],
                "total_steps": _pipeline_state["total_steps"],
            }
            if _pipeline_state["started_at"]:
                elapsed = (_pipeline_state["finished_at"] or _time.time()) - _pipeline_state["started_at"]
                result["elapsed_s"] = round(elapsed, 1)
            if _pipeline_state["step_details"]:
                result["current_step_details"] = _pipeline_state["step_details"]
            if _pipeline_state["error"]:
                result["error"] = _pipeline_state["error"]
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_system_status":
            result = await _get_system_data()
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}. Use list_tools() to see available tools.")]

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error executing {name}: {str(e)}")]


# ─────────────────────────────────────────────────
# Server Entry Points
# ─────────────────────────────────────────────────
async def run_stdio():
    """Run MCP server with stdio transport (for Claude Desktop local)."""
    logger.info("Starting MCP server in STDIO mode")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


async def run_sse(host: str = "0.0.0.0", port: int = 8001):
    """Run MCP server with SSE transport (for remote network access)."""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    import uvicorn

    sse = SseServerTransport("/messages/")

    async def handle_sse(scope, receive, send):
        async with sse.connect_sse(
            scope, receive, send
        ) as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())

    starlette_app = Starlette(
        debug=False,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

    logger.info(f"Starting MCP server in SSE mode on {host}:{port}")
    config = uvicorn.Config(starlette_app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    try:
        if "--sse" in sys.argv:
            host = os.environ.get("MCP_HOST", "0.0.0.0")
            port = int(os.environ.get("MCP_PORT", "8001"))
            asyncio.run(run_sse(host, port))
        else:
            asyncio.run(run_stdio())
    except Exception as e:
        import traceback
        try:
            with open("mcp_crash.log", "w") as f:
                f.write(f"Crash at {_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(traceback.format_exc())
        except:
            pass
        logger.error(f"MCP server crashed: {e}", exc_info=True)
        sys.exit(1)
