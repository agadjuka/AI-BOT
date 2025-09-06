"""
Service for generating supply files for Poster
"""
import pandas as pd
import io
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

from models.receipt import ReceiptData, ReceiptItem
from models.ingredient_matching import IngredientMatchingResult, IngredientMatch


class FileGeneratorService:
    """Service for generating supply files in various formats"""
    
    def __init__(self):
        self.supported_formats = ['xlsx']
    
    def generate_supply_file(self, 
                           receipt_data: ReceiptData, 
                           matching_result: IngredientMatchingResult,
                           file_format: str = 'xlsx',
                           supplier: str = "Supplier",
                           storage_location: str = "Storage 1",
                           comment: str = "") -> bytes:
        """
        Generate supply file for Poster
        
        Args:
            receipt_data: Processed receipt data
            matching_result: Ingredient matching results
            file_format: Output format ('xlsx')
            supplier: Supplier name
            storage_location: Storage location
            comment: Additional comment
            
        Returns:
            File content as bytes
        """
        if file_format not in self.supported_formats:
            raise ValueError(f"Unsupported format: {file_format}. Supported: {self.supported_formats}")
        
        # Create supply data from receipt and matching
        supply_data = self._create_supply_data(receipt_data, matching_result)
        
        # Create DataFrame
        df = pd.DataFrame(supply_data)
        
        # Add metadata
        metadata = self._create_metadata(supplier, storage_location, comment, matching_result)
        
        if file_format == 'xlsx':
            return self._generate_xlsx(df, metadata)
        else:
            raise ValueError(f"Unsupported format: {file_format}. Only 'xlsx' is supported.")
    
    def _create_supply_data(self, receipt_data: ReceiptData, matching_result: IngredientMatchingResult) -> List[Dict[str, Any]]:
        """Create supply data from receipt and matching results"""
        supply_data = []
        
        print(f"DEBUG: Creating supply data for {len(receipt_data.items)} items")
        
        for i, item in enumerate(receipt_data.items):
            # Get matching result for this item
            match = None
            if i < len(matching_result.matches):
                match = matching_result.matches[i]
            
            # Use matched ingredient name if available (any status except NO_MATCH), 
            # otherwise use receipt item name as fallback
            if match and match.match_status.value != 'no_match' and match.matched_ingredient_name:
                name = match.matched_ingredient_name
                print(f"DEBUG: Item {i+1}: Using matched name '{name}' (status: {match.match_status.value})")
            else:
                name = item.name
                print(f"DEBUG: Item {i+1}: Using receipt name '{name}' (no match or no matched name)")
            
            supply_item = {
                'Name': name,
                'Quantity': item.quantity if item.quantity is not None else 0,
                'Price for piece': item.price if item.price is not None else 0,
                'Total amount': item.total if item.total is not None else 0
            }
            
            supply_data.append(supply_item)
        
        print(f"DEBUG: Created supply data with {len(supply_data)} items")
        return supply_data
    
    def _create_metadata(self, supplier: str, storage_location: str, comment: str, 
                        matching_result: IngredientMatchingResult = None) -> Dict[str, Any]:
        """Create metadata for the supply file"""
        metadata = {
            'supplier': supplier,
            'storage_location': storage_location,
            'comment': comment,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'generated_by': 'AI Bot'
        }
        
        # Add matching statistics if available
        if matching_result:
            metadata.update({
                'total_items': len(matching_result.matches),
                'exact_matches': matching_result.exact_matches,
                'partial_matches': matching_result.partial_matches,
                'no_matches': matching_result.no_matches,
                'matching_rate': f"{(matching_result.exact_matches + matching_result.partial_matches) / len(matching_result.matches) * 100:.1f}%"
            })
        
        return metadata
    
    def _generate_xlsx(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> bytes:
        """Generate XLSX file"""
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write main data
            df.to_excel(writer, sheet_name='Supply Items', index=False)
            
            # Create metadata sheet
            metadata_df = pd.DataFrame(list(metadata.items()), columns=['Field', 'Value'])
            metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
        
        output.seek(0)
        return output.getvalue()
    
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        return self.supported_formats.copy()
    
    def validate_data(self, receipt_data: ReceiptData, matching_result: IngredientMatchingResult) -> tuple[bool, str]:
        """
        Validate data before generating file
        
        Returns:
            (is_valid, error_message)
        """
        if not receipt_data or not receipt_data.items:
            return False, "Нет данных о товарах в чеке"
        
        if not matching_result or not matching_result.matches:
            return False, "Нет данных о сопоставлении ингредиентов"
        
        if len(receipt_data.items) != len(matching_result.matches):
            return False, "Количество товаров в чеке не соответствует количеству сопоставленных ингредиентов"
        
        # Check if all items have valid data
        for i, item in enumerate(receipt_data.items):
            if not item.name or item.name.strip() == "":
                return False, f"Товар в строке {i+1} не имеет названия"
            
            if item.quantity is None or item.quantity <= 0:
                return False, f"Товар '{item.name}' имеет некорректное количество"
            
            if item.price is None or item.price < 0:
                return False, f"Товар '{item.name}' имеет некорректную цену"
        
        # Check if we have at least some matched ingredients
        matched_count = sum(1 for match in matching_result.matches 
                           if match.match_status.value != 'no_match' and match.matched_ingredient_name)
        
        print(f"DEBUG: Validation - Total matches: {len(matching_result.matches)}, Matched count: {matched_count}")
        for i, match in enumerate(matching_result.matches):
            print(f"DEBUG: Match {i}: '{match.receipt_item_name}' -> '{match.matched_ingredient_name}' (status: {match.match_status}, score: {match.similarity_score})")
        
        if matched_count == 0:
            return False, "Нет сопоставленных ингредиентов. Необходимо выполнить сопоставление товаров с ингредиентами Poster."
        
        return True, ""
    
    def generate_excel_file(self, receipt_data: ReceiptData, matching_result: IngredientMatchingResult) -> Optional[str]:
        """
        Generate Excel file with the same data format as Google Sheets upload
        
        Args:
            receipt_data: Processed receipt data
            matching_result: Ingredient matching results
            
        Returns:
            Path to generated file or None if error
        """
        try:
            # Create data in Google Sheets format (Date, Volume, Harga, Product)
            data_rows = self._create_google_sheets_format_data(receipt_data, matching_result)
            
            if not data_rows:
                print("DEBUG: No data to generate Excel file")
                return None
            
            # Create DataFrame without headers (just data)
            df = pd.DataFrame(data_rows)
            
            # Generate temporary file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"receipt_data_{timestamp}.xlsx"
            filepath = os.path.join(os.getcwd(), filename)
            
            # Write to Excel file without headers
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Receipt Data', index=False, header=False)
                
                # Add metadata sheet
                metadata = {
                    'Generated at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Total items': len(data_rows),
                    'Generated by': 'AI Bot'
                }
                metadata_df = pd.DataFrame(list(metadata.items()), columns=['Field', 'Value'])
                metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
            
            print(f"DEBUG: Generated Excel file: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error generating Excel file: {e}")
            return None
    
    def _create_google_sheets_format_data(self, receipt_data: ReceiptData, matching_result: IngredientMatchingResult) -> List[List[Any]]:
        """Create data in Google Sheets format (Date, Volume, Harga, Product)"""
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
            
            # Format quantity with "kg" (same as Google Sheets)
            quantity_str = ""
            if item.quantity is not None and item.quantity > 0:
                quantity_str = f"{item.quantity:.2f} kg"
            
            # Format price with "Rp" suffix (same as Google Sheets)
            price_str = ""
            if item.price is not None and item.price > 0:
                # Format price with spaces for thousands separator
                price_formatted = f"{item.price:,.0f}".replace(",", " ")
                price_str = f"{price_formatted}Rp"
            
            # Use matched ingredient name
            product_name = match.matched_ingredient_name
            
            data_rows.append([current_date, quantity_str, price_str, product_name])
        
        return data_rows