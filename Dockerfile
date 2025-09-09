# Базовый образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости
COPY requirements_full.txt .
RUN pip install --no-cache-dir -r requirements_full.txt

# Копируем файл
COPY main_full.py .

# Cloud Run передает порт в переменной $PORT
ENV PORT=8080

# Запускаем полную версию
CMD ["python", "main_full.py"]