# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем системные зависимости для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ make \
    && rm -rf /var/lib/apt/lists/*

# Настройки Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8080

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем директории для данных
RUN mkdir -p data

# Открываем порт
EXPOSE 8080

# Команда запуска
CMD ["python", "main_cloud.py"]
