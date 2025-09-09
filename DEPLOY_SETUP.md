# 🚀 Настройка автоматического деплоя на Google Cloud Run

## ✅ Что уже настроено

1. **Google Cloud Project**: `just-advice-470905-a3`
2. **API включены**: Cloud Run, Container Registry, Cloud Build
3. **Service Account создан**: `github-actions@just-advice-470905-a3.iam.gserviceaccount.com`
4. **Права назначены**: Cloud Run Admin, Storage Admin, Service Account User
5. **Cloud Run сервис создан**: `ai-bot` (URL: https://ai-bot-366461711404.europe-west1.run.app)
6. **GitHub Actions workflow**: `.github/workflows/deploy.yml`

## 🔑 Настройка GitHub Secrets

### Шаг 1: Перейдите в GitHub
1. Откройте ваш GitHub репозиторий
2. Перейдите в **Settings** (вкладка в верхнем меню)
3. В левом меню выберите **Secrets and variables** → **Actions**

### Шаг 2: Добавьте секреты
Нажмите **New repository secret** и добавьте:

#### GCP_PROJECT_ID
- **Name**: `GCP_PROJECT_ID`
- **Value**: `just-advice-470905-a3`

#### GCP_SA_KEY
- **Name**: `GCP_SA_KEY`
- **Value**: JSON ключ Service Account (создан в процессе настройки)

## 🔧 Настройка переменных окружения в Cloud Run

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/run)
2. Выберите сервис `ai-bot`
3. Нажмите **Edit & Deploy New Revision**
4. Перейдите в **Variables & Secrets**
5. Добавьте переменные:

| Переменная | Значение |
|------------|----------|
| `BOT_TOKEN` | `8291213805:AAEHDlkDCHLQ3RFtrB5HLMeU-nGzF1hOZYE` |
| `POSTER_TOKEN` | `853931:71424838d41a70ee724e07ef6c6f0774` |
| `PROJECT_ID` | `just-advice-470905-a3` |
| `PORT` | `8080` (автоматически) |

## 🚀 Запуск автоматического деплоя

### Шаг 1: Push в GitHub
```bash
git push origin clean-deploy
```

### Шаг 2: Проверка деплоя
1. Перейдите в ваш GitHub репозиторий
2. Откройте вкладку **Actions**
3. Найдите workflow "Deploy to Google Cloud Run"
4. Проверьте статус выполнения

## ✅ Проверка работы

1. **URL сервиса**: https://ai-bot-366461711404.europe-west1.run.app
2. **Health check**: https://ai-bot-366461711404.europe-west1.run.app/health
3. **Telegram бот**: отправьте `/start` вашему боту

## 🔄 Автоматическое обновление

После настройки каждый push в ветку `main` будет автоматически:
1. Собирать Docker образ
2. Загружать его в Google Container Registry
3. Обновлять Cloud Run сервис
4. Развертывать новую версию

## 📋 Файлы проекта

- `.github/workflows/deploy.yml` - GitHub Actions workflow
- `Dockerfile` - Docker конфигурация
- `.dockerignore` - исключения для Docker
- `.gitignore` - исключения для Git
- `main.py` - основной файл приложения
- `config/settings.py` - настройки приложения
- `requirements.txt` - Python зависимости

## 🎉 Готово!

После выполнения всех шагов ваш бот будет автоматически обновляться при каждом push в ветку `main`!
