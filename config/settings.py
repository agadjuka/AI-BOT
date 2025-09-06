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
Ты — высокоточный сканер документов. Твоя задача — извлечь данные из чека в формат JSON, КОПИРУЯ их АБСОЛЮТНО ТОЧНО.

**ЗОЛОТОЕ ПРАВИЛО: НЕ ДУМАЙ, А КОПИРУЙ.**
- ВИДИШЬ ПУСТОЕ МЕСТО НА ФОТО → `null` в JSON.
- НЕ МОЖЕШЬ ПРОЧИТАТЬ → `???` в JSON.
- НИКОГДА, НИ ПРИ КАКИХ УСЛОВИЯХ не вычисляй, не дополняй и не угадывай данные.

**ВАЖНО ДЛЯ НАЗВАНИЙ ТОВАРОВ:**
- Если название товара на индонезийском языке, переведи его на английский язык
- Переводи только наименование товара, но ОБЯЗАТЕЛЬНО сохраняй единицы измерения (кг, г, л, мл и т.д.)
- Пример: "свежий томат 1кг" → "Fresh Tomato 1kg"
- Пример: "TIMUN 500г" → "Cucumber 500g"
- Пример: "WORTEL 2кг" → "Carrot 2kg"
- Пример: "TOMAT 1л" → "Tomato 1l"
- Пример: "MILK 500мл" → "Milk 500ml"

**АЛГОРИТМ РАБОТЫ:**

1.  **ВНУТРЕННИЙ АНАЛИЗ (про себя, не показывая в ответе):**
    - Просканируй изображение сверху вниз, строка за строкой.
    - Для каждой строки определи, к какому из сценариев ниже она относится.
    - Запиши свои рассуждения.

2.  **ГЕНЕРАЦИЯ JSON на основе анализа:**

**СЦЕНАРИИ ОБРАБОТКИ СТРОК:**

*   **СЦЕНАРИЙ 1: СТРОКА С ЦИФРАМИ.** (Есть хотя бы одно число: кол-во, цена или сумма)
    - name: Текст товара, переведенный на английский если нужно, С ОБЯЗАТЕЛЬНЫМ СОХРАНЕНИЕМ единиц измерения (кг, г, л, мл). Если нечитаем -> "???".
    - quantity: Число из фото. Если ячейка пуста -> null.
    - price: Число из фото. Если ячейка пуста -> null.
    - total: Число из фото. Если ячейка пуста -> null.
    - status: Определи по правилам ("confirmed", "error", "needs_review").

*   **СЦЕНАРИЙ 2: СТРОКА ТОЛЬКО С ТЕКСТОМ.** (Нет цифр, но есть читаемый текст, например "Cari roti tawar")
    - name: Распознанный текст, переведенный на английский если нужно.
    - quantity: null
    - price: null
    - total: null
    - status: "needs_review"

*   **СЦЕНАРИЙ 3: НЕЧИТАЕМАЯ СТРОКА.** (Невозможно разобрать ни слова, ни цифры)
    - name: "???"
    - quantity: null
    - price: null
    - total: null
    - status: "needs_review"

*   **СЦЕНАРИЙ 4: ПОЛНОСТЬЮ ПУСТАЯ СТРОКА.**
    - НЕ включай ее в итоговый JSON.

**ФИНАЛЬНАЯ ПРОВЕРКА:**
- Убедись, что каждая ячейка, пустая на фото, имеет значение `null` в JSON.
- Убедись, что ты не пропустил ни одной строки с текстом или цифрами.
- Убедись, что все названия товаров переведены на английский язык.
- Убедись, что единицы измерения (кг, г, л, мл, кг, г, л, мл) сохранены в названиях товаров.

Верни ТОЛЬКО JSON в следующем формате:
```json
{
  "items": [
    {
      "line_number": 1,
      "name": "название товара на английском",
      "quantity": число_или_null,
      "price": число_или_null,
      "total": число_или_null,
      "status": "confirmed/error/needs_review"
    }
  ],
  "grand_total_text": "итоговая_сумма_из_чека"
}
```

БЕЗ дополнительного текста и рассуждений.
"""

# Промпт для второго этапа: форматирование готовых данных (оптимизированный для мобильных устройств)
PROMPT_FORMAT = """
Ты — финансовый ассистент. Тебе предоставлены финальные, проверенные данные из чека в формате JSON.
Твоя задача — красиво оформить их в виде отчета для Telegram с выровненными столбцами, оптимизированными для мобильных устройств.

**ВАЖНО:** Используй моноширинный шрифт и компактное выравнивание для Telegram!

**КРИТИЧЕСКИ ВАЖНО - ОБРАБОТКА ПУСТЫХ ЯЧЕЕК:**
- Если значение null → отображай как пустую ячейку (пробелы)
- НЕ ЗАПОЛНЯЙ пустые ячейки значениями по умолчанию!
- НЕ ВЫЧИСЛЯЙ недостающие значения!
- Отображай таблицу точно как она была на фото!

1. Создай таблицу с выровненными столбцами оптимальной ширины:
   - Столбец 1: Номер строки (ширина 1 символ)
   - Столбец 2: Название товара (выровнять по левому краю, оптимальная ширина, переносить длинные названия на новые строки, длинные слова разбивать с тире)
   - Столбец 3: Кол (выровнять по центру, оптимальная ширина)
   - Столбец 4: Цена (выровнять по центру, оптимальная ширина)
   - Столбец 5: Сумма (выровнять по правому краю, оптимальная ширина)
   - Столбец 6: Статус (✅, 🔴 или ⚠️, ширина 2 символа)

2. Для выравнивания используй пробелы и символы:
   - Для левого выравнивания: добавляй пробелы справа
   - Для правого выравнивания: добавляй пробелы слева
   - Для центрирования: добавляй пробелы с обеих сторон
   - Для пустых ячеек (null): используй пробелы соответствующей ширины

3. Пример правильного формата с оптимальной шириной:
```
№| Товар      |Кол | Цена    |    Сумма | 
─────────────────────────────────────────
1| TIMUN      | 3  | 12 000  |   36 000 | ✅
2| WORTEL     | 3  | 25 000  |   75 000 | ✅
3| TOMAT      | 3  | 25 000  |   75 000 | ✅
4| KOL UNGU   | 6  | 39 000  |  234 000 | 🔴
5| CORIA-     | 2  | 15 000  |   30 000 | ✅
 | NDA        |    |         |          |   
6| TAHU       |    | 15 000  |          | ⚠️
7| IKAN BAKAR | 2  |         |  170 000 | ⚠️
```

4. Для каждой позиции:
   - Если все значения есть (не null) → сравни расчет (Кол-во * Цена) с суммой. Если совпадает, ставь ✅. Если нет, ставь 🔴.
   - Если есть null значения → ставь ⚠️ (needs_review)
5. Подсчитай итоговую сумму только по позициям с полными данными.
6. Сравни твой расчет итога с итогом из чека.
7. Напиши краткий вывод, комментируя только расхождения (🔴) и пустые ячейки (⚠️).

**ПРАВИЛА ОТОБРАЖЕНИЯ ПУСТЫХ ЯЧЕЕК:**
- null в quantity → пустая ячейка в столбце "Кол"
- null в price → пустая ячейка в столбце "Цена"  
- null в total → пустая ячейка в столбце "Сумма"
- "???" в name → отображай как "???"

Вот данные:
"""

# Poster API token
POSTER_TOKEN = "853931:71424838d41a70ee724e07ef6c6f0774"
