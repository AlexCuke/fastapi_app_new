import json
import csv
import os
from typing import Dict, List, Optional, Any
import asyncpg

SCHEMA_FILE_MAPPING = {
    'sort.csv': 'elastic_index',          # изменено
    'sort_index.csv': 'index_final',
    'keys.csv': 'keys',
}


def _read_schema_headers_from_csv(filepath: str) -> List[str]:
    """Читает первую строку CSV-схемы (разделитель ';', BOM-safe)."""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')
        try:
            raw_headers = next(reader)
        except StopIteration:
            return []
    clean_headers = []
    for col in raw_headers:
        col = col.strip().strip('\ufeff')
        if col:
            clean_headers.append(col)
    return clean_headers


async def init_config_table(conn: asyncpg.Connection):
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            group_name TEXT DEFAULT 'default'
        )
    """)
    await conn.execute("""
        ALTER TABLE config ADD COLUMN IF NOT EXISTS group_name TEXT DEFAULT 'default'
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS status_tracker (
            id SERIAL PRIMARY KEY,
            assignment_id TEXT,
            assignment_status TEXT,
            procedure_code TEXT,
            procedure_status TEXT,
            trigger_command TEXT,
            last_updated TEXT,
            tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    default_config = {
        'assignmentCompositionUid': '550e8400-e29b-41d4-a716-446655440000',
        'code': 'PROC_ROLLBACK_01',
        'workplaceId': 'workplace_40',
        'doctorName': 'Крылова Татьяна Сергеевна',
        'doctorJob': 'Радиолог',
        'resultCompositionUid': 'res_12345678-1234-1234-1234-123456789abc',
        'careCaseId': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
        'patientId': 'patient_67890',
        'ehrId': 'ehr_12345',
        'assignmentId': '019e6830-7f8a-7039-8d96-7de04ddf5144',
        'procedureCode': '518b220d-9d4a-4ca6-a3d9-bda810829569',
        'assignmentCode': 'ASSIGN_CODE_001',
        'assignmentName': 'МРТ головы',
        'assigneeId': '101',
        'assigneeName': 'Исполнитель Иванов',
        'cito': 'CITO',
        'effectArea': 'Голова',
        'room': 'Каб. МРТ-1',
        'deviceId': 'MRT_01',
        'scheduleCode': 'SCHED_001',
        'periodCode': 'MORNING',
        'procedureDressing': 'Нет',
        'isDoctor': 'True',
        'procedureCount': '1',
        'pmuNaz': 'PMU_001',
        'byExecutor': 'True',
        'description': 'Пациент стабилен',
        'dayTimePeriod': 'MORNING',
        'compositionUid': 'd0e1f2a3-4567-8901-2345-abcdef012345',
        'executorId': '202',
    }
    for key, val in default_config.items():
        await conn.execute(
            "INSERT INTO config (key, value, group_name) VALUES ($1, $2, $3) ON CONFLICT (key) DO NOTHING",
            key, str(val), 'default'
        )


async def init_templates_table(conn: asyncpg.Connection):
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS request_templates (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            method TEXT NOT NULL,
            path TEXT NOT NULL,
            payload JSONB NOT NULL,
            group_name TEXT DEFAULT 'default'
        )
    """)
    await conn.execute("""
        ALTER TABLE request_templates ADD COLUMN IF NOT EXISTS group_name TEXT DEFAULT 'default'
    """)
    count = await conn.fetchval("SELECT COUNT(*) FROM request_templates")
    if count == 0:
        from app.default_templates import DEFAULT_TEMPLATES
        for tmpl in DEFAULT_TEMPLATES:
            await conn.execute(
                "INSERT INTO request_templates (name, method, path, payload, group_name) VALUES ($1, $2, $3, $4, $5)",
                tmpl['name'], tmpl['method'], tmpl['path'], json.dumps(tmpl['payload']), tmpl.get('group_name', 'default')
            )


async def refresh_status_tracker(conn: asyncpg.Connection, trigger_command: str = "Системный апдейт"):
    config = await load_config(conn)
    assignment_id = config.get('assignmentId')
    procedure_code = config.get('procedureCode')
    if not assignment_id or not procedure_code:
        return
    table_exists = await conn.fetchval("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'elastic_index'
        )
    """)
    if not table_exists:
        return
    columns_rows = await conn.fetch("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'elastic_index'
    """)
    cols = [r['column_name'] for r in columns_rows]
    col_assign_id = "procedureAssignment.assignmentId" if "procedureAssignment.assignmentId" in cols else next((c for c in cols if c.lower().endswith("assignmentid")), "procedureAssignment.assignmentId")
    col_assign_status = "procedureAssignment.assignmentStatus" if "procedureAssignment.assignmentStatus" in cols else next((c for c in cols if c.lower().endswith("assignmentstatus")), "procedureAssignment.assignmentStatus")
    col_proc_code = "procedureAssignment.procedureCode" if "procedureAssignment.procedureCode" in cols else next((c for c in cols if c.lower().startswith("procedureassignment.procedurecod")), "procedureAssignment.procedureCode")
    col_proc_status = "procedureAssignment.status" if "procedureAssignment.status" in cols else next((c for c in cols if c.lower().endswith("status")), "procedureAssignment.status")
    col_updated = "procedureAssignment.updated" if "procedureAssignment.updated" in cols else next((c for c in cols if c.lower().endswith("updated")), "procedureAssignment.updated")
    query = f"""
        SELECT "{col_assign_status}" as assign_status, 
               "{col_proc_status}" as proc_status, 
               "{col_updated}" as updated_at
        FROM elastic_index 
        WHERE "{col_assign_id}" = $1 
          AND "{col_proc_code}" = $2
        LIMIT 1
    """
    db_row = await conn.fetchrow(query, assignment_id, procedure_code)
    db_assign_status = db_row['assign_status'] if db_row else "—"
    db_proc_status = db_row['proc_status'] if db_row else "—"
    db_updated_at = db_row['updated_at'] if db_row else "—"
    tracker_row = await conn.fetchrow("""
        SELECT assignment_status, procedure_status 
        FROM status_tracker 
        WHERE assignment_id = $1 AND procedure_code = $2
        ORDER BY id DESC LIMIT 1
    """, assignment_id, procedure_code)
    if not tracker_row:
        await conn.execute("""
            INSERT INTO status_tracker (
                assignment_id, assignment_status,
                procedure_code, procedure_status,
                trigger_command, last_updated
            ) VALUES ($1, $2, $3, $4, $5, $6)
        """, assignment_id, db_assign_status, procedure_code, db_proc_status, trigger_command, db_updated_at)
    else:
        prev_assign_status = tracker_row['assignment_status']
        prev_proc_status = tracker_row['procedure_status']
        if (prev_assign_status != db_assign_status) or (prev_proc_status != db_proc_status):
            await conn.execute("""
                INSERT INTO status_tracker (
                    assignment_id, assignment_status,
                    procedure_code, procedure_status,
                    trigger_command, last_updated
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """, assignment_id, db_assign_status, procedure_code, db_proc_status, trigger_command, db_updated_at)


async def sync_current_assignment(conn: asyncpg.Connection):
    config = await load_config(conn)
    uid = config.get('assignmentCompositionUid')
    if not uid:
        return
    index_exists = await conn.fetchval("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'elastic_index'
        )
    """)
    if not index_exists:
        return
    columns_rows = await conn.fetch("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'elastic_index'
    """)
    cols = [r['column_name'] for r in columns_rows]
    col_uid = "procedureAssignment.assignmentCompositionUid" if "procedureAssignment.assignmentCompositionUid" in cols else next((c for c in cols if c.lower().endswith("assignmentcompositionuid")), None)
    if not col_uid:
        return
    await conn.execute("DROP TABLE IF EXISTS current_assignment")
    await conn.execute(f'CREATE TABLE current_assignment AS SELECT * FROM elastic_index WHERE "{col_uid}" = $1', uid)
    await conn.execute("DROP TABLE IF EXISTS currrent_assignment")
    await conn.execute("CREATE TABLE currrent_assignment AS SELECT * FROM current_assignment")


async def copy_index_to_index_final_async(conn: asyncpg.Connection) -> int:
    index_exists = await conn.fetchval("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'elastic_index'
        )
    """)
    if not index_exists:
        raise ValueError("Таблица 'elastic_index' не найдена. Пожалуйста, сначала импортируйте CSV или запустите экспорт.")
    columns_final = await get_column_order_from_db(conn, 'sort_headers', 'index_final')
    if not columns_final:
        raise ValueError("Схема колонок для 'index_final' не найдена в 'sort_headers'. Пожалуйста, сначала нажмите 'Обновить столбцы'.")
    index_columns_rows = await conn.fetch("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'elastic_index'
    """)
    index_cols = {r['column_name'] for r in index_columns_rows}
    await conn.execute("DROP TABLE IF EXISTS index_final")
    quoted_columns_def = ", ".join([f'"{col}" TEXT' for col in columns_final])
    await conn.execute(f"CREATE TABLE index_final ({quoted_columns_def})")
    select_parts = []
    for col in columns_final:
        if col in index_cols:
            select_parts.append(f'"{col}"')
        else:
            select_parts.append(f"NULL::text as \"{col}\"")
    select_clause = ", ".join(select_parts)
    insert_cols = ", ".join([f'"{col}"' for col in columns_final])
    query = f"INSERT INTO index_final ({insert_cols}) SELECT {select_clause} FROM elastic_index"
    result = await conn.execute(query)
    await refresh_status_tracker(conn, "Синхронизация elastic_index -> index_final")
    return int(result.split()[-1]) if result else 0


async def load_config(conn: asyncpg.Connection) -> Dict[str, str]:
    rows = await conn.fetch("SELECT key, value FROM config")
    return {row['key']: row['value'] for row in rows}


async def load_config_items(conn: asyncpg.Connection) -> List[Dict[str, str]]:
    rows = await conn.fetch("SELECT key, value, group_name FROM config ORDER BY key")
    return [
        {
            "key": row['key'],
            "value": row['value'],
            "group_name": row['group_name']
        }
        for row in rows
    ]


async def update_config_value(conn: asyncpg.Connection, key: str, value: str, group_name: Optional[str] = None):
    await conn.execute(
        "INSERT INTO config (key, value, group_name) VALUES ($1, $2, $3) "
        "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, group_name = COALESCE(EXCLUDED.group_name, config.group_name)",
        key, value, group_name
    )


async def get_sort_headers_from_index(conn: asyncpg.Connection) -> List[str]:
    row = await conn.fetchrow("SELECT sort_headers FROM elastic_index LIMIT 1")
    if not row or not row['sort_headers']:
        raise ValueError("Таблица elastic_index пуста или поле sort_headers не содержит значения.")
    raw = row['sort_headers'].strip()
    if raw.startswith('[') and raw.endswith(']'):
        return json.loads(raw)
    return [c.strip() for c in raw.split(',')]


async def copy_index_to_keys(conn: asyncpg.Connection) -> int:
    columns = await get_sort_headers_from_index(conn)
    await conn.execute("DROP TABLE IF EXISTS keys")
    columns_def = ", ".join([f'"{col}" TEXT' for col in columns])
    await conn.execute(f"CREATE TABLE keys ({columns_def})")
    select_cols = ", ".join([f'"{col}"' for col in columns])
    result = await conn.execute(f"INSERT INTO keys ({select_cols}) SELECT {select_cols} FROM elastic_index")
    return int(result.split()[-1]) if result else 0


async def get_column_order_from_db(conn: asyncpg.Connection, table_name: str, filename_value: str) -> Optional[List[str]]:
    rows = await conn.fetch(f"SELECT header FROM {table_name} WHERE filename = $1 ORDER BY header", filename_value)
    return [row['header'] for row in rows] if rows else None


async def load_csv_to_table_async(conn: asyncpg.Connection, csv_file: str, table_name: str):
    import csv, os
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"Файл {csv_file} не найден")
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')
        try:
            header = next(reader)
        except StopIteration:
            return
        clean_header = [col.strip().strip('\ufeff') for col in header]
        quoted_columns = [f'"{col}"' for col in clean_header]
    
    await conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    columns_def = ", ".join([f'{qcol} TEXT' for qcol in quoted_columns])
    await conn.execute(f'CREATE TABLE "{table_name}" ({columns_def})')
    
    records = []
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)
        for row in reader:
            records.append(tuple(row))
    if records:
        await conn.copy_records_to_table(table_name, records=records, columns=clean_header)


async def load_rows_to_table_directly_async(conn: asyncpg.Connection, rows: List[Dict], column_order: List[str], table_name: str):
    if not column_order or not rows:
        return
    quoted_columns = [f'"{col}"' for col in column_order]
    await conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    columns_def = ", ".join([f'{qcol} TEXT' for qcol in quoted_columns])
    await conn.execute(f'CREATE TABLE "{table_name}" ({columns_def})')
    records = []
    for row in rows:
        records.append(tuple(str(row.get(col, '')) for col in column_order))
    if records:
        await conn.copy_records_to_table(table_name, records=records, columns=column_order)


async def get_all_templates_db(conn: asyncpg.Connection) -> List[asyncpg.Record]:
    return await conn.fetch("SELECT id, name, method, path, payload, group_name FROM request_templates ORDER BY id")


async def get_template_by_id_db(conn: asyncpg.Connection, template_id: int) -> Optional[asyncpg.Record]:
    return await conn.fetchrow(
        "SELECT id, name, method, path, payload, group_name FROM request_templates WHERE id = $1",
        template_id
    )


async def get_template_by_name_db(conn: asyncpg.Connection, name: str) -> Optional[asyncpg.Record]:
    return await conn.fetchrow("SELECT id, name, method, path, payload FROM request_templates WHERE name = $1", name)


async def update_template_db(
    conn: asyncpg.Connection,
    template_id: int,
    name: str,
    method: str,
    path: str,
    payload: dict,
    group_name: str
):
    await conn.execute(
        "UPDATE request_templates SET name=$1, method=$2, path=$3, payload=$4, group_name=$5 WHERE id=$6",
        name, method, path, json.dumps(payload), group_name, template_id
    )


async def load_headers_to_table_async(conn: asyncpg.Connection) -> int:
    table_name = 'sort_headers'
    await conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (filename TEXT, header TEXT, name TEXT)")
    await conn.execute(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS name TEXT")
    await conn.execute(f"DELETE FROM {table_name}")
    inserted = 0
    for filepath, new_name in SCHEMA_FILE_MAPPING.items():
        if not os.path.exists(filepath):
            continue
        clean_headers = _read_schema_headers_from_csv(filepath)
        if not clean_headers:
            continue
        for header in clean_headers:
            await conn.execute(
                f"INSERT INTO {table_name} (filename, header, name) VALUES ($1, $2, $3)",
                new_name, header, header
            )
            inserted += 1
    return inserted


async def get_sort_headers(conn: asyncpg.Connection) -> List[Dict[str, str]]:
    await conn.execute("CREATE TABLE IF NOT EXISTS sort_headers (filename TEXT, header TEXT, name TEXT)")
    await conn.execute("ALTER TABLE sort_headers ADD COLUMN IF NOT EXISTS name TEXT")
    rows = await conn.fetch("SELECT filename, header, name FROM sort_headers ORDER BY filename, header")
    return [dict(row) for row in rows]


async def update_sort_header_name(conn: asyncpg.Connection, filename: str, header: str, name: str) -> None:
    await conn.execute("CREATE TABLE IF NOT EXISTS sort_headers (filename TEXT, header TEXT, name TEXT)")
    result = await conn.execute(
        "UPDATE sort_headers SET name=$1 WHERE filename=$2 AND header=$3",
        name, filename, header
    )
    if result == 'UPDATE 0':
        await conn.execute(
            "INSERT INTO sort_headers (filename, header, name) VALUES ($1, $2, $3)",
            filename, header, name
        )


async def init_settings_schema_table_async(conn: asyncpg.Connection) -> int:
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            filename TEXT PRIMARY KEY,
            headers TEXT NOT NULL
        )
    """)
    await conn.execute("DELETE FROM settings")
    inserted = 0
    for filepath, _ in SCHEMA_FILE_MAPPING.items():
        if not os.path.exists(filepath):
            continue
        clean_headers = _read_schema_headers_from_csv(filepath)
        if not clean_headers:
            continue
        await conn.execute(
            "INSERT INTO settings (filename, headers) VALUES ($1, $2)",
            filepath, ';'.join(clean_headers)
        )
        inserted += 1
    return inserted