#!/bin/bash

# Скрипт для деплоя AI Bot в Google Cloud Run
# Убедитесь, что у вас установлен gcloud CLI и вы авторизованы

set -e

# Переменные
PROJECT_ID="just-advice-470905-a3"
SERVICE_NAME="ai-bot"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Начинаем деплой AI Bot в Google Cloud Run..."

# Проверяем, что gcloud установлен
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI не найден. Установите Google Cloud SDK"
    exit 1
fi

# Проверяем авторизацию
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Не авторизованы в gcloud. Выполните: gcloud auth login"
    exit 1
fi

# Устанавливаем проект
echo "📋 Устанавливаем проект: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Включаем необходимые API
echo "🔧 Включаем необходимые API..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Сборка и отправка образа
echo "🏗️ Собираем Docker образ..."
gcloud builds submit --tag $IMAGE_NAME .

# Деплой в Cloud Run
echo "🚀 Деплоим в Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 10 \
    --min-instances 0 \
    --timeout 300 \
    --set-env-vars "BOT_TOKEN=8291213805:AAEHDlkDCHLQ3RFtrB5HLMeU-nGzF1hOZYE,POSTER_TOKEN=853931:71424838d41a70ee724e07ef6c6f0774,PROJECT_ID=$PROJECT_ID"

echo "✅ Деплой завершен!"
echo "🌐 URL сервиса:"
gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)"

echo ""
echo "📊 Для просмотра логов используйте:"
echo "gcloud logs tail --follow --service=$SERVICE_NAME --region=$REGION"

