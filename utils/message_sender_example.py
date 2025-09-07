"""
Пример использования MessageSender
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config.settings import BotConfig
from utils.message_sender import MessageSender


class MessageSenderExample:
    """Пример использования MessageSender в обработчиках"""
    
    def __init__(self):
        self.config = BotConfig()
        self.message_sender = MessageSender(self.config)
    
    async def example_success_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Пример успешного выполнения операции"""
        try:
            # Имитируем выполнение операции
            await self.message_sender.send_processing_message(
                update, context, 
                "Обрабатываю данные...", 
                duration=3
            )
            
            # Имитируем задержку
            import asyncio
            await asyncio.sleep(2)
            
            # Отправляем сообщение об успехе
            await self.message_sender.send_success_message(
                update, context, 
                "Данные успешно обработаны!"
            )
            
        except Exception as e:
            # Отправляем сообщение об ошибке
            await self.message_sender.send_error_message(
                update, context, 
                self.message_sender.format_error_message(e, "При обработке данных")
            )
    
    async def example_error_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Пример обработки ошибки"""
        try:
            # Имитируем ошибку
            raise ValueError("Тестовая ошибка")
            
        except Exception as e:
            # Отправляем сообщение об ошибке
            await self.message_sender.send_error_message(
                update, context, 
                self.message_sender.format_error_message(e, "При выполнении тестовой операции")
            )
    
    async def example_long_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Пример отправки длинного сообщения с клавиатурой"""
        # Создаем длинный текст
        long_text = "Это очень длинное сообщение. " * 100  # Создаем длинный текст
        
        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Продолжить", callback_data="continue")],
            [InlineKeyboardButton("Отмена", callback_data="cancel")]
        ])
        
        # Отправляем длинное сообщение с клавиатурой
        await self.message_sender.send_long_message_with_keyboard(
            update, context, 
            long_text, 
            keyboard
        )
    
    async def example_info_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Пример отправки различных типов сообщений"""
        # Информационное сообщение
        await self.message_sender.send_info_message(
            update, context, 
            "Это информационное сообщение с полезной информацией."
        )
        
        # Предупреждение
        await self.message_sender.send_warning_message(
            update, context, 
            "Внимание! Проверьте данные перед продолжением.",
            "Убедитесь, что все поля заполнены корректно."
        )
        
        # Подтверждение
        await self.message_sender.send_confirmation_message(
            update, context, 
            "Операция подтверждена и выполнена успешно."
        )
    
    async def example_formatted_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Пример использования методов форматирования"""
        # Форматированное сообщение об успехе
        success_text = self.message_sender.format_success_message(
            "Сохранение данных", 
            "Все изменения были успешно сохранены в базу данных."
        )
        await self.message_sender.send_temp_message(update, context, success_text)
        
        # Форматированное информационное сообщение
        info_text = self.message_sender.format_info_message(
            "Статистика обработки", 
            "Обработано 150 записей за 2.5 секунды."
        )
        await self.message_sender.send_temp_message(update, context, info_text)
        
        # Форматированное предупреждение
        warning_text = self.message_sender.format_warning_message(
            "Обнаружены дублирующиеся записи", 
            "Рекомендуется проверить данные перед сохранением."
        )
        await self.message_sender.send_temp_message(update, context, warning_text)


# Пример использования в реальном обработчике
async def example_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пример обработчика, использующего MessageSender"""
    example = MessageSenderExample()
    
    # Выбираем тип примера на основе callback_data
    if hasattr(update, 'callback_query') and update.callback_query:
        action = update.callback_query.data
        
        if action == "success_example":
            await example.example_success_flow(update, context)
        elif action == "error_example":
            await example.example_error_flow(update, context)
        elif action == "long_message_example":
            await example.example_long_message(update, context)
        elif action == "info_messages_example":
            await example.example_info_messages(update, context)
        elif action == "formatted_messages_example":
            await example.example_formatted_messages(update, context)
        else:
            await example.message_sender.send_error_message(
                update, context, 
                "Неизвестное действие"
            )
