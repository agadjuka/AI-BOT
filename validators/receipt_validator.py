"""
Receipt data validation
"""
from typing import Tuple
from models.receipt import ReceiptData


class ReceiptValidator:
    """Validator for receipt data"""
    
    @staticmethod
    def validate_receipt_data(data: ReceiptData) -> Tuple[bool, str]:
        """Validate receipt data correctness"""
        items = data.items
        
        if not items:
            return False, "Нет товарных позиций"
        
        # Check that all lines have correct numbers
        line_numbers = [item.line_number for item in items]
        expected_numbers = list(range(1, len(items) + 1))
        
        if line_numbers != expected_numbers:
            return False, f"Неправильная нумерация строк: {line_numbers}, ожидалось: {expected_numbers}"
        
        # Check that all lines have required fields
        for item in items:
            # Check required fields exist (name and status are always required)
            if not hasattr(item, 'name') or item.name is None:
                return False, f"Отсутствует поле name в строке {item.line_number}"
            if not hasattr(item, 'status') or item.status is None:
                return False, f"Отсутствует поле status в строке {item.line_number}"
            
            # quantity, price, total могут быть None (нечитаемые данные)
            # Проверяем только что поля существуют, но не требуем значений
            if not hasattr(item, 'quantity'):
                return False, f"Отсутствует поле quantity в строке {item.line_number}"
            if not hasattr(item, 'price'):
                return False, f"Отсутствует поле price в строке {item.line_number}"
            if not hasattr(item, 'total'):
                return False, f"Отсутствует поле total в строке {item.line_number}"
            
            # Additional calculation check (only for logging)
            quantity = item.quantity
            price = item.price
            total = item.total
            
            # Проверяем расчеты только если все поля не None и больше 0
            if quantity is not None and price is not None and total is not None and quantity > 0 and price > 0 and total > 0:
                expected_total = quantity * price
                if abs(expected_total - total) > 0.01:
                    print(f"Предупреждение: Строка {item.line_number} - расчеты не сходятся: {quantity} * {price} = {expected_total}, но в чеке {total}")
        
        return True, "Данные корректны"
    
    @staticmethod
    def validate_line_number(data: ReceiptData, line_number: int) -> Tuple[bool, str]:
        """Validate line number for editing"""
        if line_number < 1:
            return False, "Номер строки должен быть больше 0"
        
        max_line_number = data.get_max_line_number()
        if line_number > max_line_number:
            return False, f"Номер строки {line_number} превышает максимальный {max_line_number}"
        
        # Check if line exists
        item = data.get_item(line_number)
        if not item:
            return False, f"Строка {line_number} не найдена"
        
        return True, "Номер строки корректен"
    
    @staticmethod
    def validate_numeric_input(value: str, field_name: str) -> Tuple[bool, str, float]:
        """Validate numeric input from user"""
        if not value or not value.strip():
            return False, f"{field_name} не может быть пустым", 0.0
        
        try:
            # Simple validation - check if it can be converted to float
            numeric_value = float(value.strip())
            if numeric_value < 0:
                return False, f"{field_name} не может быть отрицательным", 0.0
            
            return True, "Значение корректно", numeric_value
        except ValueError:
            return False, f"Неверный формат {field_name}. Введите число", 0.0
    
    @staticmethod
    def validate_text_input(value: str, field_name: str) -> Tuple[bool, str]:
        """Validate text input from user"""
        if not value or not value.strip():
            return False, f"{field_name} не может быть пустым"
        
        if len(value.strip()) > 100:  # Reasonable limit for product names
            return False, f"{field_name} слишком длинное (максимум 100 символов)"
        
        return True, "Значение корректно"
