import httpx
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from app.config import settings

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace("+00:00", "Z")

def resolve_value(v: Any, config: Dict[str, str]) -> Any:
    if isinstance(v, str):
        if v.startswith('@config:'):
            key = v[8:]
            return config.get(key, f"<MISSING:{key}>")
        elif v == '@now_iso':
            return now_iso()
    elif isinstance(v, dict):
        return {k: resolve_value(val, config) for k, val in v.items()}
    elif isinstance(v, list):
        return [resolve_value(item, config) for item in v]
    return v

def substitute_markers(payload: Dict[str, Any], config: Dict[str, str]) -> Dict[str, Any]:
    return resolve_value(payload, config)

async def send_request_async(
    method: str, 
    url: str, 
    payload: Optional[Dict[str, Any]], 
    tenant_id: str, 
    user_id: str
) -> Tuple[int, Any, Optional[str]]:
    headers = {
        "Content-Type": "application/json", 
        "X-Tenant-Id": tenant_id, 
        "X-User-Id": user_id
    }
    async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
        try:
            if method.upper() == "GET":
                resp = await client.get(url, params=payload, headers=headers)
            else:
                resp = await client.post(url, json=payload, headers=headers)
            
            try:
                data = resp.json()
            except ValueError:
                data = resp.text
            return resp.status_code, data, None
        except Exception as e:
            return 0, None, str(e)
