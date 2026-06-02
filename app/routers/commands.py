from fastapi import APIRouter, Depends, HTTPException
import asyncpg
from app.db import get_db
import app.db_ops as db_ops

router = APIRouter(prefix="/commands", tags=["Commands"])

@router.get("")
async def list_commands(conn: asyncpg.Connection = Depends(get_db)):
    records = await db_ops.get_all_templates_db(conn)
    return {"commands": [r['name'] for r in records]}

@router.get("/template/{command_name}")
async def get_template(command_name: str, conn: asyncpg.Connection = Depends(get_db)):
    record = await db_ops.get_template_by_name_db(conn, command_name)
    if not record:
        raise HTTPException(status_code=404, detail="Template not found")
    import json
    return {"template": json.loads(record['payload'])}

@router.post("/reset-templates")
async def reset_templates(conn: asyncpg.Connection = Depends(get_db)):
    """Кнопка в интерфейсе вызывает этот метод"""
    try:
        await db_ops.reset_templates_table(conn)
        return {"message": "Таблица команд успешно восстановлена и обновлена!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))