from fastapi import APIRouter, Depends, HTTPException
import asyncpg
from app.db import get_db
from app.config import settings
import app.db_ops as db_ops

router = APIRouter(prefix="/config", tags=["Configuration"])

@router.get("")
async def get_config(conn: asyncpg.Connection = Depends(get_db)):
    return await db_ops.load_config(conn)

@router.put("/{key}")
async def set_config(key: str, value: str, conn: asyncpg.Connection = Depends(get_db)):
    await db_ops.update_config_value(conn, key, value)
    return {"key": key, "value": value}

@router.post("/auto-update")
async def auto_update_config(data: dict, conn: asyncpg.Connection = Depends(get_db)):
    updates = {
        "assignmentCompositionUid": data.get("assignmentCompositionUid"),
        "assignmentId": data.get("id"),
        "ehrId": data.get("ehrId"),
        "patientId": data.get("patientId"),
        "careCaseId": data.get("careCaseId"),
        "workplaceId": data.get("workplaceId"),
        "doctorName": data.get("doctorName"),
        "doctorJob": data.get("doctorJob"),
        "assignmentName": data.get("assignmentName"),
        "assignmentCode": data.get("assignmentCode"),
    }
    procs = data.get("procedures", [])
    if procs:
        updates["procedureCode"] = procs[0].get("code")
        updates["code"] = procs[0].get("code")

    for k, v in updates.items():
        if v is not None:
            await db_ops.update_config_value(conn, k, str(v))
    return {"status": "success"}

@router.get("/app-settings")
async def get_app_settings():
    return {
        "TENANT_ID": settings.TENANT_ID,
        "USER_ID": settings.USER_ID,
        "BASE_URL": settings.BASE_URL,
        "ES_HOST": settings.ES_HOST,
        "INDEX_NAME": settings.INDEX_NAME,
    }

@router.post("/app-settings")
async def update_app_settings(new_settings: dict):
    for k, v in new_settings.items():
        if hasattr(settings, k):
            setattr(settings, k, str(v))
    try:
        with open(".env", "w", encoding="utf-8") as f:
            for key in settings.model_fields.keys():
                f.write(f"{key}={getattr(settings, key)}\n")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": "settings updated"}

@router.get("/status-tracker")
async def get_status_tracker(conn: asyncpg.Connection = Depends(get_db)):
    cfg = await db_ops.load_config(conn)
    return {"assignment_id": cfg.get('assignmentId', '—'), "procedures": []}