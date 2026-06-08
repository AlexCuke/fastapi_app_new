FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей (для asyncpg, uvloop и т.д.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей и их установка
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всего кода
COPY . .

# Создание директории для статики (если её нет, но она может понадобиться)
RUN mkdir -p static

# Переменные окружения по умолчанию (можно переопределить в compose)
ENV PYTHONPATH=/app
ENV PORT=8000

# Открываем порт
EXPOSE 8000

# Запуск приложения через uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]