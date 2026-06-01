# FastAPI Integration Service

Современный асинхронный интеграционный сервис, построенный на базе стандартов **FastAPI** и **Pydantic v2**.

## Установка и запуск

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt

2.  Настройте подключение к БД. Вы можете определить переменные окружения в
    файле .env в корневой директории:

    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=mydb
    DB_USER=postgres
    DB_PASSWORD=sa
    ES_HOST=http://elastic-dev.m15.dzm:80/

3.  Запустите сервис через uvicorn:

    uvicorn main:app --reload

4.  Откройте в браузере:

      - Интерактивный UI-интерфейс: http://localhost:8000/
      - Интерактивная OpenAPI-документация (Swagger): http://localhost:8000/docs
        