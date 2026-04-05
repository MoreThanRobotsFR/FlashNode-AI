from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from core.pipeline_engine import pipeline_engine
from ws.connection_manager import manager
import json
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["Pipelines"])

# Active pipeline tracking
active_pipelines = {}
_cancel_flags = {}

PIPELINES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "config"
)
PIPELINES_FILE = os.path.join(PIPELINES_DIR, "pipelines.json")


def _load_all_pipelines() -> List[dict]:
    try:
        with open(PIPELINES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("pipelines", [])
    except Exception:
        return []


def _save_all_pipelines(pipelines: List[dict]):
    os.makedirs(os.path.dirname(PIPELINES_FILE), exist_ok=True)
    with open(PIPELINES_FILE, "w", encoding="utf-8") as f:
        json.dump({"pipelines": pipelines}, f, indent=2, ensure_ascii=False)


async def emit_progress(pipeline_id: str, step_idx: int, total_steps: int, status: str, step_details: dict = None):
    payload = {
        "type": "pipeline_progress",
        "pipeline_id": pipeline_id,
        "step_idx": step_idx,
        "total_steps": total_steps,
        "status": status,
        "step_details": step_details or {}
    }
    logger.info(f"[WS BROADCAST] pipeline_status -> {payload}. Manager ID: {id(manager)}")
    await manager.broadcast(payload, channel="pipeline_status")

pipeline_engine.on_step_progress = emit_progress


# ---- Models ----
class PipelineStartRequest(BaseModel):
    pipeline_name: str

class PipelineCreateRequest(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    on_error: Optional[str] = "stop"
    steps: List[dict]


# ---- Endpoints ----
@router.get("/list")
def list_pipelines():
    """Lists all saved pipelines"""
    return _load_all_pipelines()


@router.get("/{name}")
def get_pipeline(name: str):
    """Returns the full JSON definition of a pipeline"""
    pipelines = _load_all_pipelines()
    pipeline = next((p for p in pipelines if p["id"] == name), None)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline


@router.post("/create")
def create_pipeline(request: PipelineCreateRequest):
    """Creates or updates a pipeline definition"""
    pipelines = _load_all_pipelines()
    
    # Check if pipeline with same ID already exists — update it
    existing_idx = next((i for i, p in enumerate(pipelines) if p["id"] == request.id), None)
    
    pipeline_dict = {
        "id": request.id,
        "name": request.name,
        "description": request.description,
        "on_error": request.on_error,
        "steps": request.steps
    }
    
    if existing_idx is not None:
        pipelines[existing_idx] = pipeline_dict
        action = "updated"
    else:
        pipelines.append(pipeline_dict)
        action = "created"
    
    _save_all_pipelines(pipelines)
    return {"status": "success", "action": action, "pipeline_id": request.id}


@router.post("/start")
async def start_pipeline(request: PipelineStartRequest, background_tasks: BackgroundTasks):
    """Starts a pipeline execution in the background"""
    name = request.pipeline_name
    
    pipelines = _load_all_pipelines()
    pipeline_def = next((p for p in pipelines if p["id"] == name), None)
    
    if not pipeline_def:
        raise HTTPException(status_code=404, detail="Pipeline definition not found")
    
    if name in active_pipelines and active_pipelines[name] == "running":
        raise HTTPException(status_code=400, detail="Pipeline already running")
        
    active_pipelines[name] = "running"
    _cancel_flags[name] = False
    
    async def run_in_bg():
        try:
            success = await pipeline_engine.run_pipeline(pipeline_def, cancel_check=lambda: _cancel_flags.get(name, False))
            if _cancel_flags.get(name):
                active_pipelines[name] = "stopped"
            else:
                active_pipelines[name] = "success" if success else "failed"
        except Exception as e:
            logger.error(f"Pipeline {name} error: {e}")
            active_pipelines[name] = "error"
            
    background_tasks.add_task(run_in_bg)
    return {"status": "started", "pipeline": name}


@router.post("/stop")
async def stop_pipeline():
    """Stops any currently running pipeline"""
    stopped = []
    for name, status in active_pipelines.items():
        if status == "running":
            _cancel_flags[name] = True
            stopped.append(name)
    
    if not stopped:
        raise HTTPException(status_code=404, detail="No running pipeline to stop")
    
    return {"status": "stopping", "pipelines": stopped}


@router.get("/status/{name}")
def get_status(name: str):
    """Returns the status of a specific pipeline"""
    return {"pipeline": name, "status": active_pipelines.get(name, "not_found")}


@router.delete("/{name}")
def delete_pipeline(name: str):
    """Deletes a pipeline definition"""
    if name in active_pipelines and active_pipelines[name] == "running":
        raise HTTPException(status_code=400, detail="Cannot delete a running pipeline")
    
    pipelines = _load_all_pipelines()
    new_pipelines = [p for p in pipelines if p["id"] != name]
    
    if len(new_pipelines) == len(pipelines):
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    _save_all_pipelines(new_pipelines)
    
    # Clean up active state
    active_pipelines.pop(name, None)
    _cancel_flags.pop(name, None)
    
    return {"status": "deleted", "pipeline": name}
