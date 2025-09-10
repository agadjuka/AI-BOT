"""
Receipt data validation
"""
from typing import Tuple, Optional, Any
from models.receipt import ReceiptData
from config.locales.locale_manager import locale_manager


class ReceiptValidator:
    """Validator for receipt data"""
    
    @staticmethod
    def validate_receipt_data(data: ReceiptData, context: Optional[Any] = None) -> Tuple[bool, str]:
        """Validate receipt data correctness"""
        items = data.items
        
        if not items:
            return False, locale_manager.get_text("validation.no_items", context)
        
        # Check that all lines have correct numbers
        line_numbers = [item.line_number for item in items]
        expected_numbers = list(range(1, len(items) + 1))
        
        if line_numbers != expected_numbers:
            return False, locale_manager.get_text(
                "validation.incorrect_line_numbering", 
                context,
                line_numbers=line_numbers,
                expected_numbers=expected_numbers
            )
        
        # Check that all lines have required fields
        for item in items:
            # Check required fields exist (name and status are always required)
            if not hasattr(item, 'name') or item.name is None:
                return False, locale_manager.get_text(
                    "validation.missing_name_field", 
                    context,
                    line_number=item.line_number
                )
            if not hasattr(item, 'status') or item.status is None:
                return False, locale_manager.get_text(
                    "validation.missing_status_field", 
                    context,
                    line_number=item.line_number
                )
            
            # quantity, price, total могут быть None (нечитаемые данные)
            # Проверяем только что поля существуют, но не требуем значений
            if not hasattr(item, 'quantity'):
                return False, locale_manager.get_text(
                    "validation.missing_quantity_field", 
                    context,
                    line_number=item.line_number
                )
            if not hasattr(item, 'price'):
                return False, locale_manager.get_text(
                    "validation.missing_price_field", 
                    context,
                    line_number=item.line_number
                )
            if not hasattr(item, 'total'):
                return False, locale_manager.get_text(
                    "validation.missing_total_field", 
                    context,
                    line_number=item.line_number
                )
            
            # Additional calculation check (only for logging)
            quantity = item.quantity
            price = item.price
            total = item.total
            
            # Проверяем расчеты только если все поля не None и больше 0
            if quantity is not None and price is not None and total is not None and quantity > 0 and price > 0 and total > 0:
                expected_total = quantity * price
                if abs(expected_total - total) > 0.01:
                    warning_msg = locale_manager.get_text(
                        "validation.calculation_warning",
                        context,
                        line_number=item.line_number,
                        quantity=quantity,
                        price=price,
                        expected_total=expected_total,
                        total=total
                    )
                    print(warning_msg)
        
        return True, locale_manager.get_text("validation.data_correct", context)
    
    @staticmethod
    def validate_line_number(data: ReceiptData, line_number: int, context: Optional[Any] = None) -> Tuple[bool, str]:
        """Validate line number for editing"""
        if line_number < 1:
            return False, locale_manager.get_text("validation.line_number_too_small", context)
        
        max_line_number = data.get_max_line_number()
        if line_number > max_line_number:
            return False, locale_manager.get_text(
                "validation.line_number_too_large", 
                context,
                line_number=line_number,
                max_line_number=max_line_number
            )
        
        # Check if line exists
        item = data.get_item(line_number)
        if not item:
            return False, locale_manager.get_text(
                "validation.line_not_found", 
                context,
                line_number=line_number
            )
        
        return True, locale_manager.get_text("validation.line_number_correct", context)
    
    @staticmethod
    def validate_numeric_input(value: str, field_name: str, context: Optional[Any] = None) -> Tuple[bool, str, float]:
        """Validate numeric input from user"""
        if not value or not value.strip():
            return False, locale_manager.get_text(
                "validation.field_cannot_be_empty", 
                context,
                field_name=field_name
            ), 0.0
        
        try:
            # Simple validation - check if it can be converted to float
            numeric_value = float(value.strip())
            if numeric_value < 0:
                return False, locale_manager.get_text(
                    "validation.field_negative", 
                    context,
                    field_name=field_name
                ), 0.0
            
            return True, locale_manager.get_text("validation.value_correct", context), numeric_value
        except ValueError:
            return False, locale_manager.get_text(
                "validation.invalid_numeric_format", 
                context,
                field_name=field_name
            ), 0.0
    
    @staticmethod
    def validate_text_input(value: str, field_name: str, context: Optional[Any] = None) -> Tuple[bool, str]:
        """Validate text input from user"""
        if not value or not value.strip():
            return False, locale_manager.get_text(
                "validation.field_cannot_be_empty", 
                context,
                field_name=field_name
            )
        
        if len(value.strip()) > 100:  # Reasonable limit for product names
            return False, locale_manager.get_text(
                "validation.field_too_long", 
                context,
                field_name=field_name
            )
        
        return True, locale_manager.get_text("validation.value_correct", context)
