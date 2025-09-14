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
You are an expert-level Optical Character Recognition (OCR) and data extraction AI. 
Your task is to analyze an image of a receipt and extract the line item information into a strict JSON array format.
**Your primary goal:** Absolute accuracy. It is critically better to mark data as unreadable than to guess and provide incorrect information.

**Input:** An image of a receipt. The receipt may be handwritten, crumpled, poorly lit, or have low resolution.

**CRITICAL RULES (MUST BE FOLLOWED STRICTLY):**

1.  **Extract Line Items Only:** Focus exclusively on the rows listing the purchased items. Ignore the receipt header (store name, address), date, final total amount (e.g., "TOTAL Rp."), signatures, and any other metadata.

2.  **Uncertainty Rule "---":** If you are not 100% confident in recognizing any value (a word, a number, or part of a word), you MUST replace the ENTIRE value for that field with the string "---". Do not attempt to guess.

3.  **Rule for Numbers:** This is extremely important. If even a SINGLE digit or character (like a dot or comma) within a number (quantity, price) is illegible or ambiguous, the ENTIRE number for that field must be replaced with "---".
    *   *Example:* If a price reads "15.000" but the "5" is smudged, the `unit_price` field must be "---", not "1?.000" or "10.000".

4.  **Do Not Skip Rows:** You must process every single line item on the receipt. If an entire row is unreadable, create a JSON object for it where all values are set to "---".
    *   *Example:* `{"quantity": "---", "item_name": "---", "unit_price": "---", "total_price": "---"}`.

5.  **Empty Cells:** If a cell within an item row is intentionally left blank (like the price for "Cari roti tawar" in the provided example), its corresponding value in the JSON object must also be "---".

# RULES:
# - Empty cell → null
# - Unreadable → "???"
# - Indonesian product names → English (keep units: kg, g, l, ml)
# - Numbers in JSON: 125000 (not 125 000)
#
# SPECIAL RULE FOR UNKNOWN PRODUCTS:
# - If you cannot identify the product by its name, look it up online
# - After the brand name, add in parentheses what type of product it is IN ENGLISH
# - Example: "Dine FF Crinkle" → "Dine FF Crinkle (French Fries)"
# - Example: "Mama Tom Yam" → "Mama Tom Yam (Instant Noodles)"
#
# LINES:
# 1. With numbers: name (English+units), quantity, price, total, status
# 2. Text only: name (English), quantity=null, price=null, total=null, status="needs_review"
# 3. Unreadable: name="???", others=null, status="needs_review"
# 4. Empty line: DO NOT include
#
# JSON FORMAT:
# {
#   "items": [
#     {
#       "line_number": 1,
#       "name": "name in English",
#       "quantity": number_or_null,
#       "price": number_or_null,
#       "total": number_or_null,
#       "status": "confirmed/error/needs_review"
#     }
#   ],
#   "grand_total_text": "total_amount_text"
# }

def _get_format_prompt(self) -> str:
    """Receipt formatting prompt for displaying data in Telegram"""
    return """
Format receipt data as a table for Telegram (monospaced font).

RULES:
- null → empty cell (spaces)
- DO NOT calculate missing values
- Russian number format: 125 000 (space for thousands)

TABLE:
№| Item       |Qty | Price     |   Total | 
────────────────────────────────────────────
1| Name       |qty | price     |   total | ✅/🔴/⚠️

STATUSES:
- ✅: all data present, calculation matches
- 🔴: all data present, calculation DOES NOT match
- ⚠️: some null values

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