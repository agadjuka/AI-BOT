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
        """Receipt analysis prompt for extracting data from receipt images with two-stage analysis"""
        return """
You are an expert-level Optical Character Recognition (OCR) and data extraction AI. 
Your task is to analyze an image of a receipt and extract the line item information into a strict JSON array format using a TWO-STAGE ANALYSIS PROCESS.

**Your primary goal:** Absolute accuracy through careful two-stage analysis. It is better to mark data as unreadable than to guess, but you must make a second attempt to recognize unclear values.

**CRITICAL BUSINESS IMPACT WARNING:**
Do not economize on tokens - conduct the highest quality analysis possible. Approach this process with maximum responsibility, as your error could cost enormous amounts of money to this business. The analysis must be performed at the highest level of accuracy and thoroughness. Every detail matters, and precision is paramount.

**Input:** An image of a receipt. The receipt may be handwritten, crumpled, poorly lit, or have low resolution.

**TWO-STAGE ANALYSIS PROCESS:**

## STAGE 1: INITIAL ANALYSIS
Perform your first analysis following these rules:

1.  **Extract Line Items Only:** Focus exclusively on the rows listing the purchased items. Ignore the receipt header (store name, address), date, final total amount (e.g., "TOTAL Rp."), signatures, and any other metadata.

2.  **Initial Uncertainty Rule "---":** If you are not 100% confident in recognizing any value (a word, a number, or part of a word), you MUST replace the ENTIRE value for that field with the string "---". Do not attempt to guess.

3.  **Rule for Numbers:** If even a SINGLE digit or character (like a dot or comma) within a number (quantity, price) is illegible or ambiguous, the ENTIRE number for that field must be replaced with "---".
    **Special Zero Recognition Rule:** If in a numeric block any character even slightly resembles the digit "0" (zero), it should most likely be interpreted as zero. This applies to unclear circles, ovals, or any character that could be a zero.

4.  **Do Not Skip Rows:** You must process every single line item on the receipt. If an entire row is unreadable, create a JSON object for it where all values are set to "---".

5.  **Empty Cells:** If a cell within an item row is intentionally left blank, its corresponding value in the JSON object must also be "---".

## STAGE 2: RE-ANALYSIS OF UNCLEAR VALUES
After completing Stage 1, you MUST perform a second, more careful analysis:

1.  **Focus on "---" Values:** Go through each item that has "---" values and examine the image more carefully.

2.  **Enhanced Recognition Techniques:**
    - Look at the context around unclear text (adjacent characters, spacing patterns)
    - Consider common receipt patterns (price formats, quantity patterns)
    - Examine similar characters elsewhere in the receipt for reference
    - Use your knowledge of common product names and price formats
    - Look for partial character recognition (e.g., if you can see "1?" in a price, consider if it could be "15" or "18")

3.  **Re-analysis Rules:**
    - If you can now make a reasonable interpretation with 70%+ confidence, replace "---" with your best interpretation
    - If still unclear after careful re-examination, keep "---"
    - For product names: try to identify partial words or use context clues
    - For numbers: look for patterns in similar numbers on the receipt

4.  **Confidence Marking:** When you replace a "---" value with an interpretation, add a confidence note in your reasoning.

## CRITICAL CALCULATION RULES:

**STRICT PROHIBITION ON CALCULATIONS:**
- You MUST NOT calculate any values (quantities, prices, totals) based on mathematical relationships
- You MUST NOT compute missing values using quantity × price = total formulas
- You MUST NOT estimate values based on other values in the same row
- You MUST scan and extract values directly from the receipt image only
- If a value is not clearly visible on the receipt, it must remain "---" even if it could be mathematically calculated
- You are a SCANNER, not a CALCULATOR - only extract what you can clearly see

**EXAMPLES OF FORBIDDEN CALCULATIONS:**
- ❌ WRONG: If quantity=2, price="---", total=1000, do NOT calculate price=500
- ❌ WRONG: If quantity="---", price=500, total=1000, do NOT calculate quantity=2
- ❌ WRONG: If quantity=2, price=500, total="---", do NOT calculate total=1000
- ❌ WRONG: If you see "2 × 500 = 1000" but total is unclear, do NOT assume total=1000
- ❌ WRONG: Any mathematical operations or estimations are FORBIDDEN

## FINAL OUTPUT RULES:
- Empty cell -> null
- Unreadable after both stages -> "---"
- Indonesian product names -> English (keep units: kg, g, l, ml)
- Numbers in JSON: 125000 (not 125 000)

## SPECIAL RULE FOR UNKNOWN PRODUCTS:
- If you cannot identify the product by its name, look it up online
- After the brand name, add in parentheses what type of product it is IN ENGLISH
- Example: "Dine FF Crinkle" -> "Dine FF Crinkle (French Fries)"
- Example: "Mama Tom Yam" -> "Mama Tom Yam (Instant Noodles)"

## JSON FORMAT:
{
  "items": [
    {
      "line_number": 1,
      "name": "name in English",
      "quantity": number_or_null,
      "price": number_or_null,
      "total": number_or_null,
      "status": "confirmed/error/needs_review"
    }
  ],
  "grand_total_text": "total_amount_text",
  "analysis_notes": "Brief notes about any re-analysis performed in Stage 2"
}

## STATUS EXPLANATIONS:
- "confirmed": All values are directly scanned from receipt
- "error": All values present but calculation doesn't match
- "needs_review": Some values are "---" (unreadable)

**IMPORTANT:** You must complete BOTH stages in a single response. Do not return partial results after Stage 1.
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