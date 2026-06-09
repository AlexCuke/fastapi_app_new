# main.py
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncpg

from app.db import db_manager, get_db, get_db2
import app.db_ops as db_ops
from app.routers import config, commands, export


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.export_status = {
        "status": "idle",
        "message": "",
        "timestamp": None,
        "rows_exported": 0
    }
    app.state.export_lock = asyncio.Lock()

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


# ========== SQL Query Endpoints ==========
class SqlQueryRequest(BaseModel):
    query: str
    database: str = "default"   # "default" или "hospital"


@app.post("/api/sql-query")
async def execute_sql_query(req: SqlQueryRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Пустой запрос")
    if not query.upper().startswith("SELECT"):
        raise HTTPException(status_code=400, detail="Разрешены только SELECT-запросы")

    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "GRANT", "REVOKE"]
    upper_q = query.upper()
    for word in forbidden:
        if word in upper_q:
            raise HTTPException(status_code=400, detail=f"Запрос содержит запрещённое слово: {word}")

    if req.database == "hospital":
        pool = db_manager.pool2
    else:
        pool = db_manager.pool

    if not pool:
        raise HTTPException(status_code=500, detail="Пул базы данных не инициализирован")

    async with pool.acquire() as conn:
        try:
            rows = await conn.fetch(query)
            if not rows:
                return {"columns": [], "rows": []}
            columns = list(rows[0].keys())
            result_rows = [dict(row) for row in rows]
            return {"columns": columns, "rows": result_rows}
        except asyncpg.PostgresError as e:
            raise HTTPException(status_code=400, detail=f"Ошибка SQL: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")


@app.get("/db-query", response_class=HTMLResponse, include_in_schema=False)
async def db_query_interface(request: Request):
    """Страница выполнения SQL-запросов (с выбором БД)"""
    return templates.TemplateResponse(request=request, name="db_query.html")


# ========== Остальные HTML-страницы ==========
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
            await conn.execute("CREATE TABLE IF NOT EXISTS config_headers (filename TEXT, header TEXT, name TEXT)")
            records = await conn.fetch('SELECT * FROM "index_final" LIMIT 1000')
            if records:
                columns = list(records[0].keys())
                rows = [dict(record) for record in records]
            headers = await conn.fetch("SELECT header, name FROM config_headers WHERE filename = 'index_final'")
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
            await conn.execute("CREATE TABLE IF NOT EXISTS config_headers (filename TEXT, header TEXT, name TEXT)")
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
            headers = await conn.fetch("SELECT header, name FROM config_headers WHERE filename = 'index_final'")
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

@app.get("/help", response_class=HTMLResponse, include_in_schema=False)
async def help_interface(request: Request):
    return templates.TemplateResponse(request=request, name="help.html")

@app.get("/config-params", response_class=HTMLResponse, include_in_schema=False)
async def config_params_interface(request: Request):
    return templates.TemplateResponse(request=request, name="config_params.html")

@app.get("/database", response_class=HTMLResponse, include_in_schema=False)
async def database_manager_interface(request: Request):
    return templates.TemplateResponse(request=request, name="database_manager.html")

@app.post("/api/sql-query")
async def execute_sql_query(req: SqlQueryRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Пустой запрос")
    if not query.upper().startswith("SELECT"):
        raise HTTPException(status_code=400, detail="Разрешены только SELECT-запросы")

    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "GRANT", "REVOKE"]
    upper_q = query.upper()
    for word in forbidden:
        if word in upper_q:
            raise HTTPException(status_code=400, detail=f"Запрос содержит запрещённое слово: {word}")

    if req.database == "hospital":
        if not db_manager.pool2:
            raise HTTPException(status_code=503, detail="Вторая БД (hospital_dev) недоступна. Проверьте подключение к 10.115.6.99:5432")
        pool = db_manager.pool2
    else:
        pool = db_manager.pool

    if not pool:
        raise HTTPException(status_code=500, detail="Пул базы данных не инициализирован")

    async with pool.acquire() as conn:
        try:
            rows = await conn.fetch(query)
            if not rows:
                return {"columns": [], "rows": []}
            columns = list(rows[0].keys())
            result_rows = [dict(row) for row in rows]
            return {"columns": columns, "rows": result_rows}
        except asyncpg.PostgresError as e:
            raise HTTPException(status_code=400, detail=f"Ошибка SQL: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")