# Исправление ошибки numpy/pandas совместимости

## Проблема
```
ValueError: numpy.dtype size changed, may indicate binary incompatibility. 
Expected 96 from C header, got 88 from PyObject
```

## Причина
Несовместимость версий numpy и pandas с Python 3.11. Pandas 1.5.3 был скомпилирован для более старых версий Python.

## Исправления

### ✅ 1. Обновлен requirements.txt
- Заменены фиксированные версии на совместимые диапазоны
- Добавлен numpy>=1.24.0,<2.0.0
- Обновлен pandas>=2.0.0,<3.0.0

### ✅ 2. Создан requirements-stable.txt
- Фиксированные стабильные версии для Python 3.11
- numpy==1.24.3
- pandas==2.0.3

### ✅ 3. Обновлен Dockerfile
- Добавлена переменная NUMPY_DISABLE_THREADING=1
- Улучшен порядок установки зависимостей
- Используется requirements-stable.txt

### ✅ 4. Добавлена проверка в main.py
- Проверка версий numpy/pandas при запуске
- Логирование версий для диагностики

## Файлы изменены

1. **requirements.txt** - обновлены версии
2. **requirements-stable.txt** - создан с фиксированными версиями
3. **Dockerfile** - улучшена установка зависимостей
4. **main.py** - добавлена проверка совместимости

## Тестирование

### 1. Локальное тестирование (опционально)
```bash
# Создать виртуальное окружение
python -m venv test_env
test_env\Scripts\activate  # Windows
# test_env/bin/activate    # Linux/Mac

# Установить зависимости
pip install -r requirements-stable.txt

# Проверить версии
python -c "import numpy; import pandas; print(f'numpy: {numpy.__version__}, pandas: {pandas.__version__}')"
```

### 2. Деплой на Cloud Run
```bash
# Сделать commit изменений
git add .
git commit -m "Fix numpy/pandas compatibility for Python 3.11"
git push origin main

# GitHub Actions автоматически запустит деплой
```

### 3. Проверка деплоя
1. Перейдите в GitHub Actions в вашем репозитории
2. Проверьте статус последнего workflow
3. Если успешно - проверьте Cloud Run в Google Cloud Console
4. Проверьте логи контейнера на предмет ошибок

## Ожидаемый результат

После исправления:
- ✅ Контейнер должен запуститься без ошибок numpy/pandas
- ✅ Приложение должно слушать на порту 8080
- ✅ Health check должен проходить успешно
- ✅ В логах должны быть версии: numpy 1.24.3, pandas 2.0.3

## Если проблема остается

1. **Проверьте логи Cloud Run** - должны быть версии numpy/pandas
2. **Очистите кэш Docker** - пересоберите образ с нуля
3. **Проверьте переменные окружения** - убедитесь, что все секреты настроены

## Дополнительные улучшения

Если нужно еще больше стабильности:
1. Можно зафиксировать все версии в requirements-stable.txt
2. Можно добавить проверку совместимости в CI/CD
3. Можно использовать poetry или pipenv для управления зависимостями
