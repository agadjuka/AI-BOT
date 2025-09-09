# Базовый образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем только простой файл (без зависимостей)
COPY main_simple.py .

# Cloud Run передает порт в переменной $PORT
ENV PORT=8080

# Запускаем простую версию для тестирования
CMD ["python", "main_simple.py"]