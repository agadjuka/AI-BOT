"""
Access Control Decorator for AI Bot
Provides @access_check decorator for controlling access to bot handlers
"""

import functools
from typing import Callable, Any, Optional
from telegram import Update
from telegram.ext import ContextTypes

from config.settings import BotConfig
from services.user_service import get_user_service
from config.locales.locale_manager import get_global_locale_manager


def access_check(func: Callable) -> Callable:
    """
    Декоратор для проверки прав доступа к хендлерам бота.
    
    Логика проверки:
    1. Проверка на админа (ADMIN_TELEGRAM_ID)
    2. Проверка существующего пользователя с ролью "user"
    3. Проверка по whitelist (если есть username)
    4. Отказ в доступе с локализованным сообщением
    
    Args:
        func: Функция-хендлер для обертывания
        
    Returns:
        Обернутая функция с проверкой доступа
    """
    @functools.wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[Any]:
        """
        Обертка для проверки доступа
        
        Args:
            self: Экземпляр класса
            update: Telegram Update объект
            context: Telegram Context объект
            
        Returns:
            Результат выполнения основной функции или None при отказе в доступе
        """
        # Получаем объект пользователя
        if not update.effective_user:
            print("❌ No user found in update")
            return None
            
        user = update.effective_user
        user_id = user.id
        username = user.username
        
        # Получаем конфигурацию и сервисы
        config = BotConfig()
        user_service = get_user_service()
        locale_manager = get_global_locale_manager()
        
        print(f"🔍 Checking access for user {user_id} (@{username})")
        
        # Шаг 1: Проверка на админа
        if user_id == config.ADMIN_TELEGRAM_ID:
            print(f"✅ User {user_id} is admin - access granted")
            return await func(self, update, context)
        
        # Шаг 2: Проверка существующего пользователя с ролью "user"
        has_user_role = await user_service.get_user_role(user_id)
        if has_user_role:
            print(f"✅ User {user_id} has user role - access granted")
            return await func(self, update, context)
        
        # Шаг 3: Проверка по whitelist (только если есть username)
        if username:
            # Приводим username к нижнему регистру и убираем @
            clean_username = username.lower().lstrip('@')
            
            # Проверяем, есть ли пользователь в whitelist
            is_whitelisted = await user_service.is_user_whitelisted(clean_username)
            
            if is_whitelisted:
                print(f"✅ User {user_id} (@{username}) is whitelisted - granting access")
                
                # Добавляем/обновляем пользователя в коллекции users с ролью "user"
                success = await user_service.set_user_role(user_id, "user")
                if success:
                    print(f"✅ User {user_id} added to users collection with role 'user'")
                else:
                    print(f"❌ Failed to add user {user_id} to users collection")
                
                # Удаляем пользователя из whitelist
                remove_success = await user_service.remove_from_whitelist(clean_username)
                if remove_success:
                    print(f"✅ User @{username} removed from whitelist")
                else:
                    print(f"❌ Failed to remove user @{username} from whitelist")
                
                # Выполняем основную функцию
                return await func(self, update, context)
        
        # Шаг 4: Отказ в доступе
        print(f"❌ Access denied for user {user_id} (@{username})")
        
        # Отправляем локализованное сообщение об отказе в доступе
        try:
            # Получаем язык пользователя из контекста
            user_language = locale_manager.get_language_from_context(context, update)
            
            # Формируем сообщение об отказе в доступе
            access_denied_message = locale_manager.get_text(
                "access_control.access_denied",
                context=context,
                language=user_language,
                update=update
            )
            
            # Отправляем сообщение пользователю
            await update.message.reply_text(access_denied_message)
            
        except Exception as e:
            print(f"❌ Error sending access denied message: {e}")
            
            # Fallback сообщение на русском языке
            fallback_message = (
                "Извините, у вас нет доступа к этому боту. "
                "Пожалуйста, свяжитесь с администратором @markov1u"
            )
            await update.message.reply_text(fallback_message)
        
        return None
    
    return wrapper


def admin_only(func: Callable) -> Callable:
    """
    Декоратор для проверки, что пользователь является администратором.
    
    Args:
        func: Функция-хендлер для обертывания
        
    Returns:
        Обернутая функция с проверкой админских прав
    """
    @functools.wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[Any]:
        """
        Обертка для проверки админских прав
        
        Args:
            self: Экземпляр класса
            update: Telegram Update объект
            context: Telegram Context объект
            
        Returns:
            Результат выполнения основной функции или None при отказе в доступе
        """
        # Получаем объект пользователя
        if not update.effective_user:
            print("❌ No user found in update")
            return None
            
        user_id = update.effective_user.id
        
        # Получаем конфигурацию
        config = BotConfig()
        
        # Проверяем, является ли пользователь администратором
        if user_id != config.ADMIN_TELEGRAM_ID:
            print(f"❌ User {user_id} is not admin - access denied")
            
            # Отправляем сообщение об отказе в доступе
            try:
                locale_manager = get_global_locale_manager()
                user_language = locale_manager.get_language_from_context(context, update)
                
                admin_only_message = locale_manager.get_text(
                    "access_control.admin_only",
                    context=context,
                    language=user_language,
                    update=update
                )
                
                await update.message.reply_text(admin_only_message)
                
            except Exception as e:
                print(f"❌ Error sending admin only message: {e}")
                
                # Fallback сообщение
                fallback_message = "Эта команда доступна только администратору."
                await update.message.reply_text(fallback_message)
            
            return None
        
        print(f"✅ User {user_id} is admin - access granted")
        return await func(self, update, context)
    
    return wrapper
