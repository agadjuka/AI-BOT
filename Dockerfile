# Базовый образ
FROM python:3.11-slim

# Устанавливаем системные зависимости для OpenCV
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы
COPY . .

# Получаем credentials как build argument
ARG GOOGLE_APPLICATION_CREDENTIALS_JSON

# Создаем файл credentials из build argument (для Google Sheets)
# Создаем файл с именем, которое ожидает конфигурация
RUN if [ -n "$GOOGLE_APPLICATION_CREDENTIALS_JSON" ]; then \
        echo "$GOOGLE_APPLICATION_CREDENTIALS_JSON" > /app/google_sheets_credentials_fixed.json; \
        echo "✅ Создан файл credentials для Google Sheets: google_sheets_credentials_fixed.json"; \
    else \
        echo "❌ GOOGLE_APPLICATION_CREDENTIALS_JSON не передан"; \
    fi

# Для Vertex AI используем Application Default Credentials (ADC)
# Cloud Run автоматически предоставляет сервисный аккаунт

# Cloud Run передает порт в переменной $PORT
ENV PORT=8080

# Запускаем оригинальный main.py
CMD ["python", "main.py"]