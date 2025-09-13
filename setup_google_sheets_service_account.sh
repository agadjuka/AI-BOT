#!/bin/bash

# Скрипт для настройки Google Sheets service account
# Запустите этот скрипт для создания service account и настройки прав

PROJECT_ID="just-advice-470905-a3"
SERVICE_ACCOUNT_NAME="ai-bot-service-account"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
KEY_FILE="ai-bot-key.json"

echo "🚀 Настройка Google Sheets service account для проекта: $PROJECT_ID"
echo "================================================================"

# Проверяем, что gcloud настроен
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Ошибка: gcloud не аутентифицирован"
    echo "💡 Запустите: gcloud auth login"
    exit 1
fi

# Устанавливаем проект
echo "📋 Устанавливаем проект: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Создаем service account (если не существует)
echo "👤 Создаем service account: $SERVICE_ACCOUNT_NAME"
if gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL &>/dev/null; then
    echo "✅ Service account уже существует"
else
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="AI Bot Service Account" \
        --description="Service account for AI Bot Google Sheets access"
    echo "✅ Service account создан"
fi

# Создаем ключ (если не существует)
echo "🔑 Создаем ключ service account"
if [ -f "$KEY_FILE" ]; then
    echo "✅ Ключ уже существует: $KEY_FILE"
else
    gcloud iam service-accounts keys create $KEY_FILE \
        --iam-account=$SERVICE_ACCOUNT_EMAIL
    echo "✅ Ключ создан: $KEY_FILE"
fi

# Назначаем роли
echo "🔐 Назначаем роли service account"

# Роль для Google Sheets
echo "  - Назначаем роль: roles/spreadsheets.editor"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/spreadsheets.editor" \
    --quiet

# Роль для Firestore
echo "  - Назначаем роль: roles/firestore.user"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/firestore.user" \
    --quiet

# Роль для Cloud Run
echo "  - Назначаем роль: roles/run.invoker"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/run.invoker" \
    --quiet

# Включаем необходимые API
echo "🔌 Включаем необходимые API"
gcloud services enable sheets.googleapis.com --project=$PROJECT_ID
gcloud services enable firestore.googleapis.com --project=$PROJECT_ID
gcloud services enable run.googleapis.com --project=$PROJECT_ID

echo "✅ API включены"

# Проверяем права
echo "🔍 Проверяем назначенные права:"
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:$SERVICE_ACCOUNT_EMAIL"

echo ""
echo "🎉 Настройка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Скопируйте содержимое файла $KEY_FILE"
echo "2. Добавьте его в GitHub Secrets как GOOGLE_SHEETS_CREDENTIALS_JSON"
echo "3. Предоставьте доступ к Google Sheets таблице для email: $SERVICE_ACCOUNT_EMAIL"
echo ""
echo "🔑 Содержимое ключа для GitHub Secrets:"
echo "=========================================="
cat $KEY_FILE
echo "=========================================="
echo ""
echo "⚠️  ВАЖНО: Не коммитьте файл $KEY_FILE в репозиторий!"
echo "💡 Добавьте $KEY_FILE в .gitignore"
