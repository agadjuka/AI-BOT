<<<<<<< HEAD
# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем директории для данных
RUN mkdir -p data

# Устанавливаем переменные окружения
ENV PYTHONPATH=/app
ENV PORT=8080

# Открываем порт
EXPOSE 8080

# Команда запуска
CMD ["python", "main_cloud.py"]
=======
# 1) База
FROM python:3.11-slim

# 2) Системные пакеты для сборки тяжёлых либ (pandas и др.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ make \
    && rm -rf /var/lib/apt/lists/*

# 3) Настройки Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 4) Рабочая директория
WORKDIR /app

# 5) Зависимости
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# 6) Код
COPY . .

# 7) Старт с uvicorn для production
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --log-level info"]
>>>>>>> 562d10c69e6e854963bf134dc1a919227ef51d4d
