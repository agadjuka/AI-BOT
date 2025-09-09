# Базовый образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости
COPY requirements_telegram.txt .
RUN pip install --no-cache-dir -r requirements_telegram.txt

# Копируем файл
COPY main_telegram.py .

# Cloud Run передает порт в переменной $PORT
ENV PORT=8080

# Запускаем Telegram версию
CMD ["python", "main_telegram.py"]