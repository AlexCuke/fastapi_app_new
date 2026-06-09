# app/routers/config.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import asyncpg
from typing import Optional

from app.db import get_db
from app.config import settings
from app.schemas.settings import AppSettingsUpdate
import app.db_ops as db_ops

router = APIRouter(prefix="/config", tags=["Configuration"])


class ConfigUpdate(BaseModel):
    value: str
    group_name: Optional[str] = None


class SortHeaderUpdate(BaseModel):
    filename: str
    header: str
    name: str


@router.get("")
async def get_config(conn: asyncpg.Connection = Depends(get_db)):
    return await db_ops.load_config(conn)


@router.get("/items")
async def get_config_items(conn: asyncpg.Connection = Depends(get_db)):
    return await db_ops.load_config_items(conn)


@router.put("/{key}")
async def set_config(
    key: str,
    value: Optional[str] = None,
    payload: Optional[ConfigUpdate] = None,
    conn: asyncpg.Connection = Depends(get_db)
):
    if payload is not None:
        new_value = payload.value
        group_name = payload.group_name
    elif value is not None:
        new_value = value
        group_name = None
    else:
        raise HTTPException(status_code=400, detail="Missing value for config update")

    await db_ops.update_config_value(conn, key, new_value, group_name)

    # Если обновили assignmentCompositionUid — синхронизируем current_assignment
    if key == 'assignmentCompositionUid':
        await db_ops.sync_current_assignment(conn)
        await db_ops.refresh_status_tracker(conn, "Смена assignmentCompositionUid через API")

    return {"key": key, "value": new_value, "group_name": group_name}


@router.delete("/{key}")
async def delete_config(key: str, conn: asyncpg.Connection = Depends(get_db)):
    result = await conn.execute("DELETE FROM config WHERE key = $1", key)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
    return {"key": key, "deleted": True}


@router.get("/sort-headers")
async def get_sort_headers(conn: asyncpg.Connection = Depends(get_db)):
    """Возвращает все заголовки из config_headers."""
    return await db_ops.get_sort_headers(conn)


@router.post("/sort-headers")
async def save_sort_header(update: SortHeaderUpdate, conn: asyncpg.Connection = Depends(get_db)):
    await db_ops.update_sort_header_name(conn, update.filename, update.header, update.name)
    return {"message": "Sort header name saved"}


@router.delete("/sort-headers/{filename}/{header}")
async def delete_sort_header(filename: str, header: str, conn: asyncpg.Connection = Depends(get_db)):
    result = await conn.execute(
        "DELETE FROM config_headers WHERE filename = $1 AND header = $2",
        filename, header
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return {"filename": filename, "header": header, "deleted": True}


@router.get("/status-tracker")
async def get_status_tracker(conn: asyncpg.Connection = Depends(get_db)):
    """Извлекает переходы статусов для всех процедур из таблицы current_assignment."""
    config = await db_ops.load_config(conn)
    assignment_uid = config.get('assignmentCompositionUid', '—')

    await db_ops.sync_current_assignment(conn)
    await db_ops.refresh_status_tracker(conn, "Ручное/Системное обновление")

    curr_exists = await db_ops.table_exists(conn, 'current_assignment')
    procedures_list = []
    last_updated = "—"
    trigger_command = "—"
    current_assignment_status = "—"
    previous_assignment_status = "—"

    if curr_exists:
        col_proc_code = await db_ops.guess_column(
            conn, 'current_assignment',
            ['procedureAssignment.procedureCode', 'procedureCode'],
            'procedureAssignment.procedureCode'
        )
        col_proc_status = await db_ops.guess_column(
            conn, 'current_assignment',
            ['procedureAssignment.status', 'status'],
            'procedureAssignment.status'
        )
        col_assign_status = await db_ops.guess_column(
            conn, 'current_assignment',
            ['procedureAssignment.assignmentStatus', 'assignmentStatus'],
            'procedureAssignment.assignmentStatus'
        )
        col_updated = await db_ops.guess_column(
            conn, 'current_assignment',
            ['procedureAssignment.updated', 'updated'],
            'procedureAssignment.updated'
        )

        if col_proc_code and col_proc_status:
            rows = await conn.fetch(f"""
                SELECT DISTINCT "{col_proc_code}" as proc_code,
                                "{col_proc_status}" as proc_status,
                                "{col_assign_status}" as assign_status,
                                "{col_updated}" as updated_at
                FROM current_assignment
            """)
            if rows:
                current_assignment_status = rows[0]["assign_status"] or "—"
                last_updated = rows[0]["updated_at"] or "—"
                prev_row = await conn.fetchrow("""
                    SELECT assignment_status
                    FROM status_tracker
                    WHERE assignment_id = $1 AND assignment_status != $2
                    ORDER BY id DESC LIMIT 1
                """, config.get('assignmentId'), current_assignment_status)
                if prev_row:
                    previous_assignment_status = prev_row["assignment_status"]

                for r in rows:
                    code = r["proc_code"]
                    curr_status = r["proc_status"]
                    prev_status = "—"
                    prev_proc_row = await conn.fetchrow("""
                        SELECT procedure_status, trigger_command
                        FROM status_tracker
                        WHERE procedure_code = $1 AND procedure_status != $2
                        ORDER BY id DESC LIMIT 1
                    """, code, curr_status)
                    if prev_proc_row:
                        prev_status = prev_proc_row["procedure_status"]
                        trigger_command = prev_proc_row["trigger_command"]
                    procedures_list.append({
                        "code": code,
                        "current_status": curr_status,
                        "previous_status": prev_status
                    })

    if not procedures_list:
        procedures_list.append({
            "code": config.get('procedureCode', '—'),
            "current_status": "—",
            "previous_status": "—"
        })

    return {
        "assignment_id": config.get('assignmentId', '—'),
        "assignment_composition_uid": assignment_uid,
        "current_assignment_status": current_assignment_status,
        "previous_assignment_status": previous_assignment_status,
        "procedures": procedures_list,
        "last_updated": last_updated,
        "trigger_command": trigger_command
    }


@router.get("/app-settings")
async def get_app_settings():
    return {
        "TENANT_ID": settings.TENANT_ID,
        "USER_ID": settings.USER_ID,
        "BASE_URL": settings.BASE_URL,
        "REQUEST_TIMEOUT": settings.REQUEST_TIMEOUT,
        "ES_HOST": settings.ES_HOST,
        "INDEX_NAME": settings.INDEX_NAME,
        "SCROLL_SIZE": settings.SCROLL_SIZE,
        "REQUEST_TIMEOUT_ES": settings.REQUEST_TIMEOUT_ES,
        "OUTPUT_JSONL": settings.OUTPUT_JSONL,
        "OUTPUT_CSV": settings.OUTPUT_CSV,
        "DB_HOST": settings.DB_HOST,
        "DB_PORT": settings.DB_PORT,
        "DB_NAME": settings.DB_NAME,
        "DB_USER": settings.DB_USER,
        "DB_PASSWORD": settings.DB_PASSWORD,
    }


@router.post("/app-settings")
async def update_app_settings(new_settings: AppSettingsUpdate):
    for k, v in new_settings.model_dump(exclude_unset=True).items():
        setattr(settings, k, v)
    try:
        with open(".env", "w", encoding="utf-8") as f:
            for key in settings.model_fields.keys():
                val = getattr(settings, key)
                f.write(f"{key}={val}\n")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Не удалось перезаписать .env: {str(e)}")
    return {"message": "Настройки успешно сохранены."}