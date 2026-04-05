from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List

from core.pipeline_engine import pipeline_engine
from ws.connection_manager import manager
import json
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["Pipelines"])

# Mock state
active_pipelines = {}

def load_pipelines():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    config_path = os.path.join(base_dir, "config", "pipelines.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("pipelines", [])
    except Exception:
        return []

async def emit_progress(step_idx: int, total_steps: int, status: str, step_details: dict = None):
    payload = {
        "type": "pipeline_progress",
        "step_idx": step_idx,
        "total_steps": total_steps,
        "status": status,
        "step_details": step_details or {}
    }
    logger.info(f"[WS BROADCAST] pipeline_status -> {payload}. Manager ID: {id(manager)}")
    await manager.broadcast(payload, channel="pipeline_status")

pipeline_engine.on_step_progress = emit_progress

@router.get("/list")
def list_pipelines():
    return load_pipelines()

class PipelineStartRequest(BaseModel):
    pipeline_name: str

@router.post("/start")
async def start_pipeline(request: PipelineStartRequest, background_tasks: BackgroundTasks):
    """Starts a pipeline execution in the background"""
    name = request.pipeline_name
    
    pipelines = load_pipelines()
    pipeline_def = next((p for p in pipelines if p["id"] == name), None)
    
    if not pipeline_def:
        raise HTTPException(status_code=404, detail="Pipeline definition not found")
    
    if name in active_pipelines and active_pipelines[name] == "running":
        raise HTTPException(status_code=400, detail="Pipeline already running")
        
    active_pipelines[name] = "running"
    
    # Run in background to not block the API response
    async def run_in_bg():
        try:
            success = await pipeline_engine.run_pipeline(pipeline_def)
            active_pipelines[name] = "success" if success else "failed"
        except Exception:
            active_pipelines[name] = "error"
            
    background_tasks.add_task(run_in_bg)
    return {"status": "started", "pipeline": name}

@router.get("/status/{name}")
def get_status(name: str):
    """Returns the status of a specific pipeline"""
    return {"pipeline": name, "status": active_pipelines.get(name, "not_found")}
