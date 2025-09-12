"""
Formatter for ingredient matching results
"""
from typing import List, Optional
from telegram.ext import ContextTypes
from models.ingredient_matching import IngredientMatchingResult, IngredientMatch, MatchStatus
from utils.table_manager import TableManager


class IngredientFormatter:
    """Formatter for ingredient matching results"""
    
    def __init__(self, table_manager: Optional[TableManager] = None):
        self.max_name_length = 15  # Maximum length for ingredient names in table
        self.max_suggestion_length = 15  # Maximum length for suggestion names
        self.table_manager = table_manager
    
    def format_matching_table(self, result: IngredientMatchingResult, changed_indices: set = None, context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> str:
        """
        Format ingredient matching results as a table
        
        Args:
            result: IngredientMatchingResult to format
            changed_indices: Set of indices that were manually changed (0-based)
            context: Telegram context for device detection and localization
            
        Returns:
            Formatted table string
        """
        # Используем новый TableManager если доступен
        if self.table_manager:
            return self.table_manager.format_ingredient_matching_table(result, context, changed_indices)
        
        # Fallback на старую логику
        if not result.matches:
            return "Нет ингредиентов для сопоставления."
        
        # Create table header
        table_lines = []
        table_lines.append("**Сопоставление ингредиентов:**\n")
        
        # Add summary
        summary = f"📊 **Статистика:** Всего: {result.total_items} | "
        summary += f"🟢 Точных: {result.exact_matches} | "
        summary += f"🟡 Частичных: {result.partial_matches} | "
        summary += f"🔴 Не найдено: {result.no_matches}\n"
        table_lines.append(summary)
        
        # Create table
        table_lines.append("```")
        table_lines.append(self._create_table_header())
        table_lines.append(self._create_table_separator())
        
        # Add table rows
        for i, match in enumerate(result.matches, 1):
            is_changed = changed_indices is not None and (i-1) in changed_indices
            table_lines.append(self._create_table_row(i, match, is_changed))
        
        table_lines.append("```")
        
        return "\n".join(table_lines)
    
    def _create_table_header(self) -> str:
        """Create table header"""
        return f"{'№':<2} | {'Товар':<{self.max_name_length}} | {'Google Sheets':<{self.max_name_length}} | {'Статус':<4}"
    
    def _create_table_separator(self) -> str:
        """Create table separator"""
        total_width = 2 + 3 + self.max_name_length + 3 + self.max_name_length + 3 + 4
        return "-" * total_width
    
    def _create_table_row(self, row_number: int, match: IngredientMatch, is_changed: bool = False) -> str:
        """Create a table row for a match"""
        # Wrap names instead of truncating
        receipt_name_lines = self._wrap_text(match.receipt_item_name, self.max_name_length)
        ingredient_name_lines = self._wrap_text(
            match.matched_ingredient_name or "—", 
            self.max_name_length
        )
        
        # Get status emoji - if changed, show pencil instead of regular status
        if is_changed:
            status_emoji = "✏️"
        else:
            status_emoji = self._get_status_emoji(match.match_status)
        
        # Create multi-line row
        max_lines = max(len(receipt_name_lines), len(ingredient_name_lines))
        row_lines = []
        
        for i in range(max_lines):
            receipt_name = receipt_name_lines[i] if i < len(receipt_name_lines) else ""
            ingredient_name = ingredient_name_lines[i] if i < len(ingredient_name_lines) else ""
            
            # Only show row number and status on first line
            if i == 0:
                row_line = f"{row_number:<2} | {receipt_name:<{self.max_name_length}} | {ingredient_name:<{self.max_name_length}} | {status_emoji:<4}"
            else:
                row_line = f"{'  ':<2} | {receipt_name:<{self.max_name_length}} | {ingredient_name:<{self.max_name_length}} | {'  ':<4}"
            
            row_lines.append(row_line)
        
        return "\n".join(row_lines)
    
    def _wrap_text(self, text: str, max_width: int) -> list[str]:
        """Wrap text to fit within max_width, breaking on words when possible"""
        if not text:
            return [""]
        
        if len(text) <= max_width:
            return [text]
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            # If adding this word would exceed the width
            if len(current_line) + len(word) + 1 > max_width:
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    # Single word is too long, split it with hyphen
                    lines.append(word[:max_width-1] + "-")
                    current_line = word[max_width-1:]
            else:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines

    def _truncate_name(self, name: str, max_length: int) -> str:
        """Truncate name if too long"""
        if len(name) <= max_length:
            return name
        return name[:max_length-3] + "..."
    
    def _get_status_emoji(self, status: MatchStatus) -> str:
        """Get emoji for match status"""
        if status == MatchStatus.EXACT_MATCH:
            return "🟢"
        elif status == MatchStatus.PARTIAL_MATCH:
            return "🟡"
        else:
            return "🔴"
    
    def format_suggestions_for_manual_matching(self, match: IngredientMatch, min_score: float = 0.5) -> List[dict]:
        """
        Get filtered suggestions for manual matching
        
        Args:
            match: IngredientMatch with suggestions
            min_score: Minimum score threshold (default 0.5 = 50%)
            
        Returns:
            List of suggestion dictionaries with score >= min_score
        """
        if not match.suggested_matches:
            return []
        
        # Filter suggestions by minimum score
        filtered_suggestions = [
            suggestion for suggestion in match.suggested_matches 
            if suggestion['score'] >= min_score
        ]
        
        return filtered_suggestions
    
    def format_manual_matching_instructions(self) -> str:
        """Format instructions for manual matching"""
        return (
            "**Инструкции по ручному сопоставлению:**\n\n"
            "1. Выберите номер предложения для автоматического сопоставления\n"
            "2. Или введите '0' для пропуска этого ингредиента\n"
            "3. Или введите 'search: <название>' для поиска других вариантов\n\n"
            "Примеры:\n"
            "• `1` - выбрать первое предложение\n"
            "• `0` - пропустить\n"
            "• `search: tomato` - найти варианты с 'tomato'"
        )
    
    def format_search_results(self, query: str, results: List[dict]) -> str:
        """
        Format search results for manual selection
        
        Args:
            query: Search query
            results: List of search results
            
        Returns:
            Formatted search results string
        """
        if not results:
            return f"По запросу '{query}' ничего не найдено."
        
        lines = [f"**Результаты поиска для '{query}':**\n"]
        
        for i, result in enumerate(results, 1):
            name = self._truncate_name(result['name'], self.max_suggestion_length)
            score = int(result['score'] * 100)
            lines.append(f"{i}. {name} ({score}%)")
        
        return "\n".join(lines)
