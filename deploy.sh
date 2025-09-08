#!/bin/bash

# Скрипт для быстрого развертывания AI Bot на Google Cloud Run

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка аргументов
if [ $# -lt 2 ]; then
    print_error "Использование: $0 <PROJECT_ID> <SERVICE_NAME> [REGION]"
    echo "Пример: $0 my-project-id aibot-service us-central1"
    exit 1
fi

PROJECT_ID=$1
SERVICE_NAME=$2
REGION=${3:-us-central1}

print_status "Начинаем развертывание AI Bot..."
print_status "Проект: $PROJECT_ID"
print_status "Сервис: $SERVICE_NAME"
print_status "Регион: $REGION"

# Проверка установки gcloud
if ! command -v gcloud &> /dev/null; then
    print_error "Google Cloud CLI не установлен. Установите его с https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Установка проекта
print_status "Установка проекта..."
gcloud config set project $PROJECT_ID

# Включение необходимых API
print_status "Включение необходимых API..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Сборка и развертывание
print_status "Сборка и развертывание контейнера..."
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "PORT=8080"

# Получение URL сервиса
print_status "Получение URL сервиса..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

print_status "✅ Развертывание завершено!"
print_status "🌐 URL сервиса: $SERVICE_URL"
print_status "📡 Webhook URL: $SERVICE_URL/webhook"
print_status "❤️ Health check: $SERVICE_URL/"

echo ""
print_warning "Следующие шаги:"
echo "1. Настройте переменные окружения в Cloud Run Console"
echo "2. Установите webhook:"
echo "   python setup_webhook.py YOUR_BOT_TOKEN $SERVICE_URL/webhook"
echo "3. Проверьте статус:"
echo "   python setup_webhook.py YOUR_BOT_TOKEN --info"
echo "4. Проверьте здоровье сервиса:"
echo "   curl $SERVICE_URL/"

print_status "Готово! 🎉"
