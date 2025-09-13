"""
Google Sheets Manager for user table management
Handles user-specific Google Sheets configuration and column mapping
"""
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter


class GoogleSheetsManager:
    """Manager for user Google Sheets configuration and column mapping"""
    
    def __init__(self, db_instance: Optional[firestore.Client] = None):
        """
        Initialize GoogleSheetsManager with Firestore client
        
        Args:
            db_instance: Firestore client instance. If None, will try to get global instance
        """
        self.db = db_instance
        if not self.db:
            # Try to get global Firestore instance from main.py
            try:
                import main
                self.db = main.db
            except (ImportError, AttributeError):
                print("⚠️ GoogleSheetsManager initialized without Firestore - operations will fail")
        
        if self.db:
            print("✅ GoogleSheetsManager initialized with Firestore instance")
        else:
            print("❌ GoogleSheetsManager initialized without Firestore - operations will fail")
    
    async def add_user_sheet(
        self, 
        user_id: int, 
        sheet_url: str, 
        sheet_id: str, 
        friendly_name: str
    ) -> Union[str, bool]:
        """
        Add a new Google Sheet for a user with default column mapping
        
        Args:
            user_id: Telegram user ID
            sheet_url: Full URL of the Google Sheet
            sheet_id: Google Sheets document ID
            friendly_name: User-friendly name for the sheet
            
        Returns:
            Document ID of created sheet or True if successful, False if failed
        """
        if not self.db:
            print("❌ Firestore not available")
            return False
        
        try:
            # Check if this is the first sheet for the user
            user_ref = self.db.collection('users').document(str(user_id))
            sheets_ref = user_ref.collection('google_sheets')
            
            # Get existing sheets to determine if this should be default
            existing_sheets = sheets_ref.get()
            is_default = len(existing_sheets) == 0
            
            # Create default column mapping to match the actual sheet headers
            # Headers are in row 2: B=Date, C=Volume, D=Harga, E=Product
            default_mapping = {
                "check_date": "B",      # Date column
                "quantity": "C",        # Volume column  
                "price_per_item": "D",  # Harga (Price) column
                "product_name": "E"     # Product column
            }
            
            # Prepare sheet data
            sheet_data = {
                "sheet_url": sheet_url,
                "sheet_id": sheet_id,
                "friendly_name": friendly_name,
                "is_default": is_default,
                "created_at": datetime.utcnow(),
                "data_start_row": 2,
                "column_mapping": default_mapping
            }
            
            # Add the sheet document
            doc_ref = sheets_ref.add(sheet_data)
            sheet_doc_id = doc_ref[1].id
            
            print(f"✅ Added sheet '{friendly_name}' for user {user_id} (default: {is_default})")
            return sheet_doc_id
            
        except Exception as e:
            print(f"❌ Error adding user sheet: {e}")
            return False
    
    async def add_user_sheet_with_mapping(
        self, 
        user_id: int, 
        sheet_url: str, 
        sheet_id: str, 
        friendly_name: str,
        column_mapping: Dict[str, str],
        start_row: int
    ) -> Union[str, bool]:
        """
        Add a new Google Sheet for a user with custom column mapping
        
        Args:
            user_id: Telegram user ID
            sheet_url: Full URL of the Google Sheet
            sheet_id: Google Sheets document ID
            friendly_name: User-friendly name for the sheet
            column_mapping: Custom column mapping dictionary
            start_row: Starting row for data
            
        Returns:
            Document ID of created sheet or True if successful, False if failed
        """
        if not self.db:
            print("❌ Firestore not available")
            return False
        
        try:
            # Check if this is the first sheet for the user
            user_ref = self.db.collection('users').document(str(user_id))
            sheets_ref = user_ref.collection('google_sheets')
            
            # Get existing sheets to determine if this should be default
            existing_sheets = sheets_ref.get()
            is_default = len(existing_sheets) == 0
            
            # Prepare sheet data with custom mapping
            sheet_data = {
                "sheet_url": sheet_url,
                "sheet_id": sheet_id,
                "friendly_name": friendly_name,
                "is_default": is_default,
                "created_at": datetime.utcnow(),
                "data_start_row": start_row,
                "column_mapping": column_mapping
            }
            
            # Add the sheet document
            doc_ref = sheets_ref.add(sheet_data)
            sheet_doc_id = doc_ref[1].id
            
            print(f"✅ Added sheet '{friendly_name}' with custom mapping for user {user_id} (default: {is_default})")
            return sheet_doc_id
            
        except Exception as e:
            print(f"❌ Error adding user sheet with mapping: {e}")
            return False
    
    async def get_user_sheets(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all Google Sheets for a user
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            List of dictionaries containing sheet information
        """
        if not self.db:
            print("❌ Firestore not available")
            return []
        
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            sheets_ref = user_ref.collection('google_sheets')
            
            # Get all sheets for the user
            sheets = sheets_ref.get()
            
            result = []
            for sheet in sheets:
                sheet_data = sheet.to_dict()
                sheet_data['doc_id'] = sheet.id
                result.append(sheet_data)
            
            print(f"✅ Retrieved {len(result)} sheets for user {user_id}")
            return result
            
        except Exception as e:
            print(f"❌ Error getting user sheets: {e}")
            return []
    
    async def get_user_sheet_by_id(self, user_id: int, sheet_doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific Google Sheet by document ID
        
        Args:
            user_id: Telegram user ID
            sheet_doc_id: Document ID of the sheet
            
        Returns:
            Dictionary containing sheet information or None if not found
        """
        if not self.db:
            print("❌ Firestore not available")
            return None
        
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            sheet_ref = user_ref.collection('google_sheets').document(sheet_doc_id)
            
            sheet_doc = sheet_ref.get()
            if sheet_doc.exists:
                sheet_data = sheet_doc.to_dict()
                sheet_data['doc_id'] = sheet_doc.id
                print(f"✅ Retrieved sheet '{sheet_data.get('friendly_name', 'Unknown')}' for user {user_id}")
                return sheet_data
            else:
                print(f"❌ Sheet {sheet_doc_id} not found for user {user_id}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting user sheet by ID: {e}")
            return None
    
    async def update_user_sheet_mapping(
        self, 
        user_id: int, 
        sheet_doc_id: str, 
        new_mapping: Dict[str, str], 
        new_start_row: int
    ) -> bool:
        """
        Update column mapping and start row for a user's sheet
        
        Args:
            user_id: Telegram user ID
            sheet_doc_id: Document ID of the sheet
            new_mapping: New column mapping dictionary
            new_start_row: New starting row for data
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db:
            print("❌ Firestore not available")
            return False
        
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            sheet_ref = user_ref.collection('google_sheets').document(sheet_doc_id)
            
            # Check if sheet exists
            sheet_doc = sheet_ref.get()
            if not sheet_doc.exists:
                print(f"❌ Sheet {sheet_doc_id} not found for user {user_id}")
                return False
            
            # Update the sheet
            sheet_ref.update({
                "column_mapping": new_mapping,
                "data_start_row": new_start_row
            })
            
            print(f"✅ Updated mapping for sheet {sheet_doc_id} (user {user_id})")
            return True
            
        except Exception as e:
            print(f"❌ Error updating sheet mapping: {e}")
            return False
    
    async def delete_user_sheet(self, user_id: int, sheet_doc_id: str) -> bool:
        """
        Delete a user's Google Sheet and reassign default if necessary
        
        Args:
            user_id: Telegram user ID
            sheet_doc_id: Document ID of the sheet to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db:
            print("❌ Firestore not available")
            return False
        
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            sheets_ref = user_ref.collection('google_sheets')
            sheet_ref = sheets_ref.document(sheet_doc_id)
            
            # Check if sheet exists and get its data
            sheet_doc = sheet_ref.get()
            if not sheet_doc.exists:
                print(f"❌ Sheet {sheet_doc_id} not found for user {user_id}")
                return False
            
            sheet_data = sheet_doc.to_dict()
            was_default = sheet_data.get('is_default', False)
            
            # Delete the sheet
            sheet_ref.delete()
            
            # If deleted sheet was default, assign another sheet as default
            if was_default:
                await self._reassign_default_sheet(user_id)
            
            print(f"✅ Deleted sheet {sheet_doc_id} for user {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting user sheet: {e}")
            return False
    
    async def set_default_sheet(self, user_id: int, sheet_doc_id: str) -> bool:
        """
        Set a specific sheet as default for the user
        
        Args:
            user_id: Telegram user ID
            sheet_doc_id: Document ID of the sheet to set as default
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db:
            print("❌ Firestore not available")
            return False
        
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            sheets_ref = user_ref.collection('google_sheets')
            
            # Use transaction to ensure atomicity
            @firestore.transactional
            def update_default_transaction(transaction):
                # First, set all sheets to not default
                all_sheets = sheets_ref.get()
                for sheet in all_sheets:
                    transaction.update(sheet.reference, {"is_default": False})
                
                # Then set the specified sheet as default
                target_sheet_ref = sheets_ref.document(sheet_doc_id)
                target_sheet = target_sheet_ref.get()
                
                if not target_sheet.exists:
                    raise ValueError(f"Sheet {sheet_doc_id} not found")
                
                transaction.update(target_sheet_ref, {"is_default": True})
            
            # Execute transaction
            transaction = self.db.transaction()
            update_default_transaction(transaction)
            
            print(f"✅ Set sheet {sheet_doc_id} as default for user {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error setting default sheet: {e}")
            return False
    
    async def _reassign_default_sheet(self, user_id: int) -> bool:
        """
        Reassign default sheet when the current default is deleted
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            sheets_ref = user_ref.collection('google_sheets')
            
            # Get all remaining sheets, ordered by creation date
            sheets = sheets_ref.order_by('created_at').get()
            
            if sheets:
                # Set the oldest sheet as default
                oldest_sheet = sheets[0]
                oldest_sheet.reference.update({"is_default": True})
                print(f"✅ Reassigned default sheet to {oldest_sheet.id} for user {user_id}")
                return True
            else:
                print(f"ℹ️ No sheets remaining for user {user_id} after deletion")
                return True
                
        except Exception as e:
            print(f"❌ Error reassigning default sheet: {e}")
            return False
    
    async def get_default_sheet(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the default Google Sheet for a user
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Dictionary containing default sheet information or None if not found
        """
        if not self.db:
            print("❌ Firestore not available")
            return None
        
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            sheets_ref = user_ref.collection('google_sheets')
            
            # Query for default sheet
            default_sheets = sheets_ref.where(filter=FieldFilter("is_default", "==", True)).get()
            
            if default_sheets:
                sheet = default_sheets[0]
                sheet_data = sheet.to_dict()
                sheet_data['doc_id'] = sheet.id
                print(f"✅ Retrieved default sheet for user {user_id}")
                return sheet_data
            else:
                print(f"ℹ️ No default sheet found for user {user_id}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting default sheet: {e}")
            return None


# Global instance for easy access
_google_sheets_manager = None

def get_google_sheets_manager(db_instance: Optional[firestore.Client] = None) -> GoogleSheetsManager:
    """
    Get or create global GoogleSheetsManager instance
    
    Args:
        db_instance: Firestore client instance
        
    Returns:
        GoogleSheetsManager instance
    """
    global _google_sheets_manager
    
    if _google_sheets_manager is None:
        _google_sheets_manager = GoogleSheetsManager(db_instance)
    
    return _google_sheets_manager
