import json
import asyncpg
from typing import Dict, List, Optional, Any

async def init_config_table(conn: asyncpg.Connection):
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
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

async def init_templates_table(conn: asyncpg.Connection):
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS request_templates (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            method TEXT NOT NULL,
            path TEXT NOT NULL,
            payload JSONB NOT NULL
        )
    """)
    count = await conn.fetchval("SELECT COUNT(*) FROM request_templates")
    if count == 0:
        await reset_templates_table(conn)

async def reset_templates_table(conn: asyncpg.Connection):
    """Очищает и наполняет таблицу команд из файла default_templates.py"""
    await conn.execute("CREATE TABLE IF NOT EXISTS request_templates (id SERIAL PRIMARY KEY, name TEXT UNIQUE NOT NULL, method TEXT NOT NULL, path TEXT NOT NULL, payload JSONB NOT NULL)")
    await conn.execute("TRUNCATE TABLE request_templates RESTART IDENTITY")
    
    from app.default_templates import DEFAULT_TEMPLATES
    for tmpl in DEFAULT_TEMPLATES:
        await conn.execute(
            "INSERT INTO request_templates (name, method, path, payload) VALUES ($1, $2, $3, $4)",
            tmpl['name'], tmpl['method'], tmpl['path'], json.dumps(tmpl['payload'])
        )

async def update_config_value(conn: asyncpg.Connection, key: str, value: str):
    await conn.execute(
        "INSERT INTO config (key, value) VALUES ($1, $2) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
        key, str(value)
    )

async def load_config(conn: asyncpg.Connection) -> Dict[str, str]:
    rows = await conn.fetch("SELECT key, value FROM config")
    return {row['key']: row['value'] for row in rows}

async def get_all_templates_db(conn: asyncpg.Connection):
    return await conn.fetch("SELECT name FROM request_templates ORDER BY id")

async def get_template_by_name_db(conn: asyncpg.Connection, name: str):
    return await conn.fetchrow("SELECT payload FROM request_templates WHERE name = $1", name)