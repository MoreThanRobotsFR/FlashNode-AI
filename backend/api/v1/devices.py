from fastapi import APIRouter
from core.device_scanner import device_scanner
from typing import Dict, List, Any

router = APIRouter(prefix="/devices", tags=["Devices"])

@router.get("/scan")
async def scan_all() -> Dict[str, Any]:
    """Scans all connected devices (USB and Serial)"""
    return {
        "usb": device_scanner.scan_usb_devices(),
        "serial": device_scanner.scan_serial_ports()
    }

@router.get("/serial")
async def list_serial_ports() -> List[Dict]:
    """Returns a list of available serial ports"""
    return device_scanner.scan_serial_ports()

@router.get("/probes")
async def list_probes() -> List[Dict]:
    """Returns a list of CMSIS-DAP debug probes (Raspberry Pi Debug Probe, etc.)"""
    return device_scanner.scan_debug_probes()

@router.get("/usb-tree")
async def list_usb_devices() -> List[Dict]:
    """Returns a list of connected USB devices (using pyudev/Linux)"""
    return device_scanner.scan_usb_devices()
