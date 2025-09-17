"""
Утилиты для безопасной обработки callback queries
"""
from telegram.error import BadRequest


async def safe_callback_answer(query, text: str = None, show_alert: bool = False):
    """
    Безопасно отвечает на callback query с обработкой устаревших запросов
    
    Args:
        query: CallbackQuery объект
        text: Текст ответа (опционально)
        show_alert: Показывать ли alert (по умолчанию False)
    
    Returns:
        None - функция не поднимает исключения для устаревших запросов
    """
    try:
        await query.answer(text=text, show_alert=show_alert)
    except BadRequest as e:
        if "Query is too old" in str(e) or "query id is invalid" in str(e):
            print(f"⚠️ Callback query устарел или недействителен: {e}")
            # Не поднимаем исключение, просто логируем
        else:
            # Для других ошибок BadRequest поднимаем исключение
            raise e


async def safe_edit_message(query, text: str = None, reply_markup=None, parse_mode=None):
    """
    Безопасно редактирует сообщение с обработкой устаревших запросов
    
    Args:
        query: CallbackQuery объект
        text: Новый текст сообщения
        reply_markup: Новая клавиатура (опционально)
        parse_mode: Режим парсинга (опционально)
    
    Returns:
        None - функция не поднимает исключения для устаревших запросов
    """
    try:
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except BadRequest as e:
        if "Query is too old" in str(e) or "query id is invalid" in str(e):
            print(f"⚠️ Callback query устарел при редактировании сообщения: {e}")
            # Не поднимаем исключение, просто логируем
        else:
            # Для других ошибок BadRequest поднимаем исключение
            raise e
