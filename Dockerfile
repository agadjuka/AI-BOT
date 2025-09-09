# Базовый образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run передает порт в переменной $PORT
ENV PORT=8080

# Запускаем основной код
CMD ["python", "main_test.py"]