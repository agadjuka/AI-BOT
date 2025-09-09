# Исправление проблемы деплоя на Google Cloud Run

## Проблема
Контейнер не может запуститься и слушать на порту 8080 в Google Cloud Run.

## Причины и исправления

### ✅ 1. Исправлен Dockerfile
**Проблема:** Конфликт слияния Git в Dockerfile
**Исправление:** Убраны маркеры `<<<<<<< HEAD`, `=======`, `>>>>>>> ...`

### ✅ 2. Переключен на FastAPI
**Проблема:** `main_cloud.py` использует простой HTTP сервер, который может не работать в Cloud Run
**Исправление:** Переключились на `main.py` с FastAPI + uvicorn

### ✅ 3. Исправлен cloudbuild.yaml
**Проблема:** Конфликт слияния Git в cloudbuild.yaml
**Исправление:** Убраны маркеры конфликта, объединены лучшие части

### ✅ 4. Создан GitHub Actions workflow
**Проблема:** Не было автоматического деплоя через GitHub
**Исправление:** Создан `.github/workflows/deploy.yml`

### ✅ 5. Улучшена безопасность
**Проблема:** Токены захардкожены в коде
**Исправление:** Токены теперь берутся из переменных окружения

## Файлы изменены

1. **Dockerfile** - исправлен, использует `main.py`
2. **cloudbuild.yaml** - исправлен, убран конфликт слияния
3. **main.py** - улучшена обработка переменных окружения
4. **.github/workflows/deploy.yml** - создан для автоматического деплоя
5. **GITHUB_ACTIONS_SETUP.md** - инструкция по настройке

## Что нужно сделать

### 1. Настроить GitHub Secrets
В GitHub репозитории (Settings → Secrets and variables → Actions):
```
GCP_PROJECT_ID = just-advice-470905-a3
GCP_SA_KEY = <JSON ключ service account>
BOT_TOKEN = 8291213805:AAEHDlkDCHLQ3RFtrB5HLMeU-nGzF1hOZYE
POSTER_TOKEN = 853931:71424838d41a70ee724e07ef6c6f0774
```

### 2. Создать Service Account в Google Cloud
Роли:
- Cloud Run Admin
- Storage Admin
- Cloud Build Editor
- Service Account User

### 3. Сделать commit и push
```bash
git add .
git commit -m "Fix deployment issues: resolve merge conflicts, switch to FastAPI"
git push origin main
```

## Проверка деплоя

1. GitHub Actions автоматически запустит деплой
2. Проверьте логи в разделе Actions
3. Проверьте статус сервиса в Google Cloud Console

## Структура приложения

- **main.py** - FastAPI приложение с webhook поддержкой
- **main_cloud.py** - старая версия с простым HTTP сервером (не используется)
- **Dockerfile** - использует `main.py` с uvicorn
- **cloudbuild.yaml** - для ручного деплоя через Cloud Build
- **.github/workflows/deploy.yml** - для автоматического деплоя через GitHub Actions

## Endpoints

После успешного деплоя будут доступны:
- `GET /` - health check
- `POST /webhook` - Telegram webhook
- `POST /set_webhook` - установка webhook
- `GET /get_webhook` - получение информации о webhook
