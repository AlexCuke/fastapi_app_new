from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from app.db import db_manager
import app.db_ops as db_ops
from app.routers import config, commands, export

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация БД
    await db_manager.connect()
    async with db_manager.pool.acquire() as conn:
        await db_ops.init_config_table(conn)
        await db_ops.init_templates_table(conn)
    
    # Запуск Kafka (если упадет - приложение продолжит работу)
    from app.kafka_producer import kafka_manager
    try:
        await kafka_manager.start()
    except Exception as e:
        print(f"Kafka warning: {e}")
    
    yield
    # Завершение
    from app.kafka_producer import kafka_manager
    await kafka_manager.stop()
    await db_manager.disconnect()

app = FastAPI(title="API Integration Service", lifespan=lifespan)

# Указываем папку с шаблонами
templates = Jinja2Templates(directory="templates")

# Роутеры API
app.include_router(config.router)
app.include_router(commands.router)
app.include_router(export.router)

# Роуты интерфейса (Исправлен синтаксис TemplateResponse)
@app.get("/", response_class=HTMLResponse)
async def web_interface(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/settings", response_class=HTMLResponse)
async def settings_interface(request: Request):
    return templates.TemplateResponse(request=request, name="settings.html")

@app.get("/services", response_class=HTMLResponse)
async def services_interface(request: Request):
    return templates.TemplateResponse(request=request, name="services.html")