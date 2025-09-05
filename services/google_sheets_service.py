"""
Service for uploading data to Google Sheets
"""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

from models.receipt import ReceiptData, ReceiptItem
from models.ingredient_matching import IngredientMatchingResult, IngredientMatch


class GoogleSheetsService:
    """Service for uploading receipt data to Google Sheets"""
    
    def __init__(self, credentials_path: Optional[str] = None, spreadsheet_id: Optional[str] = None):
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Sheets API service"""
        if not self.credentials_path or not os.path.exists(self.credentials_path):
            print("⚠️ Google Sheets credentials not found. Service will be disabled.")
            return
        
        if not self.spreadsheet_id:
            print("⚠️ Google Sheets spreadsheet ID not configured. Service will be disabled.")
            return
        
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            
            credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            self.service = build('sheets', 'v4', credentials=credentials)
            print("✅ Google Sheets service initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing Google Sheets service: {e}")
            self.service = None
    
    def is_available(self) -> bool:
        """Check if Google Sheets service is available"""
        return self.service is not None and self.spreadsheet_id is not None
    
    def upload_receipt_data(self, 
                           receipt_data: ReceiptData, 
                           matching_result: IngredientMatchingResult,
                           worksheet_name: str = "Receipts") -> tuple[bool, str]:
        """
        Upload receipt data to Google Sheets
        
        Args:
            receipt_data: Processed receipt data
            matching_result: Ingredient matching results
            worksheet_name: Name of the worksheet to upload to
            
        Returns:
            (success, message)
        """
        if not self.is_available():
            return False, "Google Sheets service is not available. Please check configuration."
        
        try:
            # Create data rows for Google Sheets
            data_rows = self._create_sheets_data(receipt_data, matching_result)
            
            # Upload data to Google Sheets
            result = self._upload_to_sheets(data_rows, worksheet_name)
            
            return True, f"Successfully uploaded {len(data_rows)-1} items to Google Sheets (updated {result.get('updatedCells', 0)} cells)"
            
        except Exception as e:
            return False, f"Error uploading to Google Sheets: {str(e)}"
    
    def _create_sheets_data(self, receipt_data: ReceiptData, matching_result: IngredientMatchingResult) -> List[List[Any]]:
        """Create data rows for Google Sheets"""
        data_rows = []
        
        # Add header row
        header_row = [
            "Timestamp",
            "Item Name", 
            "Matched Ingredient",
            "Quantity",
            "Price per Unit",
            "Total Amount",
            "Match Status",
            "Similarity Score"
        ]
        data_rows.append(header_row)
        
        # Add data rows
        for i, item in enumerate(receipt_data.items):
            # Get matching result for this item
            match = None
            if i < len(matching_result.matches):
                match = matching_result.matches[i]
            
            # Prepare row data
            row = [
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Timestamp
                item.name,  # Original item name
                match.matched_ingredient_name if match and match.matched_ingredient_name else "",  # Matched ingredient
                item.quantity if item.quantity is not None else 0,  # Quantity
                item.price if item.price is not None else 0,  # Price per unit
                item.total if item.total is not None else 0,  # Total amount
                match.match_status.value if match else "no_match",  # Match status
                match.similarity_score if match else 0.0  # Similarity score
            ]
            
            data_rows.append(row)
        
        return data_rows
    
    def _upload_to_sheets(self, data_rows: List[List[Any]], worksheet_name: str):
        """Upload data to Google Sheets"""
        body = {
            'values': data_rows
        }
        
        range_name = f"{worksheet_name}!A1"
        result = self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        print(f"Updated {result.get('updatedCells')} cells in Google Sheets")
        return result
    
    def get_upload_summary(self, receipt_data: ReceiptData, matching_result: IngredientMatchingResult) -> str:
        """Get summary of data to be uploaded"""
        total_items = len(receipt_data.items)
        matched_items = sum(1 for match in matching_result.matches 
                           if match.match_status.value != 'no_match' and match.matched_ingredient_name)
        
        summary = f"📊 **Данные для загрузки в Google Sheets:**\n\n"
        summary += f"📦 **Всего товаров:** {total_items}\n"
        summary += f"✅ **Сопоставлено:** {matched_items}\n"
        summary += f"❌ **Не сопоставлено:** {total_items - matched_items}\n"
        summary += f"📈 **Процент сопоставления:** {(matched_items / total_items * 100):.1f}%\n\n"
        summary += f"🕒 **Время загрузки:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return summary
