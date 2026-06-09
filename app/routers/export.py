# app/routers/export.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
import asyncpg
import os

from app.db import get_db
from app.config import settings
from app.models import ExportRequest
from app.elastic_export import run_export, export_to_keys_job
import app.db_ops as db_ops

router = APIRouter(tags=["Elastic Export Processing"])


@router.post("/export")
async def export_elastic(background_tasks: BackgroundTasks, req: ExportRequest, request: Request):
    """Фоновый экспорт из Elasticsearch напрямую в БД (без CSV)."""
    background_tasks.add_task(
        run_export,
        request.app.state.export_status,
        request.app.state.export_lock,
        req.export_index_final
    )
    return {"message": "Экспорт из Elasticsearch запущен."}


@router.get("/export/status")
async def export_status(request: Request):
    return request.app.state.export_status


@router.post("/export-to-csv")
async def export_table_to_csv(conn: asyncpg.Connection = Depends(get_db)):
    """
    Экспортирует таблицу elastic_index в CSV-файл (output_PA.csv)
    с использованием порядка колонок из config_headers.
    """
    try:
        count = await db_ops.export_table_to_csv(conn, 'elastic_index', settings.OUTPUT_CSV, settings.SORT_FILENAME_DB)
        return {"message": f"Таблица elastic_index выгружена в {settings.OUTPUT_CSV}. Строк: {count}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка выгрузки: {str(e)}")


@router.post("/import-csv")
async def import_csv_to_index(conn: asyncpg.Connection = Depends(get_db)):
    """
    Импортирует данные из CSV-файла (output_PA.csv) в таблицу elastic_index.
    """
    csv_path = settings.OUTPUT_CSV
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=400, detail=f"Файл {csv_path} не найден.")
    try:
        await conn.execute("DROP TABLE IF EXISTS elastic_index")
        await db_ops.load_csv_to_table_async(conn, csv_path, 'elastic_index')
        await db_ops.refresh_status_tracker(conn, "Импорт локального CSV")
        return {"message": f"Данные из {csv_path} импортированы в elastic_index."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка импорта: {str(e)}")


@router.post("/export_to_keys")
async def export_to_keys_endpoint(background_tasks: BackgroundTasks, request: Request):
    background_tasks.add_task(export_to_keys_job, request.app.state.export_status, request.app.state.export_lock)
    return {"message": "Экспорт keys запущен."}


@router.post("/create_keys")
async def create_keys(conn: asyncpg.Connection = Depends(get_db)):
    try:
        count = await db_ops.copy_index_to_keys(conn)
        return {"message": f"Таблица 'keys' создана, заполнено {count} записей."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-headers")
async def import_headers_to_db(conn: asyncpg.Connection = Depends(get_db)):
    try:
        count = await db_ops.load_headers_to_table_async(conn)
        return {"message": f"Импортировано {count} заголовков в config_headers из headers.csv и headers_index.csv."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка импорта схемы заголовков: {str(e)}")


@router.post("/copy-index-to-final")
async def copy_index_to_final(conn: asyncpg.Connection = Depends(get_db)):
    try:
        count = await db_ops.copy_index_to_index_final_async(conn)
        return {"message": f"Данные скопированы из elastic_index в index_final. Строк: {count}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка копирования: {str(e)}")


