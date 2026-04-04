from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List

from core.pipeline_engine import pipeline_engine

router = APIRouter(prefix="/pipeline", tags=["Pipelines"])

# Mock state
active_pipelines = {}

@router.post("/start")
async def start_pipeline(pipeline_def: Dict[str, Any], background_tasks: BackgroundTasks):
    """Starts a pipeline execution in the background"""
    name = pipeline_def.get("pipeline_name", "Unknown")
    
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
