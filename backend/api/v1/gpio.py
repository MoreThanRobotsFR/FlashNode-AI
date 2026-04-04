from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from core.gpio.factory import get_gpio_backend
from core.gpio.power_rails import power_rails
from core.gpio.sequences import sequence_runner

router = APIRouter(prefix="/gpio", tags=["GPIO & Power"])
backend = get_gpio_backend()

@router.get("/status")
def get_status() -> Dict[str, Any]:
    return power_rails.get_status()

@router.post("/rail/{rail}/on")
def rail_on(rail: str):
    if rail.lower() == "5v":
        backend.set(power_rails.rail_5v_pin, 1)
    elif rail.lower() == "3v3":
        backend.set(power_rails.rail_3v3_pin, 1)
    else:
        raise HTTPException(status_code=400, detail="Invalid rail")
    return {"status": "ok"}

@router.post("/rail/{rail}/off")
def rail_off(rail: str):
    if rail.lower() == "5v":
        backend.set(power_rails.rail_5v_pin, 0)
    elif rail.lower() == "3v3":
        backend.set(power_rails.rail_3v3_pin, 0)
    else:
        raise HTTPException(status_code=400, detail="Invalid rail")
    return {"status": "ok"}

@router.post("/sequence/{seq_name}")
async def run_sequence(seq_name: str):
    if seq_name == "power_cycle":
        power_rails.power_cycle()
        return {"status": "ok"}
        
    success = await sequence_runner.run_sequence(seq_name)
    if not success:
        raise HTTPException(status_code=404, detail="Sequence not found")
    return {"status": "ok"}

class PinActionRequest(BaseModel):
    value: int = 1
    duration_ms: int = 100

@router.post("/pin/{pin_id}/set")
def set_pin(pin_id: str, payload: PinActionRequest):
    backend.set(pin_id, payload.value)
    return {"status": "ok"}

@router.post("/pin/{pin_id}/pulse")
def pulse_pin(pin_id: str, payload: PinActionRequest):
    backend.pulse(pin_id, payload.duration_ms)
    return {"status": "ok"}
