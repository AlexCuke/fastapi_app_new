from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
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
    yield
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

@app.get("/index-db", response_class=HTMLResponse, include_in_schema=False)
async def index_db_interface(request: Request):
    columns = []
    rows = []
    error = None
    async with db_manager.pool.acquire() as conn:
        try:
            await conn.execute("CREATE TABLE IF NOT EXISTS sort_headers (filename TEXT, header TEXT, name TEXT)")
            records = await conn.fetch('SELECT * FROM "index_final" LIMIT 1000')
            if records:
                columns = list(records[0].keys())
                rows = [dict(record) for record in records]
            headers = await conn.fetch("SELECT header, name FROM sort_headers WHERE filename = 'index_final'")
            name_map = {record['header']: record['name'] for record in headers}
        except Exception as exc:
            error = str(exc)
            name_map = {}
    return templates.TemplateResponse(request=request, name="index_db.html", context={"request": request, "columns": columns, "rows": rows, "error": error, "name_map": name_map})

@app.get("/current-patient", response_class=HTMLResponse, include_in_schema=False)
async def current_patient_interface(request: Request):
    columns = []
    rows = []
    error = None
    variables = {}
    required_columns = ['ACuid', 'Фамилия', 'Имя', 'Отчество', 'День рождения', 'Cito', 'Дата планируемая', 'Процедура', 'Зона возд.', 'None', 'ФИО Врача', 'Номер карты', 'Статус назначения', 'Статус', 'Code']
    async with db_manager.pool.acquire() as conn:
        try:
            await conn.execute("CREATE TABLE IF NOT EXISTS sort_headers (filename TEXT, header TEXT, name TEXT)")
            config = await db_ops.load_config(conn)
            from datetime import datetime
            variables = {
                'now_iso': datetime.now().isoformat(),
                'assignmentCode': config.get('assignmentCode', ''),
                'assignmentCompositionUid': config.get('assignmentCompositionUid', ''),
                'assignmentName': config.get('assignmentName', ''),
                'careCaseId': config.get('careCaseId', ''),
                'doctorJob': config.get('doctorJob', ''),
                'doctorName': config.get('doctorName', ''),
                'ehrId': config.get('ehrId', ''),
                'patientId': config.get('patientId', ''),
                'workplaceId': config.get('workplaceId', ''),
            }
            await db_ops.sync_current_assignment(conn)
            records = await conn.fetch('SELECT * FROM current_assignment LIMIT 1000')
            if records:
                all_columns = list(records[0].keys())
                rows = [dict(record) for record in records]
            headers = await conn.fetch("SELECT header, name FROM sort_headers WHERE filename = 'index_final'")
            name_map = {record['header']: record['name'] for record in headers}
            reverse_map = {record['name']: record['header'] for record in headers}
            columns = [reverse_map[name] for name in required_columns if name in reverse_map]
        except Exception as exc:
            error = str(exc)
            name_map = {}
    return templates.TemplateResponse(request=request, name="current_patient.html", context={"request": request, "columns": columns, "rows": rows, "error": error, "name_map": name_map, "variables": variables})

@app.get("/commands-page", response_class=HTMLResponse, include_in_schema=False)
async def commands_interface(request: Request):
    return templates.TemplateResponse(request=request, name="commands.html")

@app.get("/services", response_class=HTMLResponse, include_in_schema=False)
async def services_interface(request: Request):
    return templates.TemplateResponse(request=request, name="services.html")

@app.get("/api/index_final", response_class=JSONResponse, include_in_schema=False)
async def api_index_final():
    async with db_manager.pool.acquire() as conn:
        try:
            records = await conn.fetch('SELECT * FROM "index_final"')
            rows = [dict(record) for record in records]
            return {"data": rows}
        except Exception as e:
            return {"error": str(e), "data": []}

@app.get("/beauty", response_class=HTMLResponse, include_in_schema=False)
async def beauty_interface(request: Request):
    return templates.TemplateResponse(request=request, name="beauty.html")