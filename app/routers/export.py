from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
import asyncpg
from app.db import get_db
from app.models import ExportRequest
from app.elastic_export import run_export, export_to_keys_job
import app.db_ops as db_ops

router = APIRouter(tags=["Elastic Export Processing"])

@router.post("/export")
async def export_elastic(background_tasks: BackgroundTasks, req: ExportRequest):
    background_tasks.add_task(run_export, export_index_final=req.export_index_final)
    return {"message": "Async migration batch runner task started successfully."}

@router.post("/export_to_keys")
async def export_to_keys_endpoint(background_tasks: BackgroundTasks):
    background_tasks.add_task(export_to_keys_job)
    return {"message": "Active synchronization workflow started successfully."}

@router.post("/create_keys")
async def create_keys(conn: asyncpg.Connection = Depends(get_db)):
    try:
        count = await db_ops.copy_index_to_keys(conn)
        return {"message": f"Table 'keys' generated, populated with {count} columns records."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
