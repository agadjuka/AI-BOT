# Базовый образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы
COPY . .

# Получаем credentials как build argument
ARG GOOGLE_APPLICATION_CREDENTIALS_JSON

# Создаем файл credentials из build argument
RUN if [ -n "$GOOGLE_APPLICATION_CREDENTIALS_JSON" ]; then \
        echo "$GOOGLE_APPLICATION_CREDENTIALS_JSON" > /app/gcp_credentials.json; \
        echo "✅ Создан файл credentials"; \
    else \
        echo "❌ GOOGLE_APPLICATION_CREDENTIALS_JSON не передан"; \
    fi

# Устанавливаем переменную окружения для credentials
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/gcp_credentials.json

# Cloud Run передает порт в переменной $PORT
ENV PORT=8080

# Запускаем оригинальный main.py
CMD ["python", "main.py"]