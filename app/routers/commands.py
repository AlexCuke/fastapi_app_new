from fastapi import APIRouter, Depends, HTTPException
import asyncpg
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ValidationError
from app.db import get_db
from app.models import ExecuteRequest, ExecuteResponse, get_command_model, validate_command_payload
from app.api_client import substitute_markers, send_request_async
from app.config import settings
import app.db_ops as db_ops

router = APIRouter(tags=["Integration Commands"])

class TemplateUpdate(BaseModel):
    name: str
    method: str
    path: str
    payload: Any
    group_name: Optional[str] = 'default'

# Список команд
@router.get("/commands")
async def list_commands(conn: asyncpg.Connection = Depends(get_db)):
    records = await db_ops.get_all_templates_db(conn)
    return {
        "commands": [
            {
                "name": r['name'],
                "group_name": r.get('group_name', 'default')
            }
            for r in records
        ]
    }

@router.get("/commands/templates")
async def list_templates(conn: asyncpg.Connection = Depends(get_db)):
    records = await db_ops.get_all_templates_db(conn)
    return {
        "templates": [
            {
                "id": r['id'],
                "name": r['name'],
                "method": r['method'],
                "path": r['path'],
                "payload": r['payload'],
                "group_name": r.get('group_name', 'default')
            }
            for r in records
        ]
    }

@router.put("/template/{template_id:int}")
async def update_template(template_id: int, payload: TemplateUpdate, conn: asyncpg.Connection = Depends(get_db)):
    record = await db_ops.get_template_by_id_db(conn, template_id)
    if not record:
        raise HTTPException(status_code=404, detail="Template not found")

    template_payload = payload.payload
    if isinstance(template_payload, str):
        try:
            template_payload = json.loads(template_payload)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Payload должен быть корректным JSON-объектом")

    if not isinstance(template_payload, dict):
        raise HTTPException(status_code=400, detail="Payload должен быть JSON-объектом")

    await db_ops.update_template_db(
        conn,
        template_id,
        payload.name,
        payload.method,
        payload.path,
        template_payload,
        payload.group_name or 'default'
    )
    return {"updated": True, "template_id": template_id}

@router.get("/template/{command_name}")
async def get_template(command_name: str, conn: asyncpg.Connection = Depends(get_db)):
    record = await db_ops.get_template_by_name_db(conn, command_name)
    if not record:
        raise HTTPException(status_code=404, detail="Template not found")
    model_cls = get_command_model(command_name)
    schema = model_cls.model_json_schema() if model_cls else None
    return {"template": json.loads(record['payload']), "schema": schema}

@router.get("/schema/{command_name}")
async def get_command_schema(command_name: str, conn: asyncpg.Connection = Depends(get_db)):
    """JSON Schema swagger-модели для команды (если сопоставлена)."""
    record = await db_ops.get_template_by_name_db(conn, command_name)
    if not record:
        raise HTTPException(status_code=404, detail="Template not found")
    model_cls = get_command_model(command_name)
    if not model_cls:
        raise HTTPException(status_code=404, detail="Schema not mapped for this command")
    return model_cls.model_json_schema()

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

    try:
        resolved_payload = validate_command_payload(req.command_name, resolved_payload)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    url = settings.BASE_URL + record['path']
    status, data, err = await send_request_async(record['method'], url, resolved_payload, req.tenant_id, req.user_id)
    
    # --- ИСПРАВЛЕНИЕ: обновляем config на основе успешного ответа ---
    if status in (200, 201):
        # 1. Обновляем assignmentCompositionUid (поддерживаем оба варианта ключа)
        uid = resolved_payload.get('assignmentCompositionUid') or resolved_payload.get('compositionUid')
        if uid:
            await db_ops.update_config_value(conn, 'assignmentCompositionUid', uid, 'default')
        
        # 2. Обновляем часто используемые параметры, если они присутствуют в payload
        for key in ('code', 'workplaceId', 'doctorName', 'doctorJob'):
            if key in resolved_payload:
                await db_ops.update_config_value(conn, key, resolved_payload[key], 'default')
        
        # 3. Дополнительно: если есть resultCompositionUid, можно тоже сохранить
        if 'resultCompositionUid' in resolved_payload:
            await db_ops.update_config_value(conn, 'resultCompositionUid', resolved_payload['resultCompositionUid'], 'default')
        
        # 4. Пересоздаём таблицу current_assignment на основе нового UID
        await db_ops.sync_current_assignment(conn)
        # 5. Фиксируем переходы статусов в трекере
        await db_ops.refresh_status_tracker(conn, trigger_command=req.command_name)

    return ExecuteResponse(
        status_code=status, 
        response=data, 
        request_payload=resolved_payload,
        error=err
    )