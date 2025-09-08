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
