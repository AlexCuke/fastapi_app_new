from typing import AsyncGenerator, Optional
import asyncpg
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class DatabaseSessionManager:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.pool2: Optional[asyncpg.Pool] = None

    async def connect(self):
        # Подключаем основную БД (обязательно)
        self.pool = await asyncpg.create_pool(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        logger.info(f"✅ Подключена основная БД {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

        # Пытаемся подключить вторую БД, но не падаем при ошибке
        try:
            self.pool2 = await asyncpg.create_pool(
                host=settings.DB2_HOST,
                port=settings.DB2_PORT,
                database=settings.DB2_NAME,
                user=settings.DB2_USER,
                password=settings.DB2_PASSWORD,
                min_size=1,
                max_size=5,
                command_timeout=10,
                timeout=10
            )
            logger.info(f"✅ Подключена вторая БД {settings.DB2_HOST}:{settings.DB2_PORT}/{settings.DB2_NAME}")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось подключить вторую БД: {e}. Продолжаем работу с основной БД.")
            self.pool2 = None

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
        if self.pool2:
            await self.pool2.close()

db_manager = DatabaseSessionManager()

async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    if not db_manager.pool:
        raise RuntimeError("Основной пул БД не инициализирован")
    async with db_manager.pool.acquire() as conn:
        yield conn

async def get_db2() -> AsyncGenerator[asyncpg.Connection, None]:
    if not db_manager.pool2:
        raise RuntimeError("Пул второй БД не инициализирован")
    async with db_manager.pool2.acquire() as conn:
        yield conn