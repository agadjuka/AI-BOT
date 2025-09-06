"""
Configuration settings for the AI Bot
"""
import os
from typing import Optional


class BotConfig:
    """Bot configuration settings"""
    
    def __init__(self):
        # Bot settings
        self.BOT_TOKEN: str = "8291213805:AAEHDlkDCHLQ3RFtrB5HLMeU-nGzF1hOZYE"
        self.PHOTO_FILE_NAME: str = "last_photo.jpg"
        
        # Poster settings
        self.POSTER_TOKEN: str = "853931:71424838d41a70ee724e07ef6c6f0774"
        
        # Google Sheets settings
        self.GOOGLE_SHEETS_CREDENTIALS: str = "google_sheets_credentials.json"  # Путь к файлу credentials.json
        self.GOOGLE_SHEETS_SPREADSHEET_ID: str = "1ah85v40ZqJzTz8PGHO6Ndoctw378NOYATH9X3OeeuUI"  # ID таблицы Google Sheets
        self.GOOGLE_SHEETS_WORKSHEET_NAME: str = "Лист1"  # Название листа
        
        # Ingredient matching settings
        self.INGREDIENT_LIST: dict = {
            "potato wedges": "potato_wedges_001",
            "chicken": "chicken_002",
            "salmon": "salmon_003",
            "shrimps": "shrimps_004",
            "yogurt": "yogurt_005",
            "mozza cheese": "mozza_cheese_006",
            "feta cheese": "feta_cheese_007",
            "avocado": "avocado_008",
            "carrot": "carrot_009",
            "cucumber": "cucumber_010",
            "cabbage red": "cabbage_red_011",
            "cabbage white": "cabbage_white_012",
            "tomato": "tomato_013",
            "parsley": "parsley_014",
            "dill": "dill_015",
            "garlic": "garlic_016",
            "french fries": "french_fries_017",
            "salt": "salt_018",
            "sugar": "sugar_019",
            "dumplings": "dumplings_020",
            "flour": "flour_021",
            "sour cream": "sour_cream_022",
            "coconut cream": "coconut_cream_023",
            "tom yum sauce": "tom_yum_sauce_024",
            "tomato sauce": "tomato_sauce_025",
            "tea black": "tea_black_026",
            "bimoil frying": "bimoil_frying_027",
            "salad oil": "salad_oil_028",
            "lettuce": "lettuce_029",
            "mayonnaise": "mayonnaise_030",
            "lemon": "lemon_031",
            "pickles": "pickles_032"
        }
        
        # Google Cloud settings
        self.PROJECT_ID: str = "just-advice-470905-a3"
        self.LOCATION: str = "us-central1"
        self.MODEL_NAME: str = "gemini-2.5-flash"
        
        # Conversation states
        self.AWAITING_CORRECTION = 0
        self.AWAITING_INPUT = 1
        self.AWAITING_LINE_NUMBER = 2
        self.AWAITING_FIELD_EDIT = 3
        self.AWAITING_DELETE_LINE_NUMBER = 4
        self.AWAITING_TOTAL_EDIT = 5
        self.AWAITING_INGREDIENT_MATCHING = 6
        self.AWAITING_MANUAL_MATCH = 7
        
        # Message settings
        self.MAX_MESSAGE_LENGTH = 4096
        self.MESSAGE_DELAY = 0.5


class PromptConfig:
    """AI prompts configuration"""
    
    PROMPT_ANALYZE = """
Извлеки данные из чека в JSON. КОПИРУЙ ТОЧНО - не вычисляй.

ПРАВИЛА:
- Пустое место → null
- Нечитаемо → "???"
- Индонезийские названия → английский (сохрани единицы: кг,г,л,мл)
- Числа в JSON: 125000 (не 125 000)

ОСОБОЕ ПРАВИЛО ДЛЯ НЕОПОЗНАННЫХ ПРОДУКТОВ:
- Если не можешь идентифицировать продукт как конкретное наименование, найди в интернете что это такое
- После названия бренда в скобках укажи что это за продукт НА АНГЛИЙСКОМ ЯЗЫКЕ
- Пример: "Dine FF Crinkle" → "Dine FF Crinkle (French Fries)"
- Пример: "Mama Tom Yam" → "Mama Tom Yam (Instant Noodles)"

СТРОКИ:
1. С цифрами: name(английский+единицы), quantity, price, total, status
2. Только текст: name(английский), quantity=null, price=null, total=null, status="needs_review"  
3. Нечитаемо: name="???", остальное=null, status="needs_review"
4. Пустая строка: НЕ включать

JSON:
```json
{
  "items": [
    {
      "line_number": 1,
      "name": "название на английском",
      "quantity": число_или_null,
      "price": число_или_null,
      "total": число_или_null,
      "status": "confirmed/error/needs_review"
    }
  ],
  "grand_total_text": "итоговая_сумма"
}
```
"""

# Промпт для второго этапа: форматирование готовых данных (оптимизированный для мобильных устройств)
PROMPT_FORMAT = """
Оформи данные чека в таблицу для Telegram (моноширинный шрифт).

ПРАВИЛА:
- null → пустая ячейка (пробелы)
- НЕ вычисляй недостающие значения
- Российский формат чисел: 125 000 (пробел для тысяч)

ТАБЛИЦА:
№| Товар      |Кол | Цена      |    Сумма | 
───────────────────────────────────────────
1| Название   |кол-во| цена    |   сумма  | ✅/🔴/⚠️

СТАТУСЫ:
- ✅: все данные есть, расчет совпадает
- 🔴: все данные есть, расчет НЕ совпадает  
- ⚠️: есть null значения

ИТОГ: сумма по полным позициям + сравнение с grand_total_text

Данные:
"""

# Poster API token
POSTER_TOKEN = "853931:71424838d41a70ee724e07ef6c6f0774"
