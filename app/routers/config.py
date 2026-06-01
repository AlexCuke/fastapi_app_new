from fastapi import APIRouter, Depends, HTTPException
import asyncpg
from app.db import get_db
import app.db_ops as db_ops

router = APIRouter(prefix="/config", tags=["Configuration"])

@router.get("")
async def get_config(conn: asyncpg.Connection = Depends(get_db)):
    return await db_ops.load_config(conn)

@router.put("/{key}")
async def set_config(key: str, value: str, conn: asyncpg.Connection = Depends(get_db)):
    await db_ops.update_config_value(conn, key, value)
    return {"key": key, "value": value}

@router.get("/status-tracker")
async def get_status_tracker(conn: asyncpg.Connection = Depends(get_db)):
    """Извлекает 2 последние записи истории изменений, чтобы показать текущий и предпоследний статусы."""
    config = await db_ops.load_config(conn)
    assignment_id = config.get('assignmentId', '—')
    procedure_code = config.get('procedureCode', '—')

    # Принудительная фоновая синхронизация с сырыми данными перед отдачей результата
    await db_ops.refresh_status_tracker(conn, "Ручное/Системное обновление")

    # Вытаскиваем две последние записи истории
    rows = await conn.fetch("""
        SELECT assignment_status, procedure_status, trigger_command, last_updated
        FROM status_tracker
        WHERE assignment_id = $1 AND procedure_code = $2
        ORDER BY id DESC LIMIT 2
    """, assignment_id, procedure_code)

    result = {
        "assignment_id": assignment_id,
        "current_assignment_status": "—",
        "previous_assignment_status": "—",
        "procedure_code": procedure_code,
        "current_procedure_status": "—",
        "previous_procedure_status": "—",
        "last_updated": "—",
        "trigger_command": "—"
    }

    # rows[0] — это последняя по времени запись (Текущий статус)
    if len(rows) >= 1:
        result["current_assignment_status"] = rows[0]["assignment_status"] or "—"
        result["current_procedure_status"] = rows[0]["procedure_status"] or "—"
        result["last_updated"] = rows[0]["last_updated"] or "—"
        result["trigger_command"] = rows[0]["trigger_command"] or "—"

    # rows[1] — это предпоследняя запись истории (Предпоследний статус)
    if len(rows) == 2:
        result["previous_assignment_status"] = rows[1]["assignment_status"] or "—"
        result["previous_procedure_status"] = rows[1]["procedure_status"] or "—"

    return result