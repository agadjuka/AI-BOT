# Базовый образ
FROM python:3.11-slim

# Устанавливаем системные зависимости для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ make \
    && rm -rf /var/lib/apt/lists/*

# Настройки Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8080 \
    NUMPY_DISABLE_THREADING=1

# Устанавливаем рабочую директорию
WORKDIR /app

<<<<<<< HEAD
# Копируем файлы
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
=======
# Копируем файлы зависимостей
COPY requirements.txt requirements-stable.txt ./

# Устанавливаем Python зависимости с правильным порядком
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements-stable.txt
>>>>>>> bed72345f4cca2278a731ad56c2134ad2393eaa8

COPY . .

<<<<<<< HEAD
# Cloud Run передает порт в переменной $PORT
ENV PORT=8080

# Запускаем твой код
CMD ["python", "main.py"]
=======
# Создаем директории для данных
RUN mkdir -p data

# Открываем порт
EXPOSE 8080

# Команда запуска
CMD ["python", "main.py"]
>>>>>>> bed72345f4cca2278a731ad56c2134ad2393eaa8
