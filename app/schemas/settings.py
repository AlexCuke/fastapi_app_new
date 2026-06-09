# app/schemas/settings.py
from pydantic import BaseModel
from typing import Optional


class AppSettingsUpdate(BaseModel):
    TENANT_ID: Optional[str] = None
    USER_ID: Optional[str] = None
    BASE_URL: Optional[str] = None
    REQUEST_TIMEOUT: Optional[int] = None
    ES_HOST: Optional[str] = None
    INDEX_NAME: Optional[str] = None
    SCROLL_SIZE: Optional[int] = None
    REQUEST_TIMEOUT_ES: Optional[int] = None
    OUTPUT_JSONL: Optional[str] = None
    OUTPUT_CSV: Optional[str] = None
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = None
    DB_NAME: Optional[str] = None
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = Noneы