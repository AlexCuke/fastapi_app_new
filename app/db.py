import asyncpg
from typing import AsyncGenerator
from app.config import settings

class DatabaseSessionManager:
    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            min_size=5,
            max_size=20
        )

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

db_manager = DatabaseSessionManager()

async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    if not db_manager.pool:
        raise RuntimeError("Database pool is not initialized")
    async with db_manager.pool.acquire() as connection:
        yield connection