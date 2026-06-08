#!/usr/bin/env python3
"""
Скрипт для быстрого создания структуры базы данных и начального наполнения.
Запуск: python init_db.py
"""

import asyncio
import asyncpg
import json
import os
import sys
from pathlib import Path

# Добавляем корень проекта в path для импорта конфигов
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.default_templates import DEFAULT_TEMPLATES

# SQL для создания таблиц (статические схемы)
CREATE_TABLES_SQL = """
-- Таблица конфигурации
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    group_name TEXT DEFAULT 'default'
);

-- Таблица шаблонов команд
CREATE TABLE IF NOT EXISTS request_templates (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    method TEXT NOT NULL,
    path TEXT NOT NULL,
    payload JSONB NOT NULL,
    group_name TEXT DEFAULT 'default'
);

-- Таблица трекера статусов
CREATE TABLE IF NOT EXISTS status_tracker (
    id SERIAL PRIMARY KEY,
    assignment_id TEXT,
    assignment_status TEXT,
    procedure_code TEXT,
    procedure_status TEXT,
    trigger_command TEXT,
    last_updated TEXT,
    tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для пользовательских названий заголовков (sort_headers)
CREATE TABLE IF NOT EXISTS sort_headers (
    filename TEXT,
    header TEXT,
    name TEXT
);

-- Таблица настроек схем файлов
CREATE TABLE IF NOT EXISTS settings (
    filename TEXT PRIMARY KEY,
    headers TEXT NOT NULL
);

-- Динамические таблицы (создаются пустыми, структура будет заполнена позже)
-- elastic_index – основная таблица для данных из Elasticsearch/CSV
CREATE TABLE IF NOT EXISTS elastic_index (placeholder TEXT);

-- index_final – финальное представление данных с приведёнными заголовками
CREATE TABLE IF NOT EXISTS index_final (placeholder TEXT);

-- keys – таблица ключей
CREATE TABLE IF NOT EXISTS keys (placeholder TEXT);

-- Таблицы для текущего назначения (будут пересозданы при синхронизации)
CREATE TABLE IF NOT EXISTS current_assignment (placeholder TEXT);
CREATE TABLE IF NOT EXISTS currrent_assignment (placeholder TEXT);
"""

# Значения конфигурации по умолчанию (из db_ops.init_config_table)
DEFAULT_CONFIG = {
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


async def init_db():
    """Инициализация базы данных: создание таблиц и начальных данных."""
    try:
        # Подключение к БД
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
        )
        print(f"✅ Подключено к БД {settings.DB_NAME} на {settings.DB_HOST}:{settings.DB_PORT}")

        # Создание таблиц
        await conn.execute(CREATE_TABLES_SQL)
        print("✅ Таблицы созданы (или уже существуют)")

        # Заполнение таблицы config
        for key, value in DEFAULT_CONFIG.items():
            await conn.execute(
                "INSERT INTO config (key, value, group_name) VALUES ($1, $2, 'default') "
                "ON CONFLICT (key) DO NOTHING",
                key, str(value)
            )
        print(f"✅ Вставлено {len(DEFAULT_CONFIG)} записей в config")

        # Заполнение таблицы request_templates (из default_templates)
        for tmpl in DEFAULT_TEMPLATES:
            await conn.execute(
                "INSERT INTO request_templates (name, method, path, payload, group_name) "
                "VALUES ($1, $2, $3, $4, $5) ON CONFLICT (name) DO NOTHING",
                tmpl['name'],
                tmpl['method'],
                tmpl['path'],
                json.dumps(tmpl['payload']),
                tmpl.get('group_name', 'default')
            )
        print(f"✅ Вставлено {len(DEFAULT_TEMPLATES)} шаблонов в request_templates")

        # Очистка динамических таблиц от заглушек (placeholder)
        for table in ['elastic_index', 'index_final', 'keys', 'current_assignment', 'currrent_assignment']:
            await conn.execute(f"DELETE FROM {table} WHERE placeholder IS NOT NULL")
            # Удаляем столбец placeholder, если он существует (но таблица может быть пустой)
            try:
                await conn.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS placeholder")
            except Exception:
                pass
        print("✅ Динамические таблицы подготовлены")

        await conn.close()
        print("🎉 Инициализация БД успешно завершена!")

    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(init_db())