"""
Formatting utilities for receipt data
"""
from typing import Dict, Any, List, Optional
from models.receipt import ReceiptData, ReceiptItem
from config.locales.locale_manager import get_global_locale_manager


class NumberFormatter:
    """Utility class for number formatting"""
    
    @staticmethod
    def format_number_with_spaces(number: Optional[float]) -> str:
        """Format number in Russian style: spaces for thousands, comma for decimal"""
        # Handle None values
        if number is None:
            return "0"
        
        # Always show number as integer if it's whole
        if number == int(number):
            return f"{int(number):,}".replace(",", " ")
        else:
            # If there are decimal places, use comma as decimal separator
            formatted = f"{number:,.2f}".replace(",", " ")
            # Replace the last dot with comma for Russian decimal format
            if '.' in formatted:
                parts = formatted.split('.')
                if len(parts) == 2:
                    # Remove trailing zeros from decimal part
                    decimal_part = parts[1].rstrip('0')
                    if decimal_part:
                        return f"{parts[0]},{decimal_part}"
                    else:
                        return parts[0]
            return formatted
    
    @staticmethod
    def get_display_width(text: str) -> int:
        """Calculate real text width considering emojis and Markdown formatting"""
        if not text:
            return 0
        
        # Remove Markdown formatting for width calculation
        clean_text = text.replace("***", "").replace("**", "").replace("*", "")
        
        # Emojis usually take 2 characters in display
        # Simple heuristic: if character is not ASCII, count as 2 characters
        width = 0
        for char in clean_text:
            if ord(char) > 127:  # Non-ASCII character (emoji, cyrillic, etc.)
                width += 2
            else:
                width += 1
        return width


class TextParser:
    """Utility class for parsing text input"""
    
    @staticmethod
    def parse_number_from_text(text: str) -> float:
        """Parse number from text, considering Russian format (spaces for thousands, comma for decimal)"""
        if not text:
            return 0.0
        
        # If text contains only words (e.g., "total sum"), return 0
        if text.isalpha() or text.replace(' ', '').isalpha():
            return 0.0
        
        # Remove everything except digits, dots, commas and spaces
        clean_text = ''.join(c for c in text if c.isdigit() or c in '., ')
        
        if not clean_text:
            return 0.0
        
        try:
            # Remove spaces (they are thousands separators in Russian format)
            clean_text = clean_text.replace(' ', '')
            
            # If there are both comma and dot
            if ',' in clean_text and '.' in clean_text:
                # Comma - thousands separator, dot - decimal separator
                # Example: 1,240.75 -> 1240.75
                clean_text = clean_text.replace(',', '')
            
            # If there are only commas
            elif ',' in clean_text:
                parts = clean_text.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2 and len(parts[1]) > 0:
                    # Comma - decimal separator (Russian format)
                    # Example: 1240,75 -> 1240.75
                    clean_text = clean_text.replace(',', '.')
                else:
                    # Commas - thousands separators
                    # Example: 1,240,750 or 496,000 -> 1240750 or 496000
                    clean_text = clean_text.replace(',', '')
            
            # If there are only dots
            elif '.' in clean_text:
                parts = clean_text.split('.')
                if len(parts) == 2 and len(parts[1]) <= 2 and len(parts[1]) > 0:
                    # Dot - decimal separator
                    # Example: 1240.75 -> 1240.75
                    pass
                else:
                    # Dots - thousands separators
                    # Example: 1.240.750 -> 1240750 or 14.000 -> 14000
                    clean_text = clean_text.replace('.', '')
            
            return float(clean_text)
        except (ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def parse_user_input_number(text: str) -> float:
        """Parse number entered by user (considers Russian format: spaces for thousands, comma for decimal)"""
        if not text:
            return 0.0
        
        # Remove everything except digits, dots, commas and spaces
        clean_text = ''.join(c for c in text if c.isdigit() or c in '., ')
        
        if not clean_text:
            return 0.0
        
        try:
            # Remove spaces (they are thousands separators in Russian format)
            clean_text = clean_text.replace(' ', '')
            
            # If there are both comma and dot
            if ',' in clean_text and '.' in clean_text:
                # Comma - decimal separator, dot - thousands separator
                # Example: 1.240,75 -> 1240.75
                clean_text = clean_text.replace('.', '')
                clean_text = clean_text.replace(',', '.')
            
            # If there are only commas
            elif ',' in clean_text:
                parts = clean_text.split(',')
                if len(parts) == 2 and len(parts[1]) <= 3 and len(parts[1]) > 0:
                    # Comma - decimal separator (Russian format)
                    # Example: 0,150 -> 0.150
                    clean_text = clean_text.replace(',', '.')
                else:
                    # Commas - thousands separators
                    # Example: 1,240,750 -> 1240750
                    clean_text = clean_text.replace(',', '')
            
            # If there are only dots
            elif '.' in clean_text:
                parts = clean_text.split('.')
                if len(parts) == 2 and len(parts[1]) <= 3 and len(parts[0]) <= 3 and len(parts[1]) > 0:
                    # Dot - decimal separator
                    # Example: 0.150 -> 0.150
                    pass
                else:
                    # Dots - thousands separators
                    # Example: 1.240.750 -> 1240750 or 14.000 -> 14000
                    clean_text = clean_text.replace('.', '')
            
            return float(clean_text)
        except (ValueError, TypeError):
            return 0.0


class ReceiptFormatter:
    """Formatter for receipt data display"""
    
    def __init__(self):
        self.number_formatter = NumberFormatter()
        self.text_parser = TextParser()
    
    def format_aligned_table(self, data: ReceiptData, context: Optional[Any] = None) -> str:
        """Create aligned table for Telegram with optimal column widths and total block"""
        items = data.items
        
        if not items:
            return get_global_locale_manager().get_text("formatters.no_data_to_display", context)
        
        # Determine optimal width for each column based on data
        # Consider real emoji width in display
        max_name_length = max(self.number_formatter.get_display_width(str(item.name)) for item in items)
        max_quantity_length = max(len(self.number_formatter.format_number_with_spaces(item.quantity)) for item in items)
        max_price_length = max(len(self.number_formatter.format_number_with_spaces(item.price)) for item in items)
        max_total_length = max(len(self.number_formatter.format_number_with_spaces(item.total)) for item in items)
        
        # Set fixed column widths (optimized for mobile devices)
        number_width = 2    # Fixed width 2 characters for number
        product_width = 15  # Fixed width 15 characters for products column
        quantity_width = 5  # Fixed width 5 characters for quantity (for decimal numbers)
        price_width = 8     # Fixed width 8 characters for price
        total_width = 8     # Fixed width 8 characters for total
        status_width = 2    # Fixed width 2 characters for status
        
        # Create header with optimal widths
        number_header = get_global_locale_manager().get_text("formatters.table_headers.number", context)
        product_header = get_global_locale_manager().get_text("formatters.table_headers.product", context)
        quantity_header = get_global_locale_manager().get_text("formatters.table_headers.quantity", context)
        price_header = get_global_locale_manager().get_text("formatters.table_headers.price", context)
        amount_header = get_global_locale_manager().get_text("formatters.table_headers.amount", context)
        
        header = f"{number_header:^{number_width}} | {product_header:<{product_width}} | {quantity_header:^{quantity_width}} | {price_header:^{price_width}} | {amount_header:>{total_width}} | {'':^{status_width}}"
        separator = "─" * (number_width + product_width + quantity_width + price_width + total_width + status_width + 10)  # 10 characters for separators
        
        lines = [header, separator]
        
        # Add data rows
        for item in items:
            line_number = item.line_number
            name = str(item.name)
            quantity = item.quantity
            price = item.price
            total = item.total
            
            # Break long names into parts with word/character wrapping
            # Consider real emoji width in display
            name_parts = []
            if self.number_formatter.get_display_width(name) <= product_width - 1:  # -1 for space
                name_parts = [name]
            else:
                # Wrap by words if possible
                words = name.split()
                current_line = ""
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    if self.number_formatter.get_display_width(test_line) <= product_width - 1:
                        current_line = test_line
                    else:
                        if current_line:
                            name_parts.append(current_line)
                            current_line = word
                        else:
                            # If word is too long, break by characters
                            while self.number_formatter.get_display_width(word) > product_width - 1:
                                # Find maximum length that fits
                                for i in range(len(word), 0, -1):
                                    if self.number_formatter.get_display_width(word[:i]) <= product_width - 1:
                                        name_parts.append(word[:i])
                                        word = word[i:]
                                        break
                                else:
                                    # If even one character doesn't fit, take it
                                    name_parts.append(word[:1])
                                    word = word[1:]
                            current_line = word
                if current_line:
                    name_parts.append(current_line)
            
            # Format quantity - if 0 or None, show dash
            if quantity is None or quantity == 0:
                quantity_str = "-"
            elif quantity is not None and quantity == int(quantity):
                quantity_str = str(int(quantity))
            else:
                quantity_str = str(quantity)
            
            # Format price - if 0 or None, show dash
            if price is None or price == 0:
                price_str = "-"
            else:
                # Use the same formatting as other places to preserve decimal places
                price_str = self.number_formatter.format_number_with_spaces(price)
            
            # Format total - if 0 or None, show dash
            if total is None or total == 0:
                total_str = "-"
            else:
                total_str = self.number_formatter.format_number_with_spaces(total)
            
            # Determine status based on item data
            item_status = item.status
            if item_status == 'confirmed':
                status = "✅"
            elif item_status == 'error':
                status = "🔴"
            else:
                status = "⚠️"
            
            # Create rows with alignment (can be multiple rows for one product)
            for i, name_part in enumerate(name_parts):
                # Apply Markdown formatting for unreadable names
                formatted_name = name_part
                if name_part == "???":
                    formatted_name = "***???***"  # Bold and underlined text in Markdown
                
                if i == 0:
                    # First row with full data
                    line = f"{line_number:^{number_width}} | {formatted_name:<{product_width}} | {quantity_str:^{quantity_width}} | {price_str:^{price_width}} | {total_str:>{total_width}} | {status:^{status_width}}"
                else:
                    # Subsequent rows only with name, but same length
                    line = f"{'':^{number_width}} | {formatted_name:<{product_width}} | {'':^{quantity_width}} | {'':^{price_width}} | {'':>{total_width}} | {'':^{status_width}}"
                lines.append(line)
        
        # Add "Total" block under table
        lines.append("")  # Empty line for separation
        
        # Get total sum from receipt
        receipt_total_text = data.grand_total_text
        receipt_total = self.text_parser.parse_number_from_text(receipt_total_text)
        formatted_receipt_total = self.number_formatter.format_number_with_spaces(receipt_total)
        
        # Create "Total" block - separate rectangle under table
        # Calculate total table width for total block alignment
        total_table_width = number_width + product_width + quantity_width + price_width + total_width + status_width + 10
        
        # Create "Total" block with right alignment
        total_label = get_global_locale_manager().get_text("formatters.total_label", context)
        total_value = formatted_receipt_total
        
        # Calculate position for total block right alignment
        total_block_width = len(total_label) + 1 + len(total_value)  # +1 for space
        padding = total_table_width - total_block_width
        
        if padding > 0:
            total_line = " " * padding + f"{total_label} {total_value}"
        else:
            total_line = f"{total_label} {total_value}"
        
        lines.append(total_line)
        
        return "\n".join(lines)
    
    def calculate_total_sum(self, data: ReceiptData) -> float:
        """Calculate total sum of all positions (sum values total taken from photo)"""
        total = 0.0
        for item in data.items:
            item_total = item.total
            # Include in total sum only if value is not None and not 0
            if item_total is not None and item_total > 0:
                total += item_total
        return total
    
    def check_total_sum_match(self, data: ReceiptData) -> tuple[bool, float, str]:
        """Check if calculated sum matches receipt sum (compares data from photo)"""
        calculated_total = self.calculate_total_sum(data)
        receipt_total_text = data.grand_total_text
        
        # Parse sum from receipt
        receipt_total = self.text_parser.parse_number_from_text(receipt_total_text)
        
        # Format parsed sum for display
        formatted_receipt_total = self.number_formatter.format_number_with_spaces(receipt_total)
        
        is_match = abs(calculated_total - receipt_total) < 0.01  # Consider tolerance
        return is_match, calculated_total, formatted_receipt_total
