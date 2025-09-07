"""
AI prompts configuration for the AI Bot
"""
from typing import Dict, Any


class PromptManager:
    """Manager for AI prompts with methods to get specific prompts"""
    
    def __init__(self):
        self._prompts = self._initialize_prompts()
    
    def _initialize_prompts(self) -> Dict[str, str]:
        """Initialize all prompts"""
        return {
            'analyze': self._get_analyze_prompt(),
            'format': self._get_format_prompt(),
            'ingredient_matching': self._get_ingredient_matching_prompt()
        }
    
    def get_analyze_prompt(self) -> str:
        """Get the receipt analysis prompt"""
        return self._prompts['analyze']
    
    def get_format_prompt(self) -> str:
        """Get the receipt formatting prompt"""
        return self._prompts['format']
    
    def get_ingredient_matching_prompt(self) -> str:
        """Get the ingredient matching prompt"""
        return self._prompts['ingredient_matching']
    
    def _get_analyze_prompt(self) -> str:
        """Receipt analysis prompt for extracting data from receipt images"""
        return """
Извлеки данные из чека в JSON. КОПИРУЙ ТОЧНО - не вычисляй.

ПРАВИЛА:
- Пустое место → null
- Нечитаемо → "???"
- Индонезийские названия → английский (сохрани единицы: кг,г,л,мл)
- Числа в JSON: 125000 (не 125 000)

ОСОБОЕ ПРАВИЛО ДЛЯ НЕОПОЗНАННЫХ ПРОДУКТОВ:
- Если не можешь идентифицировать продукт как конкретное наименование, найди в интернете что это такое
- После названия бренда в скобках укажи что это за продукт !НА АНГЛИЙСКОМ ЯЗЫКЕ!  
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
    
    def _get_format_prompt(self) -> str:
        """Receipt formatting prompt for displaying data in Telegram"""
        return """
Оформи данные чека в таблицу для Telegram (моноширинный шрифт).

ПРАВИЛА:
- null → пустая ячейка (пробелы)
- НЕ вычисляй недостающие значения
- Российский формат чисел: 125 000 (пробел для тысяч)

ТАБЛИЦА:
№| Товар      |Кол | Цена      |    Сумма | 
────────────────────────────────────────────
1| Название   |кол-во| цена    |   сумма  | ✅/🔴/⚠️

СТАТУСЫ:
- ✅: все данные есть, расчет совпадает
- 🔴: все данные есть, расчет НЕ совпадает  
- ⚠️: есть null значения

ИТОГ: сумма по полным позициям + сравнение с grand_total_text

Данные:
"""
    
    def _get_ingredient_matching_prompt(self) -> str:
        """Ingredient matching prompt for AI-assisted ingredient matching"""
        return """
Помоги сопоставить ингредиенты из чека с ингредиентами из базы данных.

ЗАДАЧА:
- Сопоставить название продукта из чека с наиболее подходящим ингредиентом из базы
- Учесть синонимы, варианты написания и похожие продукты
- Предложить несколько вариантов с оценкой совпадения

ПРАВИЛА:
- Приоритет точным совпадениям названий
- Учитывай единицы измерения (кг, г, л, мл)
- Игнорируй бренды и марки, фокусируйся на типе продукта
- Предлагай варианты с оценкой от 0 до 100%

ФОРМАТ ОТВЕТА:
```json
{
  "matches": [
    {
      "ingredient_name": "название ингредиента",
      "ingredient_id": "ID_ингредиента",
      "similarity_score": 85,
      "reason": "объяснение совпадения"
    }
  ]
}
```

Данные для сопоставления:
"""
