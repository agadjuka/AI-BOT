"""
Centralized ingredient loading utility for Google Sheets
"""
from typing import Dict, Any, Optional, Tuple
import logging

from google_sheets_handler import get_google_sheets_ingredients


class IngredientLoader:
    """Centralized ingredient loading utility for Google Sheets"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._google_sheets_ingredients: Optional[Dict[str, Dict[str, str]]] = None
    
    
    def load_google_sheets_ingredients(self, force_reload: bool = False) -> Dict[str, Dict[str, str]]:
        """
        DEPRECATED: Load ingredients from Google Sheets configuration
        This method is deprecated as ingredients are now loaded personally from Firestore.
        
        Args:
            force_reload: Force reload even if already cached
            
        Returns:
            Empty dictionary for backward compatibility
        """
        self.logger.warning("load_google_sheets_ingredients() is deprecated - use personal ingredients from Firestore")
        return {}
    
    def ensure_ingredients_available(self, ingredient_type: str, force_reload: bool = False) -> Tuple[bool, str]:
        """
        Ensure ingredients of specified type are available
        
        Args:
            ingredient_type: Type of ingredients ("google_sheets")
            force_reload: Force reload even if already cached
            
        Returns:
            Tuple of (success, message)
        """
        if ingredient_type == "google_sheets":
            ingredients = self.load_google_sheets_ingredients(force_reload)
            if ingredients:
                return True, f"Google Sheets ingredients loaded successfully ({len(ingredients)} items)"
            else:
                return False, "Failed to load Google Sheets ingredients"
        
        else:
            return False, f"Unknown ingredient type: {ingredient_type}"
    
    def get_ingredient_by_type(self, ingredient_type: str, force_reload: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get ingredients by type
        
        Args:
            ingredient_type: Type of ingredients ("google_sheets")
            force_reload: Force reload even if already cached
            
        Returns:
            Dictionary of ingredients or None if failed to load
        """
        if ingredient_type == "google_sheets":
            return self.load_google_sheets_ingredients(force_reload)
        
        else:
            self.logger.error(f"Unknown ingredient type: {ingredient_type}")
            return None
    
    
    def get_google_sheets_ingredients_for_matching(self, force_reload: bool = False) -> Dict[str, str]:
        """
        DEPRECATED: Get Google Sheets ingredients in format suitable for matching service
        This method is deprecated as ingredients are now loaded personally from Firestore.
        
        Args:
            force_reload: Force reload even if already cached
            
        Returns:
            Empty dictionary for backward compatibility
        """
        self.logger.warning("get_google_sheets_ingredients_for_matching() is deprecated - use personal ingredients from Firestore")
        return {}
    
    def clear_cache(self) -> None:
        """Clear all cached ingredients"""
        self._google_sheets_ingredients = None
        self.logger.info("Cleared ingredient cache")
    
    def get_cache_status(self) -> Dict[str, bool]:
        """
        Get status of cached ingredients
        
        Returns:
            Dictionary with cache status for each type
        """
        return {
            'google_sheets': self._google_sheets_ingredients is not None
        }
    
    def get_ingredient_count(self, ingredient_type: str) -> int:
        """
        Get count of ingredients by type
        
        Args:
            ingredient_type: Type of ingredients ("google_sheets")
            
        Returns:
            Number of ingredients or 0 if not loaded
        """
        if ingredient_type == "google_sheets":
            return len(self._google_sheets_ingredients) if self._google_sheets_ingredients else 0
        else:
            return 0
