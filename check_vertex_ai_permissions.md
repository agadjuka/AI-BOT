# Проверка прав Service Account для Vertex AI

## Нужные роли для Service Account:

1. **Vertex AI User** (`roles/aiplatform.user`)
2. **Vertex AI Service Agent** (`roles/aiplatform.serviceAgent`)
3. **Storage Admin** (`roles/storage.admin`) - уже есть
4. **Cloud Run Admin** (`roles/cloudrun.admin`) - уже есть

## Команды для проверки:

```bash
# Проверьте текущие роли
gcloud projects get-iam-policy YOUR_PROJECT_ID \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com"

# Добавьте права на Vertex AI
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.serviceAgent"
```

## Или через Google Cloud Console:

1. **IAM & Admin → IAM**
2. **Найдите** `github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com`
3. **Добавьте роли**:
   - `Vertex AI User`
   - `Vertex AI Service Agent`
