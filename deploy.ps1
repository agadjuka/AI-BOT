# Скрипт для деплоя AI Bot в Google Cloud Run (PowerShell)
# Убедитесь, что у вас установлен gcloud CLI и вы авторизованы

# Переменные
$PROJECT_ID = "just-advice-470905-a3"
$SERVICE_NAME = "ai-bot"
$REGION = "us-central1"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host "🚀 Начинаем деплой AI Bot в Google Cloud Run..." -ForegroundColor Green

# Проверяем, что gcloud установлен
try {
    gcloud --version | Out-Null
} catch {
    Write-Host "❌ gcloud CLI не найден. Установите Google Cloud SDK" -ForegroundColor Red
    exit 1
}

# Проверяем авторизацию
$authCheck = gcloud auth list --filter=status:ACTIVE --format="value(account)"
if (-not $authCheck) {
    Write-Host "❌ Не авторизованы в gcloud. Выполните: gcloud auth login" -ForegroundColor Red
    exit 1
}

# Устанавливаем проект
Write-Host "📋 Устанавливаем проект: $PROJECT_ID" -ForegroundColor Yellow
gcloud config set project $PROJECT_ID

# Включаем необходимые API
Write-Host "🔧 Включаем необходимые API..." -ForegroundColor Yellow
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Сборка и отправка образа
Write-Host "🏗️ Собираем Docker образ..." -ForegroundColor Yellow
gcloud builds submit --tag $IMAGE_NAME .

# Деплой в Cloud Run
Write-Host "🚀 Деплоим в Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_NAME `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --port 8080 `
    --memory 1Gi `
    --cpu 1 `
    --max-instances 10 `
    --min-instances 0 `
    --timeout 300 `
    --set-env-vars "BOT_TOKEN=8291213805:AAEHDlkDCHLQ3RFtrB5HLMeU-nGzF1hOZYE,POSTER_TOKEN=853931:71424838d41a70ee724e07ef6c6f0774,PROJECT_ID=$PROJECT_ID"

Write-Host "✅ Деплой завершен!" -ForegroundColor Green
Write-Host "🌐 URL сервиса:" -ForegroundColor Cyan
$url = gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)"
Write-Host $url -ForegroundColor White

Write-Host ""
Write-Host "📊 Для просмотра логов используйте:" -ForegroundColor Yellow
Write-Host "gcloud logs tail --follow --service=$SERVICE_NAME --region=$REGION" -ForegroundColor White

