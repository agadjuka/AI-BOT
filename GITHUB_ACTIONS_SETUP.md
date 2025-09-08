# Настройка автоматического деплоя через GitHub Actions

## Проблема
У вас была ошибка в Dockerfile из-за неразрешенного конфликта слияния Git (merge conflict). Docker не мог распарсить первую строку с `<<<<<<< HEAD`.

## Что исправлено
1. ✅ Убран конфликт слияния из `Dockerfile`
2. ✅ Убран конфликт слияния из `cloudbuild.yaml`
3. ✅ Создан GitHub Actions workflow файл `.github/workflows/deploy.yml`

## Настройка GitHub Actions

### 1. Создание Service Account в Google Cloud

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Выберите ваш проект `just-advice-470905-a3`
3. Перейдите в IAM & Admin → Service Accounts
4. Нажмите "Create Service Account"
5. Назовите его `github-actions-deploy`
6. Добавьте следующие роли:
   - Cloud Run Admin
   - Storage Admin
   - Cloud Build Editor
   - Service Account User
7. Создайте ключ (JSON) и скачайте его

### 2. Настройка GitHub Secrets

В вашем GitHub репозитории:
1. Перейдите в Settings → Secrets and variables → Actions
2. Добавьте следующие secrets:

```
GCP_PROJECT_ID = just-advice-470905-a3
GCP_SA_KEY = <содержимое скачанного JSON файла>
```

### 3. Активация API

Убедитесь, что в Google Cloud включены следующие API:
- Cloud Run API
- Cloud Build API
- Container Registry API

### 4. Тестирование

После настройки:
1. Сделайте commit и push изменений
2. GitHub Actions автоматически запустит деплой
3. Проверьте логи в разделе Actions вашего репозитория

## Альтернативный способ - через Cloud Build

Если хотите использовать Cloud Build вместо GitHub Actions:

1. Подключите репозиторий к Cloud Build
2. Создайте trigger для автоматической сборки при push в main ветку
3. Используйте исправленный `cloudbuild.yaml`

## Структура файлов

```
.github/
  workflows/
    deploy.yml          # GitHub Actions workflow
Dockerfile              # Исправлен (убран merge conflict)
cloudbuild.yaml         # Исправлен (убран merge conflict)
```

## Команды для проверки

```bash
# Проверить Dockerfile
docker build -t test-image .

# Проверить cloudbuild.yaml
gcloud builds submit --config cloudbuild.yaml .
```
