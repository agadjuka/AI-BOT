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
        if not self.spreadsheet_id:
            print("⚠️ Google Sheets spreadsheet ID not configured. Service will be disabled.")
            return
        
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            import json
            
            # Try to use the same credentials system as AI Service
            credentials = None
            
            # First, try to use GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable
            if os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"):
                try:
                    credentials_info = json.loads(os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON"))
                    credentials = Credentials.from_service_account_info(
                        credentials_info,
                        scopes=['https://www.googleapis.com/auth/spreadsheets']
                    )
                    print("✅ Google Sheets service initialized with GOOGLE_APPLICATION_CREDENTIALS_JSON")
                except Exception as e:
                    print(f"❌ Error parsing GOOGLE_APPLICATION_CREDENTIALS_JSON: {e}")
            
            # If that fails, try the credentials file path
            if not credentials and self.credentials_path and os.path.exists(self.credentials_path):
                try:
                    credentials = Credentials.from_service_account_file(
                        self.credentials_path,
                        scopes=['https://www.googleapis.com/auth/spreadsheets']
                    )
                    print("✅ Google Sheets service initialized with credentials file")
                except Exception as e:
                    print(f"❌ Error loading credentials file: {e}")
            
            # If still no credentials, try default authentication
            if not credentials:
                try:
                    from google.auth import default
                    credentials, project = default()
                    print(f"✅ Google Sheets service initialized with default credentials for project: {project}")
                except Exception as e:
                    print(f"❌ Error with default authentication: {e}")
            
            if not credentials:
                print("⚠️ No valid credentials found for Google Sheets. Service will be disabled.")
                return
            
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
            
            return True, f"Successfully uploaded {len(data_rows)} items to Google Sheets (updated {result.get('updatedCells', 0)} cells)"
            
        except Exception as e:
            return False, f"Error uploading to Google Sheets: {str(e)}"
    
    def _create_sheets_data(self, receipt_data: ReceiptData, matching_result: IngredientMatchingResult) -> List[List[Any]]:
        """Create data rows for Google Sheets in the target format (Date, Volume, Harga, Product)"""
        data_rows = []
        
        # Add data rows (no header, just data)
        for i, item in enumerate(receipt_data.items):
            # Get matching result for this item
            match = None
            if i < len(matching_result.matches):
                match = matching_result.matches[i]
            
            # Skip items without matched ingredients
            if not match or not match.matched_ingredient_name:
                continue
            
            # Format date as DD.MM.YYYY
            current_date = datetime.now().strftime('%d.%m.%Y')
            
            # Calculate volume using the same logic as in preview
            quantity = item.quantity if item.quantity is not None else 0
            
            # Extract volume from product name and multiply by quantity
            volume_from_name = self._extract_volume_from_name(item.name)
            if volume_from_name > 0:
                # Multiply extracted volume by quantity
                total_volume = volume_from_name * quantity
                if total_volume == int(total_volume):
                    quantity_str = f"{int(total_volume)} kg"
                else:
                    # Round to 2 decimal places
                    quantity_str = f"{total_volume:.2f} kg"
            elif quantity > 0:
                # Fallback to original behavior if no volume found in name
                if quantity == int(quantity):
                    quantity_str = f"{int(quantity)} kg"
                else:
                    # Round to 2 decimal places
                    quantity_str = f"{quantity:.2f} kg"
            else:
                quantity_str = ""
            
            # Format price with "Rp" suffix
            price_str = ""
            if item.price is not None and item.price > 0:
                # Format price with spaces for thousands separator, preserving decimal places
                if item.price == int(item.price):
                    # If it's a whole number, show it as integer
                    price_formatted = f"{int(item.price):,}".replace(",", " ")
                else:
                    # If it has decimal places, show them
                    price_formatted = f"{item.price:,.3f}".replace(",", " ").rstrip('0').rstrip('.')
                price_str = f"{price_formatted}Rp"
            
            # Use matched ingredient name as product name
            product_name = match.matched_ingredient_name
            
            # Prepare row data in target format: Date, Volume, Harga, Product
            row = [
                current_date,      # Date (B column)
                quantity_str,      # Volume (C column) 
                price_str,         # Harga (D column)
                product_name       # Product (E column)
            ]
            
            data_rows.append(row)
        
        return data_rows
    
    def _upload_to_sheets(self, data_rows: List[List[Any]], worksheet_name: str):
        """Upload data to Google Sheets by appending to the next empty row with formatting"""
        if not data_rows:
            return {"updatedCells": 0}
        
        # Find the next empty row
        next_row = self._find_next_empty_row(worksheet_name)
        
        # Calculate the range for appending data
        start_col = 2  # Column B (Date)
        end_col = start_col + len(data_rows[0]) - 1  # Column E (Product)
        range_name = f"{worksheet_name}!B{next_row}:{chr(ord('A') + end_col - 1)}{next_row + len(data_rows) - 1}"
        
        # First, upload the data
        body = {
            'values': data_rows
        }
        
        result = self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        # Then, apply formatting to the uploaded cells
        self._apply_cell_formatting(worksheet_name, next_row, next_row + len(data_rows) - 1, start_col, end_col)
        
        print(f"Updated {result.get('updatedCells')} cells in Google Sheets at row {next_row} with formatting")
        return result
    
    def _find_next_empty_row(self, worksheet_name: str) -> int:
        """Find the next empty row in the worksheet"""
        try:
            # Get all data in the worksheet starting from row 2 (skip header row)
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{worksheet_name}!B2:B"  # Check column B starting from row 2
            ).execute()
            
            values = result.get('values', [])
            
            # Find the first empty row
            for i in range(len(values)):
                if not values[i] or not values[i][0].strip():
                    return i + 2  # +2 because we started from row 2 and Google Sheets is 1-indexed
            
            # If no empty rows found, return the next row after the last data
            return len(values) + 2
            
        except Exception as e:
            print(f"Warning: Could not find next empty row, using row 4: {e}")
            return 4  # Default to row 4 if there's an error (after header row)
    
    def _apply_cell_formatting(self, worksheet_name: str, start_row: int, end_row: int, start_col: int, end_col: int):
        """Apply formatting to cells (center alignment and borders)"""
        try:
            # Convert column numbers to letters
            start_col_letter = chr(ord('A') + start_col - 1)
            end_col_letter = chr(ord('A') + end_col - 1)
            
            # Define the range for formatting
            range_name = f"{worksheet_name}!{start_col_letter}{start_row}:{end_col_letter}{end_row}"
            
            # Create formatting requests
            requests = [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": self._get_sheet_id(worksheet_name),
                            "startRowIndex": start_row - 1,  # Convert to 0-based index
                            "endRowIndex": end_row,
                            "startColumnIndex": start_col - 1,  # Convert to 0-based index
                            "endColumnIndex": end_col
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "horizontalAlignment": "CENTER",
                                "verticalAlignment": "MIDDLE",
                                "borders": {
                                    "top": {"style": "SOLID", "width": 1},
                                    "bottom": {"style": "SOLID", "width": 1},
                                    "left": {"style": "SOLID", "width": 1},
                                    "right": {"style": "SOLID", "width": 1}
                                }
                            }
                        },
                        "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment,borders)"
                    }
                }
            ]
            
            # Apply formatting
            body = {"requests": requests}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            print(f"Applied formatting to range {range_name}")
            
        except Exception as e:
            print(f"Warning: Could not apply formatting: {e}")
    
    def _get_sheet_id(self, worksheet_name: str) -> int:
        """Get the sheet ID for the given worksheet name"""
        try:
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            sheets = spreadsheet.get('sheets', [])
            
            for sheet in sheets:
                if sheet.get('properties', {}).get('title') == worksheet_name:
                    return sheet.get('properties', {}).get('sheetId', 0)
            
            # If not found, return 0 (first sheet)
            return 0
            
        except Exception as e:
            print(f"Warning: Could not get sheet ID, using 0: {e}")
            return 0
    
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
    
    def delete_last_uploaded_rows(self, worksheet_name: str, row_count: int) -> tuple[bool, str]:
        """
        Delete the last uploaded rows from Google Sheets
        
        Args:
            worksheet_name: Name of the worksheet
            row_count: Number of rows to delete from the end
            
        Returns:
            (success, message)
        """
        if not self.is_available():
            return False, "Google Sheets service is not available."
        
        try:
            # Get the current data range to find the last rows
            range_name = f"{worksheet_name}!A:Z"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return False, "No data found in the worksheet."
            
            # Find the last non-empty row
            last_row = len(values)
            
            # Calculate the range to delete (last row_count rows)
            start_row = max(1, last_row - row_count + 1)
            end_row = last_row
            
            # Delete the rows
            delete_range = f"{worksheet_name}!{start_row}:{end_row}"
            
            # Clear the range
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=delete_range
            ).execute()
            
            return True, f"Successfully deleted {row_count} rows from {worksheet_name} (rows {start_row}-{end_row})"
            
        except Exception as e:
            return False, f"Error deleting rows: {str(e)}"
    
    def _extract_volume_from_name(self, name: str) -> float:
        """Extract volume/weight from product name and convert to base units (kg/l)"""
        import re
        
        if not name:
            return 0.0
        
        # Patterns to match various volume/weight indicators with conversion factors
        patterns = [
            # Base units (kg, l) - no conversion needed
            (r'(\d+[,.]?\d*)\s*kg', 1.0),  # kg (with comma or dot as decimal separator)
            (r'(\d+[,.]?\d*)\s*кг', 1.0),  # кг (Russian)
            (r'(\d+[,.]?\d*)\s*l', 1.0),   # liters
            (r'(\d+[,.]?\d*)\s*л', 1.0),   # литры (Russian)
            # Small units (g, ml) - convert to base units (multiply by 0.001)
            (r'(\d+[,.]?\d*)\s*ml', 0.001),  # milliliters -> liters
            (r'(\d+[,.]?\d*)\s*мл', 0.001),  # миллилитры -> литры (Russian)
            (r'(\d+[,.]?\d*)\s*g', 0.001),   # grams -> kg
            (r'(\d+[,.]?\d*)\s*г', 0.001),   # граммы -> кг (Russian)
        ]
        
        for pattern, conversion_factor in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                volume_str = match.group(1)
                # Replace comma with dot for proper float conversion
                volume_str = volume_str.replace(',', '.')
                try:
                    volume = float(volume_str)
                    return volume * conversion_factor
                except ValueError:
                    continue
        
        return 0.0