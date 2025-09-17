"""
Обработчик настроек таблиц
Позволяет пользователям настраивать отображение таблиц
"""
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.base_callback_handler import BaseCallbackHandler
from config.table_config import TableType, DeviceType, TableConfig, ColumnConfig, TableStyle
from utils.table_manager import TableManager
from services.user_service import get_user_service


class TableSettingsHandler(BaseCallbackHandler):
    """Обработчик настроек таблиц"""
    
    def __init__(self, config, analysis_service):
        super().__init__(config, analysis_service)
        self.table_manager = TableManager(self.locale_manager)
    
    async def show_table_settings_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Показывает главное меню настроек таблиц"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        # Получаем сохраненную настройку пользователя
        try:
            user_service = get_user_service()
            display_mode = await user_service.get_user_display_mode(user_id)
            
            # Конвертируем display_mode в DeviceType
            if display_mode == "desktop":
                device_type = DeviceType.DESKTOP
            else:
                device_type = DeviceType.MOBILE
        except Exception as e:
            print(f"❌ Error getting user display mode: {e}")
            device_type = DeviceType.MOBILE
        
        # Сохраняем тип устройства в контексте
        context.user_data['device_type'] = device_type.value
        
        text = self.get_text("table_settings.menu.title", context)
        text += f"\n\n📱 **Текущее устройство:** {device_type.value.upper()}"
        
        keyboard = [
            [InlineKeyboardButton(
                self.get_text("table_settings.menu.ingredient_matching", context),
                callback_data="table_settings_ingredient_matching"
            )],
            [InlineKeyboardButton(
                self.get_text("table_settings.menu.google_sheets", context),
                callback_data="table_settings_google_sheets"
            )],
            [InlineKeyboardButton(
                self.get_text("table_settings.menu.receipt_preview", context),
                callback_data="table_settings_receipt_preview"
            )],
            [InlineKeyboardButton(
                self.get_text("table_settings.menu.next_items", context),
                callback_data="table_settings_next_items"
            )],
            [InlineKeyboardButton(
                self.get_text("table_settings.menu.device_type", context),
                callback_data="table_settings_device_type"
            )],
            [InlineKeyboardButton(
                self.get_text("table_settings.menu.reset_all", context),
                callback_data="table_settings_reset_all"
            )],
            [InlineKeyboardButton(
                self.get_text("buttons.back", context),
                callback_data="back_to_dashboard"
            )]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        return self.config.AWAITING_DASHBOARD
    
    async def show_table_type_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE, table_type: TableType) -> int:
        """Показывает настройки для конкретного типа таблицы"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        device_type = DeviceType(context.user_data.get('device_type', 'mobile'))
        
        # Получаем текущую конфигурацию
        current_config = self.table_manager.get_user_table_settings(user_id).get(
            f"{table_type.value}_{device_type.value}"
        )
        
        if not current_config:
            current_config = self.table_manager.config_manager.get_config(table_type, device_type)
        
        text = f"**Настройки таблицы: {table_type.value}**\n\n"
        text += f"📱 **Устройство:** {device_type.value.upper()}\n"
        text += f"📏 **Максимальная длина названия:** {current_config.style.max_name_length}\n"
        text += f"📄 **Элементов на странице:** {current_config.max_items_per_page}\n"
        text += f"🎨 **Компактный режим:** {'Да' if current_config.style.compact_mode else 'Нет'}\n"
        text += f"📊 **Показывать эмодзи:** {'Да' if current_config.style.use_emojis else 'Нет'}\n"
        
        keyboard = [
            [InlineKeyboardButton(
                f"📏 Длина названия: {current_config.style.max_name_length}",
                callback_data=f"table_settings_{table_type.value}_max_length"
            )],
            [InlineKeyboardButton(
                f"📄 Элементов на странице: {current_config.max_items_per_page}",
                callback_data=f"table_settings_{table_type.value}_items_per_page"
            )],
            [InlineKeyboardButton(
                f"🎨 Компактный режим: {'Да' if current_config.style.compact_mode else 'Нет'}",
                callback_data=f"table_settings_{table_type.value}_compact_mode"
            )],
            [InlineKeyboardButton(
                f"📊 Эмодзи: {'Да' if current_config.style.use_emojis else 'Нет'}",
                callback_data=f"table_settings_{table_type.value}_emojis"
            )],
            [InlineKeyboardButton(
                "🔄 Сбросить к стандартным",
                callback_data=f"table_settings_{table_type.value}_reset"
            )],
            [InlineKeyboardButton(
                self.get_text("buttons.back", context),
                callback_data="table_settings_menu"
            )]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        return self.config.AWAITING_DASHBOARD
    
    async def update_table_setting(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                 table_type: TableType, setting: str) -> int:
        """Обновляет настройку таблицы"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        device_type = DeviceType(context.user_data.get('device_type', 'mobile'))
        
        # Получаем текущую конфигурацию
        current_config = self.table_manager.get_user_table_settings(user_id).get(
            f"{table_type.value}_{device_type.value}"
        )
        
        if not current_config:
            current_config = self.table_manager.config_manager.get_config(table_type, device_type)
        
        # Создаем копию конфигурации для изменения
        new_config = TableConfig(
            table_type=current_config.table_type,
            device_type=current_config.device_type,
            columns=current_config.columns.copy(),
            style=TableStyle(
                max_name_length=current_config.style.max_name_length,
                show_separators=current_config.style.show_separators,
                use_emojis=current_config.style.use_emojis,
                compact_mode=current_config.style.compact_mode,
                show_row_numbers=current_config.style.show_row_numbers,
                header_style=current_config.style.header_style
            ),
            title=current_config.title,
            description=current_config.description,
            max_items_per_page=current_config.max_items_per_page,
            show_pagination=current_config.show_pagination,
            custom_formatter=current_config.custom_formatter
        )
        
        # Обновляем настройку
        if setting == "max_length":
            # Циклически переключаем длину названия
            lengths = [10, 15, 20, 25, 30]
            current_length = new_config.style.max_name_length
            try:
                current_index = lengths.index(current_length)
                new_index = (current_index + 1) % len(lengths)
            except ValueError:
                new_index = 0
            new_config.style.max_name_length = lengths[new_index]
            
        elif setting == "items_per_page":
            # Циклически переключаем количество элементов
            counts = [5, 8, 10, 15, 20]
            current_count = new_config.max_items_per_page
            try:
                current_index = counts.index(current_count)
                new_index = (current_index + 1) % len(counts)
            except ValueError:
                new_index = 0
            new_config.max_items_per_page = counts[new_index]
            
        elif setting == "compact_mode":
            new_config.style.compact_mode = not new_config.style.compact_mode
            
        elif setting == "emojis":
            new_config.style.use_emojis = not new_config.style.use_emojis
        
        # Сохраняем обновленную конфигурацию
        self.table_manager.update_user_table_settings(user_id, table_type, device_type, new_config)
        
        # Показываем обновленные настройки
        return await self.show_table_type_settings(update, context, table_type)
    
    async def reset_table_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE, table_type: TableType) -> int:
        """Сбрасывает настройки таблицы к стандартным"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        device_type = DeviceType(context.user_data.get('device_type', 'mobile'))
        
        # Сбрасываем настройки
        self.table_manager.reset_user_table_settings(user_id, table_type, device_type)
        
        # Показываем обновленные настройки
        return await self.show_table_type_settings(update, context, table_type)
    
    async def show_device_type_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Показывает настройки типа устройства"""
        query = update.callback_query
        await query.answer()
        
        current_device = context.user_data.get('device_type', 'mobile')
        
        text = f"**Настройки устройства**\n\n"
        text += f"📱 **Текущее устройство:** {current_device.upper()}\n\n"
        text += "Выберите тип устройства для оптимизации отображения таблиц:\n\n"
        text += "• **Мобильное** - компактные таблицы для маленьких экранов\n"
        text += "• **Планшет** - средние таблицы для средних экранов\n"
        text += "• **Десктоп** - полные таблицы для больших экранов"
        
        keyboard = [
            [InlineKeyboardButton(
                f"📱 Мобильное {'✅' if current_device == 'mobile' else ''}",
                callback_data="table_settings_device_mobile"
            )],
            [InlineKeyboardButton(
                f"📱 Планшет {'✅' if current_device == 'tablet' else ''}",
                callback_data="table_settings_device_tablet"
            )],
            [InlineKeyboardButton(
                f"💻 Десктоп {'✅' if current_device == 'desktop' else ''}",
                callback_data="table_settings_device_desktop"
            )],
            [InlineKeyboardButton(
                self.get_text("buttons.back", context),
                callback_data="table_settings_menu"
            )]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        return self.config.AWAITING_DASHBOARD
    
    async def set_device_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE, device_type: DeviceType) -> int:
        """Устанавливает тип устройства"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        # Сохраняем тип устройства в контексте
        context.user_data['device_type'] = device_type.value
        
        # Сохраняем настройку в Firestore
        try:
            user_service = get_user_service()
            display_mode = "desktop" if device_type == DeviceType.DESKTOP else "mobile"
            success = await user_service.set_user_display_mode(user_id, display_mode)
            
            if success:
                print(f"✅ Updated user {user_id} display mode to {display_mode}")
            else:
                print(f"❌ Failed to update user {user_id} display mode")
        except Exception as e:
            print(f"❌ Error setting user display mode: {e}")
        
        # Показываем обновленные настройки
        return await self.show_device_type_settings(update, context)
    
    async def reset_all_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Сбрасывает все настройки таблиц"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        # Сбрасываем все пользовательские настройки
        for table_type in TableType:
            for device_type in DeviceType:
                self.table_manager.reset_user_table_settings(user_id, table_type, device_type)
        
        # Сбрасываем тип устройства в контексте
        context.user_data.pop('device_type', None)
        
        # Сбрасываем настройку в Firestore (устанавливаем мобильный режим по умолчанию)
        try:
            user_service = get_user_service()
            success = await user_service.set_user_display_mode(user_id, "mobile")
            
            if success:
                print(f"✅ Reset user {user_id} display mode to mobile")
            else:
                print(f"❌ Failed to reset user {user_id} display mode")
        except Exception as e:
            print(f"❌ Error resetting user display mode: {e}")
        
        text = "✅ Все настройки таблиц сброшены к стандартным значениям!"
        
        keyboard = [
            [InlineKeyboardButton(
                self.get_text("buttons.back", context),
                callback_data="table_settings_menu"
            )]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        return self.config.AWAITING_DASHBOARD
