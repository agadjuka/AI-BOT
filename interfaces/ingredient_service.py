from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class IngredientServiceInterface(ABC):
    """
    Abstract interface for ingredient service operations.
    Defines the contract that all ingredient service implementations must follow.
    """
    
    @abstractmethod
    def load_ingredients(self) -> List[Dict[str, Any]]:
        """
        Load ingredients from the data source.
        
        Returns:
            List[Dict[str, Any]]: List of ingredient dictionaries
        """
        pass
    
    @abstractmethod
    def find_matches(self, query: str, ingredients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find matching ingredients based on a query string.
        
        Args:
            query (str): Search query string
            ingredients (List[Dict[str, Any]]): List of ingredients to search through
            
        Returns:
            List[Dict[str, Any]]: List of matching ingredient dictionaries
        """
        pass
    
    @abstractmethod
    def save_matching_result(self, result: Dict[str, Any]) -> bool:
        """
        Save a matching result to the data source.
        
        Args:
            result (Dict[str, Any]): Matching result to save
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_ingredient_by_id(self, ingredient_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific ingredient by its ID.
        
        Args:
            ingredient_id (str): The ID of the ingredient to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: The ingredient dictionary if found, None otherwise
        """
        pass
