from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from app.db import db_manager
import app.db_ops as db_ops
from app.routers import config, commands, export

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_manager.connect()
    async with db_manager.pool.acquire() as conn:
        await db_ops.init_config_table(conn)
        await db_ops.init_templates_table(conn)
    from app.kafka_producer import kafka_manager
    await kafka_manager.start()
    yield
    from app.kafka_producer import kafka_manager
    await kafka_manager.stop()
    await db_manager.disconnect()

app = FastAPI(title="API Integration Service", version="2.1.0", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

app.include_router(config.router)
app.include_router(commands.router)
app.include_router(export.router)

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def web_interface(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/settings", response_class=HTMLResponse, include_in_schema=False)
async def settings_interface(request: Request):
    return templates.TemplateResponse(request=request, name="settings.html")

@app.get("/services", response_class=HTMLResponse, include_in_schema=False)
async def services_interface(request: Request):
    return templates.TemplateResponse(request=request, name="services.html")