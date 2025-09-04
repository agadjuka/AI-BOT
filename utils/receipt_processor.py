"""
Receipt processing utilities
"""
from typing import Dict, Any
from models.receipt import ReceiptData, ReceiptItem


class ReceiptProcessor:
    """Utility class for receipt data processing"""
    
    @staticmethod
    def auto_update_item_status(item: ReceiptItem) -> ReceiptItem:
        """Automatically update item status based on its data (ONLY for markers, NOT changing data)"""
        quantity = item.quantity
        price = item.price
        total = item.total
        item_name = item.name
        
        # Check if name is unreadable
        is_unreadable = item_name == "???" or item_name == "**не распознано**"
        
        # Check if any numeric field is null (None) - means unreadable
        has_null_values = quantity is None or price is None or total is None
        
        if is_unreadable or has_null_values:
            # If name is unreadable OR any numeric field is null - needs_review
            item.status = 'needs_review'
        elif quantity is not None and price is not None and total is not None:
            # All fields are readable numbers - check calculation
            if quantity > 0 and price > 0 and total > 0:
                expected_total = quantity * price
                if abs(expected_total - total) < 0.01:
                    item.status = 'confirmed'  # Green marker
                else:
                    item.status = 'error'      # Red marker (calculation mismatch)
            else:
                # Zero values - needs_review
                item.status = 'needs_review'
        else:
            # Fallback - needs_review
            item.status = 'needs_review'
        
        return item
    
    @staticmethod
    def auto_calculate_total_if_needed(item: ReceiptItem) -> ReceiptItem:
        """DO NOT automatically calculate - only for scanner mode"""
        # В режиме сканера НЕ вычисляем значения автоматически
        # Все значения должны быть строго из чека
        item.auto_calculated = False
        return item
    
    @staticmethod
    def auto_update_all_statuses(data: ReceiptData) -> ReceiptData:
        """Automatically update statuses of all items in data (ONLY for markers, NOT changing data)"""
        for item in data.items:
            # First automatically calculate sum if needed
            item = ReceiptProcessor.auto_calculate_total_if_needed(item)
            # Then update status
            item = ReceiptProcessor.auto_update_item_status(item)
        return data
    
    @staticmethod
    def check_all_items_confirmed(data: ReceiptData) -> bool:
        """Check if all lines are confirmed (no errors and unreadable data) - ONLY for marker determination"""
        for item in data.items:
            status = item.status
            
            # Check calculation mismatch
            quantity = item.quantity
            price = item.price
            total = item.total
            has_calculation_error = False
            
            # Проверяем расчеты только если все поля не None и больше 0
            if quantity is not None and price is not None and total is not None and quantity > 0 and price > 0 and total > 0:
                expected_total = quantity * price
                has_calculation_error = abs(expected_total - total) > 0.01
            
            # Check if name is unreadable
            item_name = item.name
            is_unreadable = item_name == "???" or item_name == "**не распознано**"
            
            # If there are calculation errors, unreadable data or status not confirmed
            if status != 'confirmed' or has_calculation_error or is_unreadable:
                return False
        
        return True
