import json
import csv
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Set, Optional
from elasticsearch import AsyncElasticsearch

from app.config import settings
from app.db import db_manager
import app.db_ops as db_ops

logger = logging.getLogger(__name__)

ExportState = Dict[str, Any]

def flatten_dict(obj: Any, parent_key: str = '', sep: str = '.') -> Dict[str, str]:
    items = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(flatten_dict(v, new_key, sep=sep))
            elif isinstance(v, list):
                items[new_key] = json.dumps(v, ensure_ascii=False)
            else:
                items[new_key] = str(v) if v is not None else ''
    else:
        items[parent_key] = str(obj) if obj is not None else ''
    return items


def extract_base_parts(obj: Dict) -> Dict:
    base = {}
    if 'entityId' in obj:
        base['entityId'] = obj['entityId']
    data = obj.get('data')
    if not isinstance(data, dict):
        return base
    for section in ('patientMovement', 'hospitalCard', 'careCase'):
        if section in data and isinstance(data[section], dict):
            base.update(flatten_dict(data[section], section))
    pa = data.get('procedureAssignment')
    if isinstance(pa, dict):
        pa_without_elements = {k: v for k, v in pa.items() if k != 'elements'}
        base.update(flatten_dict(pa_without_elements, 'procedureAssignment'))
    return base


def explode_row(obj: Dict) -> List[Dict]:
    base = extract_base_parts(obj)
    data = obj.get('data')
    if not isinstance(data, dict):
        return [base] if base else []
    pa = data.get('procedureAssignment')
    if not isinstance(pa, dict):
        return [base] if base else []
    elements = pa.get('elements')
    if not isinstance(elements, list) or len(elements) == 0:
        return [base] if base else []
    rows = []
    for elem in elements:
        if isinstance(elem, dict):
            elem_flat = flatten_dict(elem, 'procedureAssignment.elements')
        else:
            elem_flat = {'procedureAssignment.elements': str(elem) if elem is not None else ''}
        row = {**base, **elem_flat}
        rows.append(row)
    return rows


def write_csv_normal(filename: str, rows: List[Dict], all_keys: Set[str], column_order: Optional[List[str]]) -> List[str]:
    if column_order:
        final_fields = [col for col in column_order if col in all_keys]
        missing_fields = sorted(all_keys - set(final_fields))
        final_fields.extend(missing_fields)
    else:
        final_fields = sorted(all_keys)
    with open(filename, 'w', encoding='utf-8-sig', newline='') as outfile:
        writer = csv.DictWriter(
            outfile, fieldnames=final_fields, delimiter=';',
            restval='', extrasaction='ignore', quoting=csv.QUOTE_ALL
        )
        writer.writeheader()
        writer.writerows(rows)
    return final_fields


async def run_export(state: ExportState, lock: asyncio.Lock, export_index_final: bool = True):
    async with lock:
        state.update({"status": "running", "message": "Экспорт запущен...", "timestamp": datetime.now().isoformat(), "rows_exported": 0})

    es = AsyncElasticsearch([settings.ES_HOST], verify_certs=False)
    try:
        response = await es.search(
            index=settings.INDEX_NAME,
            scroll=f"{settings.REQUEST_TIMEOUT_ES}m",
            size=settings.SCROLL_SIZE,
            query={"match_all": {}},
            request_timeout=settings.REQUEST_TIMEOUT_ES
        )
        scroll_id = response["_scroll_id"]
        total = response["hits"]["total"]["value"]
        logger.info(f"Elasticsearch index: {settings.INDEX_NAME}, Total documents: {total}")

        rows = []
        all_keys = set()
        processed = 0

        with open(settings.OUTPUT_JSONL, "w", encoding="utf-8") as jsonl_file:
            while True:
                hits = response["hits"]["hits"]
                if not hits:
                    break
                for hit in hits:
                    source = hit["_source"]
                    jsonl_file.write(json.dumps(source, ensure_ascii=False) + "\n")
                    if not isinstance(source, dict):
                        continue
                    data = source.get('data')
                    if not isinstance(data, dict) or 'procedureAssignment' not in data:
                        continue
                    exploded = explode_row(source)
                    for row in exploded:
                        if any(key.startswith('careCase.') for key in row.keys()):
                            rows.append(row)
                            all_keys.update(row.keys())
                processed += len(hits)
                logger.info(f"Processed: {processed}/{total} docs, Accumulating {len(rows)} rows.")
                response = await es.scroll(scroll_id=scroll_id, scroll=f"{settings.REQUEST_TIMEOUT_ES}m")
                scroll_id = response["_scroll_id"]
        await es.clear_scroll(scroll_id=scroll_id)

        if not rows:
            async with lock:
                state.update({"status": "completed", "message": "Нет записей для экспорта.", "rows_exported": 0})
            logger.info("No matching records found to insert.")
            return

        async with db_manager.pool.acquire() as conn:
            col_order = await db_ops.get_column_order_from_db(conn, 'config_headers', settings.SORT_FILENAME_DB)
            if not col_order:
                logger.warning("Не найден порядок колонок для elastic_index, загрузка невозможна")
                async with lock:
                    state.update({"status": "error", "message": "Отсутствует схема колонок для elastic_index"})
                return

            await db_ops.load_rows_to_table_directly_async(conn, rows, col_order, 'elastic_index')
            logger.info(f"Directly loaded {len(rows)} rows into 'elastic_index'")

            await db_ops.sync_current_assignment(conn)
            await db_ops.refresh_status_tracker(conn, trigger_command="Импорт из Elasticsearch")

            if export_index_final:
                col_order_index = await db_ops.get_column_order_from_db(conn, 'config_headers', settings.SORT_INDEX_FILENAME_DB)
                if col_order_index:
                    await db_ops.load_rows_to_table_directly_async(conn, rows, col_order_index, 'index_final')
                    logger.info(f"Direct loaded {len(rows)} rows into 'index_final'")
                else:
                    logger.warning("Missing column order for 'index_final'")

        async with lock:
            state.update({"status": "completed", "message": f"Экспорт завершён. Загружено {len(rows)} строк.", "rows_exported": len(rows)})
    except Exception as e:
        async with lock:
            state.update({"status": "error", "message": f"Ошибка: {str(e)}"})
        logger.exception("Export error")
    finally:
        await es.close()


async def export_to_keys_job(state: ExportState, lock: asyncio.Lock):
    async with lock:
        state.update({"status": "running", "message": "Экспорт keys запущен...", "timestamp": datetime.now().isoformat(), "rows_exported": 0})

    es = AsyncElasticsearch([settings.ES_HOST], verify_certs=False)
    try:
        response = await es.search(
            index=settings.INDEX_NAME,
            scroll=f"{settings.REQUEST_TIMEOUT_ES}m",
            size=settings.SCROLL_SIZE,
            query={"match_all": {}},
            request_timeout=settings.REQUEST_TIMEOUT_ES
        )
        scroll_id = response["_scroll_id"]
        total = response["hits"]["total"]["value"]

        rows = []
        all_keys = set()

        while True:
            hits = response["hits"]["hits"]
            if not hits:
                break
            for hit in hits:
                source = hit["_source"]
                if not isinstance(source, dict):
                    continue
                data = source.get('data')
                if not isinstance(data, dict) or 'procedureAssignment' not in data:
                    continue
                exploded = explode_row(source)
                for row in exploded:
                    if any(key.startswith('careCase.') for key in row.keys()):
                        rows.append(row)
                        all_keys.update(row.keys())
            response = await es.scroll(scroll_id=scroll_id, scroll=f"{settings.REQUEST_TIMEOUT_ES}m")
            scroll_id = response["_scroll_id"]
        await es.clear_scroll(scroll_id=scroll_id)

        if not rows:
            async with lock:
                state.update({"status": "completed", "message": "Нет записей для keys.", "rows_exported": 0})
            logger.info("No keys records extracted.")
            return

        async with db_manager.pool.acquire() as conn:
            column_order = await db_ops.get_sort_headers_from_index(conn)
            if not column_order:
                async with lock:
                    state.update({"status": "error", "message": "Не удалось получить порядок столбцов для keys."})
                return
            await db_ops.load_rows_to_table_directly_async(conn, rows, column_order, 'keys')
            async with lock:
                state.update({"status": "completed", "message": f"Keys экспортированы. Загружено {len(rows)} строк.", "rows_exported": len(rows)})
            logger.info(f"Successfully finalized keys export, populated {len(rows)} records.")
    except Exception as e:
        async with lock:
            state.update({"status": "error", "message": f"Ошибка keys: {str(e)}"})
        logger.exception("Failed keys export execution")
    finally:
        await es.close()