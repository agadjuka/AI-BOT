# 🚀 Быстрый деплой AI Bot в Google Cloud Run

## Готовые файлы для деплоя:

✅ **Dockerfile** - конфигурация контейнера  
✅ **main_cloud.py** - адаптированная версия для Cloud Run  
✅ **deploy.ps1** - скрипт деплоя для Windows  
✅ **deploy.sh** - скрипт деплоя для Linux/macOS  
✅ **cloudbuild.yaml** - конфигурация автоматической сборки  
✅ **app.yaml** - конфигурация Cloud Run  

## 🎯 Быстрый старт:

### 1. Установите Google Cloud SDK
Скачайте с [cloud.google.com/sdk](https://cloud.google.com/sdk/docs/install)

### 2. Авторизуйтесь
```powershell
gcloud auth login
gcloud config set project just-advice-470905-a3
```

### 3. Запустите деплой
```powershell
.\deploy.ps1
```

## 🔧 Что изменилось для Cloud Run:

1. **Добавлен HTTP сервер** на порту 8080 для health checks
2. **Переменные окружения** вместо hardcoded токенов
3. **Polling режим** вместо webhook (лучше для Cloud Run)
4. **Автоматическое масштабирование** от 0 до 10 экземпляров

## 📊 После деплоя:

- **URL сервиса** будет показан в консоли
- **Логи**: `gcloud logs tail --follow --service=ai-bot --region=us-central1`
- **Статус**: `gcloud run services describe ai-bot --region=us-central1`

## ⚠️ Важно:

- Все токены уже настроены в скриптах
- Функционал бота остался **полностью неизменным**
- Добавлен только HTTP сервер для Cloud Run
- Бот будет работать точно так же, как и раньше

## 🆘 Если что-то не работает:

1. Проверьте логи: `gcloud logs tail --follow --service=ai-bot --region=us-central1`
2. Убедитесь, что API включены: `gcloud services enable cloudbuild.googleapis.com run.googleapis.com`
3. Проверьте авторизацию: `gcloud auth list`

**Готово к деплою! 🎉**
