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
You are an expert OCR AI. Extract receipt line items into JSON format with high accuracy.

**TASK:** Analyze receipt image and extract purchased items only (ignore header, date, total, signatures).

**RULES:**
1. Extract ONLY line items with products
2. If uncertain about any value, use "---" 
3. For numbers: if any digit is unclear, mark entire number as "---"
4. Process every line item (even if unreadable)
5. Empty cells = null, unreadable = "---"
6. Convert Indonesian product names to English (keep units: kg, g, l, ml)
7. Numbers format: 125000 (no spaces)

**CRITICAL:** NO CALCULATIONS - only extract what you can clearly see. Don't compute missing values.

**UNKNOWN PRODUCTS:** Add product type in English after brand name.
Example: "Dine FF Crinkle" → "Dine FF Crinkle (French Fries)"

**JSON FORMAT:**
{
  "items": [
    {
      "line_number": 1,
      "name": "product name in English",
      "quantity": number_or_null,
      "price": number_or_null,
      "total": number_or_null,
      "status": "confirmed/error/needs_review"
    }
  ],
  "grand_total_text": "total_amount_text"
}

**STATUS:**
- "confirmed": All values clearly visible
- "error": All values present but calculation mismatch
- "needs_review": Some values are "---"
"""
    
    def _get_format_prompt(self) -> str:
        """Receipt formatting prompt for displaying data in Telegram"""
        return """
Format receipt data as a table for Telegram (monospaced font).

RULES:
- null -> empty cell (spaces)
- DO NOT calculate missing values
- Russian number format: 125 000 (space for thousands)

TABLE:
#| Item       |Qty | Price     |   Total | 
------------------------------------------------
1| Name       |qty | price     |   total | OK/ERR/WARN

STATUSES:
- OK: all data present, calculation matches
- ERR: all data present, calculation DOES NOT match
- WARN: some null values

TOTAL: sum of complete items + comparison with grand_total_text

Data:
"""
    
    def _get_ingredient_matching_prompt(self) -> str:
        """Ingredient matching prompt for AI-assisted ingredient matching"""
        return """
Help match receipt ingredients with ingredients from the database.

TASK:
- Match the product name from the receipt with the most suitable ingredient from the database
- Consider synonyms, spelling variations, and similar products
- Suggest multiple options with a similarity score

RULES:
- Priority to exact name matches
- Consider measurement units (kg, g, l, ml)
- Ignore brands, focus on product type
- Provide options with scores from 0 to 100%

ANSWER FORMAT:
```json
{
  "matches": [
    {
      "ingredient_name": "ingredient name",
      "ingredient_id": "ingredient_ID",
      "similarity_score": 85,
      "reason": "explanation of the match"
    }
  ]
}

```

Data to match:
"""