<<<<<<< HEAD
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

=======
# Скрипт для быстрого развертывания AI Bot на Google Cloud Run (PowerShell)

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,
    
    [Parameter(Mandatory=$true)]
    [string]$ServiceName,
    
    [string]$Region = "us-central1"
)

# Функции для вывода сообщений
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

Write-Status "Начинаем развертывание AI Bot..."
Write-Status "Проект: $ProjectId"
Write-Status "Сервис: $ServiceName"
Write-Status "Регион: $Region"

# Проверка установки gcloud
try {
    $null = Get-Command gcloud -ErrorAction Stop
} catch {
    Write-Error "Google Cloud CLI не установлен. Установите его с https://cloud.google.com/sdk/docs/install"
    exit 1
}

# Установка проекта
Write-Status "Установка проекта..."
gcloud config set project $ProjectId

# Включение необходимых API
Write-Status "Включение необходимых API..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Сборка и развертывание
Write-Status "Сборка и развертывание контейнера..."
gcloud run deploy $ServiceName `
  --source . `
  --platform managed `
  --region $Region `
  --allow-unauthenticated `
  --port 8080 `
  --memory 1Gi `
  --cpu 1 `
  --timeout 300 `
  --max-instances 10 `
  --set-env-vars "PORT=8080"

# Получение URL сервиса
Write-Status "Получение URL сервиса..."
$ServiceUrl = gcloud run services describe $ServiceName --region=$Region --format="value(status.url)"

Write-Status "✅ Развертывание завершено!"
Write-Status "🌐 URL сервиса: $ServiceUrl"
Write-Status "📡 Webhook URL: $ServiceUrl/webhook"
Write-Status "❤️ Health check: $ServiceUrl/"

Write-Host ""
Write-Warning "Следующие шаги:"
Write-Host "1. Настройте переменные окружения в Cloud Run Console"
Write-Host "2. Установите webhook:"
Write-Host "   python setup_webhook.py YOUR_BOT_TOKEN $ServiceUrl/webhook"
Write-Host "3. Проверьте статус:"
Write-Host "   python setup_webhook.py YOUR_BOT_TOKEN --info"
Write-Host "4. Проверьте здоровье сервиса:"
Write-Host "   curl $ServiceUrl/"

Write-Status "Готово! 🎉"
>>>>>>> 562d10c69e6e854963bf134dc1a919227ef51d4d
