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
        
        if is_unreadable:
            # If name is unreadable but has numbers - needs_review
            if quantity > 0 or price > 0 or total > 0:
                item.status = 'needs_review'
            else:
                # If no numbers - needs_review
                item.status = 'needs_review'
        elif quantity > 0 and price > 0 and total > 0:
            # Check calculation match ONLY for marker determination
            # DO NOT CHANGE data! Only determine status for marker
            expected_total = quantity * price
            if abs(expected_total - total) < 0.01:
                item.status = 'confirmed'  # Green marker
            else:
                item.status = 'error'      # Red marker (manually entered sum)
        elif quantity > 0 and price > 0 and total == 0:
            # If has quantity and price but sum 0 - automatically calculate
            item.status = 'confirmed'  # Green marker for automatically calculated sum
        else:
            # If missing data for calculation
            item.status = 'needs_review'   # Yellow marker
        
        return item
    
    @staticmethod
    def auto_calculate_total_if_needed(item: ReceiptItem) -> ReceiptItem:
        """Automatically calculate sum if quantity and price are set but sum is 0"""
        quantity = item.quantity
        price = item.price
        total = item.total
        
        # If has quantity and price but sum is 0 - automatically calculate
        if quantity > 0 and price > 0 and total == 0:
            item.total = quantity * price
            # Set flag that sum was automatically calculated
            item.auto_calculated = True
        else:
            # If sum was entered manually, reset flag
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
            
            if quantity > 0 and price > 0 and total > 0:
                expected_total = quantity * price
                has_calculation_error = abs(expected_total - total) > 0.01
            
            # Check if name is unreadable
            item_name = item.name
            is_unreadable = item_name == "???" or item_name == "**не распознано**"
            
            # If there are calculation errors, unreadable data or status not confirmed
            if status != 'confirmed' or has_calculation_error or is_unreadable:
                return False
        
        return True
