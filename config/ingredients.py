"""
Configuration for ingredients management
"""
from typing import Dict, Optional, List, Tuple


class IngredientConfig:
    """Configuration class for managing ingredients"""
    
    def __init__(self):
        """Initialize ingredient configuration with the ingredient list"""
        self.INGREDIENT_LIST: Dict[str, str] = {
            "potato wedges": "potato_wedges_001",
            "chicken": "chicken_002",
            "salmon": "salmon_003",
            "shrimps": "shrimps_004",
            "yogurt": "yogurt_005",
            "mozza cheese": "mozza_cheese_006",
            "feta cheese": "feta_cheese_007",
            "avocado": "avocado_008",
            "carrot": "carrot_009",
            "cucumber": "cucumber_010",
            "cabbage red": "cabbage_red_011",
            "cabbage white": "cabbage_white_012",
            "tomato": "tomato_013",
            "parsley": "parsley_014",
            "dill": "dill_015",
            "garlic": "garlic_016",
            "french fries": "french_fries_017",
            "salt": "salt_018",
            "sugar": "sugar_019",
            "dumplings": "dumplings_020",
            "flour": "flour_021",
            "sour cream": "sour_cream_022",
            "coconut cream": "coconut_cream_023",
            "tom yum sauce": "tom_yum_sauce_024",
            "tomato sauce": "tomato_sauce_025",
            "tea black": "tea_black_026",
            "bimoil frying": "bimoil_frying_027",
            "salad oil": "salad_oil_028",
            "lettuce": "lettuce_029",
            "mayonnaise": "mayonnaise_030",
            "lemon": "lemon_031",
            "pickles": "pickles_032"
        }
    
    def get_ingredient_list(self) -> Dict[str, str]:
        """
        Get the complete ingredient list
        
        Returns:
            Dict[str, str]: Dictionary mapping ingredient names to their IDs
        """
        return self.INGREDIENT_LIST.copy()
    
    def get_ingredient_by_name(self, name: str) -> Optional[str]:
        """
        Get ingredient ID by name
        
        Args:
            name (str): Ingredient name to search for
            
        Returns:
            Optional[str]: Ingredient ID if found, None otherwise
        """
        # Case-insensitive search
        name_lower = name.lower().strip()
        for ingredient_name, ingredient_id in self.INGREDIENT_LIST.items():
            if ingredient_name.lower() == name_lower:
                return ingredient_id
        return None
    
    def validate_ingredient_config(self) -> Tuple[bool, List[str]]:
        """
        Validate the ingredient configuration
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_errors)
        """
        errors = []
        
        # Check if ingredient list is empty
        if not self.INGREDIENT_LIST:
            errors.append("Ingredient list is empty")
            return False, errors
        
        # Check for duplicate ingredient names
        ingredient_names = list(self.INGREDIENT_LIST.keys())
        if len(ingredient_names) != len(set(ingredient_names)):
            errors.append("Duplicate ingredient names found")
        
        # Check for duplicate ingredient IDs
        ingredient_ids = list(self.INGREDIENT_LIST.values())
        if len(ingredient_ids) != len(set(ingredient_ids)):
            errors.append("Duplicate ingredient IDs found")
        
        # Check for empty ingredient names or IDs
        for name, ingredient_id in self.INGREDIENT_LIST.items():
            if not name or not name.strip():
                errors.append("Empty ingredient name found")
            if not ingredient_id or not ingredient_id.strip():
                errors.append(f"Empty ingredient ID for '{name}'")
        
        # Check ingredient ID format (should contain underscore and number)
        for name, ingredient_id in self.INGREDIENT_LIST.items():
            if not self._is_valid_ingredient_id_format(ingredient_id):
                errors.append(f"Invalid ingredient ID format for '{name}': '{ingredient_id}'")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _is_valid_ingredient_id_format(self, ingredient_id: str) -> bool:
        """
        Check if ingredient ID has valid format (contains underscore and number)
        
        Args:
            ingredient_id (str): Ingredient ID to validate
            
        Returns:
            bool: True if format is valid
        """
        if not ingredient_id:
            return False
        
        # Check if contains underscore and ends with number
        return '_' in ingredient_id and ingredient_id.split('_')[-1].isdigit()
    
    def add_ingredient(self, name: str, ingredient_id: str) -> bool:
        """
        Add new ingredient to the list
        
        Args:
            name (str): Ingredient name
            ingredient_id (str): Ingredient ID
            
        Returns:
            bool: True if added successfully, False if already exists
        """
        if name in self.INGREDIENT_LIST:
            return False
        
        self.INGREDIENT_LIST[name] = ingredient_id
        return True
    
    def remove_ingredient(self, name: str) -> bool:
        """
        Remove ingredient from the list
        
        Args:
            name (str): Ingredient name to remove
            
        Returns:
            bool: True if removed successfully, False if not found
        """
        if name not in self.INGREDIENT_LIST:
            return False
        
        del self.INGREDIENT_LIST[name]
        return True
    
    def get_ingredient_count(self) -> int:
        """
        Get total number of ingredients
        
        Returns:
            int: Number of ingredients
        """
        return len(self.INGREDIENT_LIST)
    
    def search_ingredients(self, query: str) -> List[Tuple[str, str]]:
        """
        Search ingredients by name (case-insensitive partial match)
        
        Args:
            query (str): Search query
            
        Returns:
            List[Tuple[str, str]]: List of (name, id) tuples matching the query
        """
        query_lower = query.lower().strip()
        results = []
        
        for name, ingredient_id in self.INGREDIENT_LIST.items():
            if query_lower in name.lower():
                results.append((name, ingredient_id))
        
        return results
