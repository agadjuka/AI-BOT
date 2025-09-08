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
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]
