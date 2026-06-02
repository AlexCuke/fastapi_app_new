from fastapi import APIRouter, Depends, HTTPException
import asyncpg
from typing import List, Dict, Any
from app.db import get_db
from app.models import ExecuteRequest, ExecuteResponse
from app.api_client import substitute_markers, send_request_async
from app.config import settings
import app.db_ops as db_ops

router = APIRouter(tags=["Integration Commands"])

@router.get("/commands", response_model=Dict[str, List[str]])
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

@router.post("/resolve")
async def resolve_markers(payload: dict, conn: asyncpg.Connection = Depends(get_db)):
    config = await db_ops.load_config(conn)
    resolved = substitute_markers(payload, config)
    return {"resolved": resolved}

@router.post("/execute", response_model=ExecuteResponse)
async def execute_command(req: ExecuteRequest, conn: asyncpg.Connection = Depends(get_db)):
    record = await db_ops.get_template_by_name_db(conn, req.command_name)
    if not record:
        raise HTTPException(status_code=404, detail="Command design schema templates not found")
    
    import json
    template_payload = json.loads(record['payload'])
    payload = req.override_payload if req.override_payload is not None else template_payload
    if payload is None:
        payload = {}

    config = await db_ops.load_config(conn)
    resolved_payload = substitute_markers(payload, config)

    def has_markers(obj):
        if isinstance(obj, str) and (obj.startswith('@config:') or obj == '@now_iso'):
            return True
        if isinstance(obj, dict):
            return any(has_markers(v) for v in obj.values())
        if isinstance(obj, list):
            return any(has_markers(i) for i in obj)
        return False

    if has_markers(resolved_payload):
        raise HTTPException(status_code=400, detail="Unresolved payload markers remain. Update settings config values.")

    # Если метод команды равен KAFKA, публикуем данные напрямую в брокер
    if record['method'].upper() == "KAFKA":
        from app.kafka_producer import kafka_manager
        try:
            topic = record['path'] or settings.KAFKA_TOPIC_NAME
            # Используем в качестве Partition Key идентификатор assignmentCompositionUid
            msg_key = resolved_payload.get("assignmentCompositionUid") or resolved_payload.get("assignmentId")
            
            await kafka_manager.send_message(topic, value=resolved_payload, key=msg_key)
            
            # Синхронизируем срезы данных и фиксируем статус
            await db_ops.sync_current_assignment(conn)
            await db_ops.refresh_status_tracker(conn, trigger_command=req.command_name)
            
            return ExecuteResponse(
                status_code=200,
                response={"message": f"Сообщение успешно опубликовано в топик Kafka '{topic}'", "partition_key": msg_key},
                request_payload=resolved_payload,
                error=None
            )
        except Exception as e:
            return ExecuteResponse(
                status_code=500,
                response=None,
                request_payload=resolved_payload,
                error=f"Ошибка паблишинга в Kafka: {str(e)}"
            )

    # Стандартные HTTP запросы
    url = settings.BASE_URL + record['path']
    status, data, err = await send_request_async(record['method'], url, resolved_payload, req.tenant_id, req.user_id)
    
    # Если команда успешно отработала на внешнем API, синхронизируем срез и фиксируем переходы
    if status in (200, 201):
        await db_ops.sync_current_assignment(conn)
        await db_ops.refresh_status_tracker(conn, trigger_command=req.command_name)

    return ExecuteResponse(
        status_code=status, 
        response=data, 
        request_payload=resolved_payload,
        error=err
    )