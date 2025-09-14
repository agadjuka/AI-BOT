#!/usr/bin/env python3
"""
Тестовый скрипт для проверки переноса текста в таблице предпросмотра Google Sheets
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from handlers.google_sheets_callback_handler import GoogleSheetsCallbackHandler
from config.table_config import ColumnConfig, TableStyle, DeviceType
from models.ingredient_matching import IngredientMatchingResult, IngredientMatch, MatchStatus
from models.receipt import ReceiptData, ReceiptItem

def test_google_sheets_preview():
    """Тестирует перенос текста в таблице предпросмотра Google Sheets"""
    
    # Создаем обработчик
    handler = GoogleSheetsCallbackHandler()
    
    # Создаем тестовые данные чека
    receipt_items = [
        ReceiptItem(
            name="Trieste Syrup - Very Long Product Name That Should Wrap",
            quantity=0.65,
            price=115384.62,
            total=75000.0
        ),
        ReceiptItem(
            name="Ampec - Coffee Creamer - Very Long Product Name That Should Wrap | 1 kg",
            quantity=4.0,
            price=65000.0,
            total=260000.0
        )
    ]
    
    receipt_data = ReceiptData(items=receipt_items)
    
    # Создаем тестовые данные сопоставления
    matches = [
        IngredientMatch(
            receipt_item_name="Trieste Syrup - Very Long Product Name That Should Wrap",
            matched_ingredient_name="Trieste Syrup - Very Long Ingredient Name That Should Also Wrap",
            match_status=MatchStatus.NO_MATCH
        ),
        IngredientMatch(
            receipt_item_name="Ampec - Coffee Creamer - Very Long Product Name That Should Wrap | 1 kg",
            matched_ingredient_name="Ampec - Coffee | Creamer - Very Long Ingredient Name That Should Also Wrap - 1 kg",
            match_status=MatchStatus.PARTIAL_MATCH
        )
    ]
    
    matching_result = IngredientMatchingResult(matches=matches)
    
    # Создаем маппинг колонок
    column_mapping = {
        "A": "date",
        "B": "item", 
        "C": "quantity",
        "E": "total"
    }
    
    # Создаем динамические колонки
    dynamic_columns = [
        ColumnConfig("date", "A", 12, "left"),
        ColumnConfig("item", "B", 20, "left"),
        ColumnConfig("quantity", "C", 8, "right"),
        ColumnConfig("total", "E", 10, "right")
    ]
    
    # Форматируем таблицу предпросмотра
    preview_text = handler._format_dynamic_google_sheets_preview(
        receipt_data, matching_result, column_mapping, DeviceType.MOBILE
    )
    
    print("=== ТЕСТ ПЕРЕНОСА ТЕКСТА В ТАБЛИЦЕ ПРЕДПРОСМОТРА GOOGLE SHEETS ===")
    print(preview_text)
    print("\n=== КОНЕЦ ТЕСТА ===")

if __name__ == "__main__":
    test_google_sheets_preview()
