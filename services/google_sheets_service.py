"""
Service for uploading data to Google Sheets
"""
import json
import aiofiles
import asyncio
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
        """Initialize Google Sheets API service - supports both file and environment variable"""
        if not self.spreadsheet_id:
            print("⚠️ Google Sheets spreadsheet ID not configured. Service will be disabled.")
            return
        
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            
            credentials = None
            
            # First try to load from new environment variable (for cloud deployment)
            google_sheets_credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON')
            if google_sheets_credentials_json:
                print(f"🔍 Found GOOGLE_SHEETS_CREDENTIALS_JSON (length: {len(google_sheets_credentials_json)})")
                try:
                    import json
                    credentials_info = json.loads(google_sheets_credentials_json)
                    print(f"🔍 Parsed credentials JSON successfully")
                    print(f"  - Project ID: {credentials_info.get('project_id', 'Не найден')}")
                    print(f"  - Client Email: {credentials_info.get('client_email', 'Не найден')}")
                    print(f"  - Type: {credentials_info.get('type', 'Не найден')}")
                    
                    credentials = Credentials.from_service_account_info(
                        credentials_info,
                        scopes=['https://www.googleapis.com/auth/spreadsheets']
                    )
                    print("✅ Google Sheets credentials loaded from GOOGLE_SHEETS_CREDENTIALS_JSON")
                except Exception as e:
                    print(f"⚠️ Error loading credentials from GOOGLE_SHEETS_CREDENTIALS_JSON: {e}")
                    import traceback
                    traceback.print_exc()
                    credentials = None
            else:
                print("🔍 GOOGLE_SHEETS_CREDENTIALS_JSON not found in environment")
                
                # Fallback to old environment variable
                google_credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
                if google_credentials_json:
                    print(f"🔍 Found GOOGLE_APPLICATION_CREDENTIALS_JSON (length: {len(google_credentials_json)})")
                    try:
                        import json
                        credentials_info = json.loads(google_credentials_json)
                        print(f"🔍 Parsed credentials JSON successfully")
                        print(f"  - Project ID: {credentials_info.get('project_id', 'Не найден')}")
                        print(f"  - Client Email: {credentials_info.get('client_email', 'Не найден')}")
                        print(f"  - Type: {credentials_info.get('type', 'Не найден')}")
                        
                        credentials = Credentials.from_service_account_info(
                            credentials_info,
                            scopes=['https://www.googleapis.com/auth/spreadsheets']
                        )
                        print("✅ Google Sheets credentials loaded from GOOGLE_APPLICATION_CREDENTIALS_JSON (fallback)")
                    except Exception as e:
                        print(f"⚠️ Error loading credentials from GOOGLE_APPLICATION_CREDENTIALS_JSON: {e}")
                        import traceback
                        traceback.print_exc()
                        credentials = None
                else:
                    print("🔍 GOOGLE_APPLICATION_CREDENTIALS_JSON also not found in environment")
            
            # If environment variable failed, try file path
            if not credentials and self.credentials_path and os.path.exists(self.credentials_path):
                try:
                    credentials = Credentials.from_service_account_file(
                        self.credentials_path,
                        scopes=['https://www.googleapis.com/auth/spreadsheets']
                    )
                    print("✅ Google Sheets credentials loaded from file")
                except Exception as e:
                    print(f"⚠️ Error loading credentials from file: {e}")
                    credentials = None
            
            if not credentials:
                print("⚠️ Google Sheets credentials not found. Service will be disabled.")
                print("💡 Check GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable or credentials file")
                return
            
            self.service = build('sheets', 'v4', credentials=credentials)
            print("✅ Google Sheets service initialized successfully")
            print(f"🔍 Spreadsheet ID: {self.spreadsheet_id}")
            
        except Exception as e:
            print(f"❌ Error initializing Google Sheets service: {e}")
            self.service = None
    
    def is_available(self) -> bool:
        """Check if Google Sheets service is available"""
        return self.service is not None and self.spreadsheet_id is not None
    
    def upload_receipt_data(self, 
                           receipt_data: ReceiptData, 
                           matching_result: IngredientMatchingResult,
                           worksheet_name: str = "Receipts",
                           column_mapping: Dict[str, str] = None,
                           data_start_row: int = 1) -> tuple[bool, str]:
        """
        Upload receipt data to Google Sheets with dynamic column mapping from Firestore
        
        Args:
            receipt_data: Processed receipt data
            matching_result: Ingredient matching results
            worksheet_name: Name of the worksheet to upload to
            column_mapping: Dictionary mapping field names to column letters from Firestore config
            data_start_row: Starting row for data (default: 1)
            
        Returns:
            (success, message)
        """
        if not self.is_available():
            return False, "Google Sheets service is not available. Please check configuration."
        
        try:
            # Always use dynamic column mapping
            if column_mapping:
                print(f"📊 Using dynamic column mapping: {column_mapping}")
            else:
                print("📊 Using default column mapping (no custom mapping provided)")
                # Use default mapping if none provided
                column_mapping = {
                    'check_date': 'A',
                    'product_name': 'B',
                    'quantity': 'C',
                    'price_per_item': 'D',
                    'total_price': 'E'
                }
            
            # Create data rows using dynamic column mapping
            data_rows = self._create_sheets_data(receipt_data, matching_result, column_mapping)
            # Upload with proper column positioning
            result = self._upload_to_sheets(data_rows, worksheet_name, data_start_row, column_mapping)
            
            return True, f"Successfully uploaded {len(data_rows)} items to Google Sheets"
            
        except Exception as e:
            return False, f"Error uploading to Google Sheets: {str(e)}"
    
    
    
    def _create_sheets_data(self, receipt_data: ReceiptData, matching_result: IngredientMatchingResult, column_mapping: Dict[str, str] = None) -> List[List[Any]]:
        """Create data rows for Google Sheets using dynamic column mapping"""
        data_rows = []
        
        # Use default mapping if none provided (backward compatibility)
        if not column_mapping:
            column_mapping = {
                'check_date': 'B',
                'quantity': 'C', 
                'price_per_item': 'D',
                'product_name': 'E'
            }
        
        print(f"📊 Creating data with column mapping: {column_mapping}")
        
        # Add data rows (no header, just data)
        for i, item in enumerate(receipt_data.items):
            # Get matching result for this item
            match = None
            if i < len(matching_result.matches):
                match = matching_result.matches[i]
            
            # Skip items without matched ingredients
            if not match or not match.matched_ingredient_name:
                continue
            
            # Create row data dictionary based on column mapping
            row_data = {}
            
            # Process each field in the column mapping
            for field_name, column_letter in column_mapping.items():
                value = self._get_field_value(field_name, item, match, receipt_data)
                row_data[column_letter] = value
            
            # Convert row_data dictionary to array with proper column order
            row_array = self._convert_row_data_to_array(row_data, column_mapping)
            data_rows.append(row_array)
        
        return data_rows
    
    def _get_field_value(self, field_name: str, item: ReceiptItem, match: IngredientMatch, receipt_data: ReceiptData) -> str:
        """Get formatted value for a specific field based on field name"""
        if field_name == 'check_date':
            return datetime.now().strftime('%d.%m.%Y')
        
        elif field_name == 'product_name':
            return match.matched_ingredient_name if match else ""
        
        elif field_name == 'quantity':
            quantity = item.quantity if item.quantity is not None else 0
            
            # Extract volume from product name and multiply by quantity
            volume_from_name = self._extract_volume_from_name(item.name)
            if volume_from_name > 0:
                # Multiply extracted volume by quantity
                total_volume = volume_from_name * quantity
                if total_volume == int(total_volume):
                    return f"{int(total_volume)} kg"
                else:
                    # Round to 2 decimal places
                    return f"{total_volume:.2f} kg"
            elif quantity > 0:
                # Fallback to original behavior if no volume found in name
                if quantity == int(quantity):
                    return f"{int(quantity)} kg"
                else:
                    # Round to 2 decimal places
                    return f"{quantity:.2f} kg"
            else:
                return ""
        
        elif field_name in ['price_per_item', 'unit_price']:
            if item.price is not None and item.price > 0:
                # Format price with spaces for thousands separator, preserving decimal places
                if item.price == int(item.price):
                    # If it's a whole number, show it as integer
                    price_formatted = f"{int(item.price):,}".replace(",", " ")
                else:
                    # If it has decimal places, show them
                    price_formatted = f"{item.price:,.3f}".replace(",", " ").rstrip('0').rstrip('.')
                return f"{price_formatted}Rp"
            return ""
        
        elif field_name == 'total_price':
            if item.total is not None and item.total > 0:
                # Format total price with spaces for thousands separator
                if item.total == int(item.total):
                    price_formatted = f"{int(item.total):,}".replace(",", " ")
                else:
                    price_formatted = f"{item.total:,.3f}".replace(",", " ").rstrip('0').rstrip('.')
                return f"{price_formatted}Rp"
            return ""
        
        elif field_name == 'store_name':
            # ReceiptData doesn't have store_name field, return empty
            return ""
        
        elif field_name == 'receipt_number':
            # ReceiptData doesn't have receipt_number field, return empty
            return ""
        
        elif field_name == 'ingredient_name':
            # Return the matched ingredient name
            return match.matched_ingredient_name if match else ""
        
        elif field_name == 'original_name':
            # Return the original product name from receipt
            return item.name if item.name else ""
        
        elif field_name == 'match_status':
            # Return the match status
            return match.match_status.value if match else "no_match"
        
        else:
            # Unknown field, return empty string
            print(f"⚠️ Unknown field in column mapping: {field_name}")
            return ""
    
    def _convert_row_data_to_array(self, row_data: Dict[str, str], column_mapping: Dict[str, str]) -> List[str]:
        """Convert row_data dictionary to array with proper column order, preserving empty columns"""
        # Find the range of columns used
        column_letters = list(column_mapping.values())
        if not column_letters:
            return []
        
        # Convert column letters to indices (A=0, B=1, etc.)
        min_col = min(ord(col) - ord('A') for col in column_letters)
        max_col = max(ord(col) - ord('A') for col in column_letters)
        
        # Create array that spans from min_col to max_col (inclusive)
        # This preserves empty columns between used columns
        row_array = [''] * (max_col - min_col + 1)
        
        # Fill in the values at correct positions
        for column_letter, value in row_data.items():
            col_index = ord(column_letter) - ord('A')
            array_index = col_index - min_col
            if 0 <= array_index < len(row_array):
                row_array[array_index] = value
        
        print(f"📊 Converted row data: {row_data}")
        print(f"📊 Column mapping: {column_mapping}")
        print(f"📊 Result array: {row_array}")
        print(f"📊 Array spans columns {chr(ord('A') + min_col)} to {chr(ord('A') + max_col)}")
        
        return row_array
    
    def _upload_to_sheets(self, data_rows: List[List[Any]], worksheet_name: str, data_start_row: int = 1, column_mapping: Dict[str, str] = None):
        """Upload data to Google Sheets by appending to the next empty row with formatting"""
        import time
        
        if not data_rows:
            print("⚠️ No data rows to upload")
            return {"updatedCells": 0}
        
        # Validate data rows structure
        if not all(isinstance(row, list) for row in data_rows):
            print("❌ Invalid data structure: all rows must be lists")
            raise ValueError("Invalid data structure: all rows must be lists")
        
        # Check if all rows have the same length
        if len(data_rows) > 1:
            first_row_length = len(data_rows[0])
            for i, row in enumerate(data_rows[1:], 1):
                if len(row) != first_row_length:
                    print(f"⚠️ Row {i} has different length ({len(row)}) than first row ({first_row_length})")
                    # Pad shorter rows with empty strings
                    while len(row) < first_row_length:
                        row.append('')
                    # Truncate longer rows
                    if len(row) > first_row_length:
                        data_rows[i] = row[:first_row_length]
        
        # Use append method instead of finding empty row to avoid quota issues
        # This is more efficient and avoids the need to check existing data
        try:
            # First check if the worksheet exists, if not use the first sheet
            try:
                # Try to get the sheet to verify it exists
                spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
                sheets = spreadsheet.get('sheets', [])
                
                # Check if the worksheet exists
                sheet_exists = any(sheet.get('properties', {}).get('title') == worksheet_name for sheet in sheets)
                
                if not sheet_exists and sheets:
                    # Use the first available sheet if the specified one doesn't exist
                    actual_worksheet_name = sheets[0].get('properties', {}).get('title', 'Sheet1')
                    print(f"⚠️ Worksheet '{worksheet_name}' not found, using '{actual_worksheet_name}' instead")
                    worksheet_name = actual_worksheet_name
                
            except Exception as e:
                print(f"⚠️ Could not verify worksheet existence: {e}")
            
            # Find the next empty row in the specified columns to avoid overwriting existing data
            next_row = self._find_next_empty_row(worksheet_name, data_start_row, column_mapping)
            
            # Calculate the range for the data based on column mapping
            if data_rows and len(data_rows[0]) > 0 and column_mapping:
                # Get the column range from the column mapping
                column_letters = list(column_mapping.values())
                if column_letters:
                    min_col = min(ord(col) - ord('A') for col in column_letters)
                    max_col = max(ord(col) - ord('A') for col in column_letters)
                    
                    # Convert to column letters (1-based)
                    start_col_letter = chr(ord('A') + min_col)
                    end_col_letter = chr(ord('A') + max_col)
                    
                    # Create range for the specific data area
                    range_name = f"{worksheet_name}!{start_col_letter}{next_row}:{end_col_letter}{next_row + len(data_rows) - 1}"
                else:
                    # Fallback to A column if no mapping
                    range_name = f"{worksheet_name}!A{next_row}:A{next_row + len(data_rows) - 1}"
            else:
                # Fallback to A column if no data or no mapping
                range_name = f"{worksheet_name}!A{next_row}:A{next_row + len(data_rows) - 1}" if data_rows else f"{worksheet_name}!A{next_row}:A{next_row}"
            
            print(f"📊 Uploading to range: {range_name}")
            
            # Use update method instead of append to have precise control over positioning
            body = {
                'values': data_rows
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            # Get the range that was updated
            updated_range = result.get('updates', {}).get('updatedRange', '')
            if updated_range:
                # Extract row numbers from the updated range
                # Format: "SheetName!A2:A5" -> extract 2 and 5
                import re
                match = re.search(r'A(\d+):A(\d+)', updated_range)
                if match:
                    start_row = int(match.group(1))
                    end_row = int(match.group(2))
                    start_col = 1
                    end_col = len(data_rows[0]) if data_rows else 1
                    
                    # Apply formatting to the uploaded cells (with retry)
                    self._apply_cell_formatting_with_retry(worksheet_name, start_row, end_row, start_col, end_col)
            
            print(f"Appended {len(data_rows)} rows to Google Sheets")
            return result
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                print(f"⚠️ API quota exceeded, trying fallback method...")
                # Fallback: try to find empty row with retry
                return self._upload_to_sheets_fallback(data_rows, worksheet_name, data_start_row, column_mapping)
            else:
                print(f"❌ Upload error: {e}")
                raise e

    def _upload_to_sheets_fallback(self, data_rows: List[List[Any]], worksheet_name: str, data_start_row: int = 1, column_mapping: Dict[str, str] = None):
        """Fallback upload method when append fails"""
        import time
        
        if not data_rows:
            return {"updatedCells": 0}
        
        # Find the next empty row
        next_row = self._find_next_empty_row(worksheet_name, data_start_row, column_mapping)
        
        # Calculate the range for appending data dynamically
        if data_rows and len(data_rows[0]) > 0 and column_mapping:
            # Get the column range from the column mapping
            column_letters = list(column_mapping.values())
            if column_letters:
                min_col = min(ord(col) - ord('A') for col in column_letters)
                max_col = max(ord(col) - ord('A') for col in column_letters)
                
                # Convert to column letters (1-based)
                start_col_letter = chr(ord('A') + min_col)
                end_col_letter = chr(ord('A') + max_col)
                
                # Create range for the specific data area
                range_name = f"{worksheet_name}!{start_col_letter}{next_row}:{end_col_letter}{next_row + len(data_rows) - 1}"
            else:
                # Fallback to A column if no mapping
                range_name = f"{worksheet_name}!A{next_row}:A{next_row + len(data_rows) - 1}"
        elif data_rows and len(data_rows[0]) > 0:
            # Fallback to A column if no mapping provided
            range_name = f"{worksheet_name}!A{next_row}:A{next_row + len(data_rows) - 1}"
        else:
            return {"updatedCells": 0}
        
        # Upload data with retry logic
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                body = {
                    'values': data_rows
                }
                
                result = self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body=body
                ).execute()
                
                # Apply formatting to the uploaded cells (with retry)
                self._apply_cell_formatting_with_retry(worksheet_name, next_row, next_row + len(data_rows) - 1, start_col, end_col)
                
                print(f"Updated {result.get('updatedCells')} cells in Google Sheets at row {next_row} with formatting")
                return result
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower():
                    if attempt < max_retries - 1:
                        print(f"⚠️ API quota exceeded during fallback upload (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        print(f"❌ API quota exceeded after {max_retries} attempts, upload failed")
                        raise e
                else:
                    print(f"❌ Upload error: {e}")
                    raise e
        
        return {"updatedCells": 0}
    
    def _find_next_empty_row(self, worksheet_name: str, data_start_row: int = 1, column_mapping: Dict[str, str] = None) -> int:
        """Find the next empty row in the specified columns with retry logic"""
        import time
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                if column_mapping:
                    # Get the columns from mapping
                    column_letters = list(column_mapping.values())
                    if column_letters:
                        min_col = min(ord(col) - ord('A') for col in column_letters)
                        max_col = max(ord(col) - ord('A') for col in column_letters)
                        
                        # Convert to column letters
                        start_col_letter = chr(ord('A') + min_col)
                        end_col_letter = chr(ord('A') + max_col)
                        
                        # Always search from row 1 to find empty rows, regardless of data_start_row
                        range_name = f"{worksheet_name}!{start_col_letter}1:{end_col_letter}"
                    else:
                        # Fallback to column A if no mapping - search from row 1
                        range_name = f"{worksheet_name}!A1:A"
                else:
                    # Fallback to column A if no mapping provided - search from row 1
                    range_name = f"{worksheet_name}!A1:A"
                
                print(f"📊 Checking for empty rows in range: {range_name}")
                
                result = self.service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name
                ).execute()
                
                values = result.get('values', [])
                
                # Find the first row where ALL specified columns are empty
                for i in range(len(values)):
                    row = values[i]
                    is_empty = True
                    
                    if column_mapping:
                        # Check only the columns specified in mapping
                        for col_letter in column_mapping.values():
                            col_index = ord(col_letter) - ord('A')
                            if col_index < len(row) and row[col_index].strip():
                                is_empty = False
                                break
                    else:
                        # Check only first column if no mapping
                        if len(row) > 0 and row[0].strip():
                            is_empty = False
                    
                    if is_empty:
                        # Convert 0-based index to 1-based row number
                        row_number = i + 1
                        # Ensure we don't return a row before data_start_row
                        if row_number >= data_start_row:
                            print(f"📊 Found empty row at position {row_number}")
                            return row_number
                
                # If no empty rows found, return the next row after the last data
                next_row = len(values) + 1
                # Ensure we don't return a row before data_start_row
                if next_row < data_start_row:
                    next_row = data_start_row
                print(f"📊 No empty rows found, using row {next_row}")
                return next_row
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower():
                    if attempt < max_retries - 1:
                        print(f"⚠️ API quota exceeded (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        print(f"⚠️ API quota exceeded after {max_retries} attempts, using fallback row")
                        return max(data_start_row, 1)
                else:
                    print(f"Warning: Could not find next empty row, using row {max(data_start_row, 1)}: {e}")
                    return max(data_start_row, 1)
        
        return max(data_start_row, 1)  # Fallback
    
    def _apply_cell_formatting_with_retry(self, worksheet_name: str, start_row: int, end_row: int, start_col: int, end_col: int):
        """Apply formatting to cells with retry logic"""
        import time
        
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                self._apply_cell_formatting(worksheet_name, start_row, end_row, start_col, end_col)
                return  # Success
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower():
                    if attempt < max_retries - 1:
                        print(f"⚠️ API quota exceeded during formatting (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        print(f"⚠️ API quota exceeded after {max_retries} attempts, skipping formatting")
                        return  # Skip formatting if quota exceeded
                else:
                    print(f"Warning: Could not apply formatting: {e}")
                    return  # Skip formatting on other errors

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
    
    def delete_last_uploaded_rows(self, worksheet_name: str, row_count: int, data_start_row: int = 1) -> tuple[bool, str]:
        """
        Delete the last uploaded rows from Google Sheets
        
        Args:
            worksheet_name: Name of the worksheet
            row_count: Number of rows to delete from the end
            data_start_row: Starting row where data was uploaded (default: 1)
            
        Returns:
            (success, message)
        """
        if not self.is_available():
            return False, "Google Sheets service is not available."
        
        try:
            # First, check if the worksheet exists
            try:
                # Try to get worksheet info
                spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
                worksheet_found = False
                for sheet in spreadsheet.get('sheets', []):
                    if sheet['properties']['title'] == worksheet_name:
                        worksheet_found = True
                        break
                
                if not worksheet_found:
                    return False, f"Worksheet '{worksheet_name}' not found in the spreadsheet"
                    
            except Exception as e:
                return False, f"Error checking worksheet existence: {str(e)}"
            
            # Get the current data range to find the last rows
            # Use the same format as other functions in this service
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
            # Ensure we don't delete header rows (before data_start_row)
            start_row = max(data_start_row, last_row - row_count + 1)
            end_row = last_row
            
            if start_row > end_row:
                return False, "No data rows to delete (all data is before data_start_row)"
            
            # Delete the rows - use same format as other functions
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