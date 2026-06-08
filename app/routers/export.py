from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
import asyncpg
from app.db import get_db
from app.config import settings
from app.models import ExportRequest
from app.elastic_export import run_export, export_to_keys_job, get_export_status
import app.db_ops as db_ops

router = APIRouter(tags=["Elastic Export Processing"])

@router.post("/export")
async def export_elastic(background_tasks: BackgroundTasks, req: ExportRequest):
    background_tasks.add_task(run_export, export_index_final=req.export_index_final)
    return {"message": "Async migration batch runner task started successfully."}

@router.get("/export/status")
async def export_status():
    """Возвращает статус последнего экспорта."""
    return get_export_status()

@router.post("/export_to_keys")
async def export_to_keys_endpoint(background_tasks: BackgroundTasks):
    background_tasks.add_task(export_to_keys_job)
    return {"message": "Active synchronization workflow started successfully."}

@router.post("/create_keys")
async def create_keys(conn: asyncpg.Connection = Depends(get_db)):
    try:
        count = await db_ops.copy_index_to_keys(conn)
        return {"message": f"Table 'keys' generated, populated with {count} columns records."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import-csv")
async def import_csv_to_index(conn: asyncpg.Connection = Depends(get_db)):
    """Асинхронно очищает таблицу elastic_index и импортирует туда данные напрямую из CSV-файла."""
    import os
    csv_path = settings.OUTPUT_CSV
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=400, detail=f"Файл {csv_path} не найден в корневом каталоге приложения.")
    try:
        await conn.execute("DROP TABLE IF EXISTS elastic_index")
        await db_ops.load_csv_to_table_async(conn, csv_path, 'elastic_index')
        await db_ops.refresh_status_tracker(conn, "Импорт локального CSV")
        return {"message": f"Данные из файла {csv_path} успешно импортированы в таблицу 'elastic_index'."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка импорта: {str(e)}")

@router.post("/import-headers")
async def import_headers_to_db(conn: asyncpg.Connection = Depends(get_db)):
    try:
        count = await db_ops.load_headers_to_table_async(conn)
        return {"message": f"Успешно импортировано {count} заголовков столбцов в таблицу 'sort_headers'."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка импорта схемы заголовков: {str(e)}")

@router.post("/copy-index-to-final")
async def copy_index_to_final(conn: asyncpg.Connection = Depends(get_db)):
    try:
        count = await db_ops.copy_index_to_index_final_async(conn)
        return {"message": f"Данные успешно перенесены из 'elastic_index' в 'index_final'. Импортировано {count} строк."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка переноса данных: {str(e)}")

@router.post("/import-settings-schema")
async def import_settings_schema(conn: asyncpg.Connection = Depends(get_db)):
    try:
        count = await db_ops.init_settings_schema_table_async(conn)
        return {"message": f"Таблица настроек 'settings' успешно заполнена. Импортировано {count} записей сопоставлений файлов."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления настроек сопоставления: {str(e)}")