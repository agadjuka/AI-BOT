# Testing Role System

## Тестирование системы ролей

### 1. Запуск тестов
```bash
python test_role_system.py
```

### 2. Что тестируется

#### ✅ Инициализация ролей
- Создание документа администратора
- Назначение роли "admin" администратору
- Инициализация системы ролей

#### ✅ Операции с whitelist
- Добавление пользователя в whitelist
- Проверка наличия пользователя в whitelist
- Получение списка пользователей в whitelist
- Удаление пользователя из whitelist

#### ✅ Проверка разрешений
- Проверка прав администратора
- Проверка прав пользователя из whitelist
- Проверка прав обычного пользователя

#### ✅ Структура данных Firestore
- Проверка коллекции `users`
- Проверка коллекции `whitelist`
- Валидация структуры документов

### 3. Ожидаемые результаты

```
🧪 Testing Role System...
✅ Firestore connected

🔧 Test 1: Initialize roles and permissions
✅ Role initialization successful

👤 Test 2: Get user service
✅ User service created

🔍 Test 3: Check admin role
Admin 261617302 role: admin
Is admin: True

📋 Test 4: Test whitelist operations
Added test_user to whitelist: True
Is test_user whitelisted: True
Whitelist: ['test_user']

🔐 Test 5: Test permission checking
Admin permissions: {'is_admin': True, 'is_whitelisted': False, 'has_access': True}
Whitelisted user permissions: {'is_admin': False, 'is_whitelisted': True, 'has_access': True}
Regular user permissions: {'is_admin': False, 'is_whitelisted': False, 'has_access': False}

📊 Test 6: Test user info
Admin user info: {'role': 'admin', 'user_id': 261617302}

🧹 Test 7: Clean up whitelist
Removed test_user from whitelist: True
Is test_user still whitelisted: False

✅ Role system test completed!

🗄️ Testing Firestore Collections...
📁 Testing users collection...
Found 1 users in collection
  - User 261617302: {'role': 'admin'}

📁 Testing whitelist collection...
Found 0 users in whitelist

✅ Firestore collections test completed!

🎉 All tests completed!
```

### 4. Устранение неполадок

#### Ошибка подключения к Firestore
```
❌ Firestore connection failed: ...
```
**Решение:** Проверьте настройки Google Cloud и переменные окружения

#### Ошибка инициализации ролей
```
❌ Role initialization failed
```
**Решение:** Проверьте права доступа к Firestore и настройки проекта

#### Ошибка операций с whitelist
```
❌ Error adding to whitelist: ...
```
**Решение:** Проверьте подключение к Firestore и права доступа

### 5. Ручное тестирование в боте

#### Тест доступа администратора
1. Запустите бота
2. Отправьте `/start` от имени администратора
3. Должен появиться приветственный экран

#### Тест доступа пользователя из whitelist
1. Добавьте пользователя в whitelist: `/add_whitelist username`
2. Отправьте `/start` от имени этого пользователя
3. Должен появиться приветственный экран

#### Тест отказа в доступе
1. Отправьте `/start` от имени пользователя не из whitelist
2. Должно появиться сообщение "Access Denied"

#### Тест команд администратора
1. Отправьте `/admin` от имени администратора
2. Должна появиться панель администратора
3. Протестируйте команды whitelist

### 6. Проверка логов

При успешной работе в логах должны быть:
```
✅ Firestore клиент инициализирован успешно (база: billscaner)
🔧 Initializing roles and permissions...
✅ Admin role initialized for user 261617302
✅ Roles and permissions initialization completed
✅ UserService предзагружен с Firestore
```

### 7. Проверка данных в Firestore

#### В коллекции `users`:
```json
{
  "261617302": {
    "role": "admin"
  }
}
```

#### В коллекции `whitelist`:
```
Документы с ID = username пользователей
```
