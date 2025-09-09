# Базовый образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы
COPY . .

# Cloud Run передает порт в переменной $PORT
ENV PORT=8080

# Запускаем оригинальный main.py
CMD ["python", "main.py"]