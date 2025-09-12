"""
Ingredients Manager for user ingredient lists
Handles user-specific ingredient list management in Firestore
"""
import asyncio
from typing import Optional, List
from google.cloud import firestore


class IngredientsManager:
    """Manager for user ingredient lists stored in Firestore"""
    
    def __init__(self, db_instance: Optional[firestore.Client] = None):
        """
        Initialize IngredientsManager with Firestore client
        
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
                print("⚠️ IngredientsManager initialized without Firestore - operations will fail")
        
        if self.db:
            print("✅ IngredientsManager initialized with Firestore instance")
        else:
            print("❌ IngredientsManager initialized without Firestore - operations will fail")
    
    async def get_user_ingredients(self, user_id: int) -> List[str]:
        """
        Get user's ingredient list from Firestore
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            List of ingredient strings. Returns empty list if field doesn't exist or is empty.
        """
        if not self.db:
            print("❌ Firestore not available")
            return []
        
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                print(f"ℹ️ User {user_id} document not found, returning empty list")
                return []
            
            user_data = user_doc.to_dict()
            ingredient_list = user_data.get('ingredient_list', [])
            
            # Ensure we return a list of strings
            if isinstance(ingredient_list, list):
                # Filter out any non-string items and return
                result = [str(item) for item in ingredient_list if item]
                print(f"✅ Retrieved {len(result)} ingredients for user {user_id}")
                return result
            else:
                print(f"ℹ️ ingredient_list field is not a list for user {user_id}, returning empty list")
                return []
                
        except Exception as e:
            print(f"❌ Error getting user ingredients: {e}")
            return []
    
    async def update_user_ingredients(self, user_id: int, ingredients_list: List[str]) -> bool:
        """
        Update user's ingredient list in Firestore
        
        Args:
            user_id: Telegram user ID
            ingredients_list: List of ingredient strings to store
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db:
            print("❌ Firestore not available")
            return False
        
        try:
            # Validate input
            if not isinstance(ingredients_list, list):
                print("❌ ingredients_list must be a list")
                return False
            
            # Convert all items to strings and filter out empty ones
            clean_ingredients = [str(item).strip() for item in ingredients_list if str(item).strip()]
            
            user_ref = self.db.collection('users').document(str(user_id))
            
            # Update the ingredient_list field
            user_ref.update({
                'ingredient_list': clean_ingredients
            })
            
            print(f"✅ Updated ingredient list for user {user_id} with {len(clean_ingredients)} ingredients")
            return True
            
        except Exception as e:
            print(f"❌ Error updating user ingredients: {e}")
            return False
    
    async def delete_user_ingredients(self, user_id: int) -> bool:
        """
        Delete user's ingredient list from Firestore
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db:
            print("❌ Firestore not available")
            return False
        
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            
            # Check if user document exists
            user_doc = user_ref.get()
            if not user_doc.exists:
                print(f"ℹ️ User {user_id} document not found, nothing to delete")
                return True
            
            # Delete the ingredient_list field
            user_ref.update({
                'ingredient_list': firestore.DELETE_FIELD
            })
            
            print(f"✅ Deleted ingredient list for user {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting user ingredients: {e}")
            return False


# Global instance for easy access
_ingredients_manager = None

def get_ingredients_manager(db_instance: Optional[firestore.Client] = None) -> IngredientsManager:
    """
    Get or create global IngredientsManager instance
    
    Args:
        db_instance: Firestore client instance
        
    Returns:
        IngredientsManager instance
    """
    global _ingredients_manager
    
    if _ingredients_manager is None:
        _ingredients_manager = IngredientsManager(db_instance)
    
    return _ingredients_manager
