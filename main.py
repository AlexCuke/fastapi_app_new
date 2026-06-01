from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from app.db import db_manager
import app.db_ops as db_ops
from app.routers import config, commands, export

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Старт приложения - инициализируем пулы соединений и таблицы
    await db_manager.connect()
    async with db_manager.pool.acquire() as conn:
        await db_ops.init_config_table(conn)
        await db_ops.init_templates_table(conn)
    yield
    # Завершение работы
    await db_manager.disconnect()

app = FastAPI(
    title="API Integration Service",
    description="Modernized High Performance Async Integration Microservice Engine",
    version="2.0.0",
    lifespan=lifespan
)

templates = Jinja2Templates(directory="templates")

# Регистрируем роуты
app.include_router(config.router)
app.include_router(commands.router)
app.include_router(export.router)

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def web_interface(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")