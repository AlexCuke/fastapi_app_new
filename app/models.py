from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional

class ExecuteRequest(BaseModel):
    command_name: str
    tenant_id: str
    user_id: str
    override_payload: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class ExecuteResponse(BaseModel):
    status_code: int
    response: Any
    request_payload: Optional[Any] = None  # Поле для отображения отправленного JSON
    error: Optional[str] = None

class ExportRequest(BaseModel):
    export_index_final: bool = True

class TemplateBase(BaseModel):
    name: str
    method: str
    path: str
    payload: Dict[str, Any]

class TemplateResponse(TemplateBase):
    id: int