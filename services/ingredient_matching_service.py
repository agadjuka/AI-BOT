"""
Service for matching receipt ingredients with Poster ingredients
"""
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher
import re

from models.ingredient_matching import IngredientMatch, IngredientMatchingResult, MatchStatus
from models.receipt import ReceiptData, ReceiptItem


class IngredientMatchingService:
    """Service for matching ingredients from receipts with Poster ingredients"""
    
    def __init__(self):
        self.exact_match_threshold = 0.95  # 95% similarity for exact match
        self.partial_match_threshold = 0.6  # 60% similarity for partial match
        self.max_suggestions = 5  # Maximum number of suggestions
    
    def match_ingredients(self, receipt_data: ReceiptData, poster_ingredients: Dict[str, str]) -> IngredientMatchingResult:
        """
        Match ingredients from receipt with Poster ingredients
        
        Args:
            receipt_data: Receipt data containing items
            poster_ingredients: Dictionary of ingredient names to IDs from Poster
            
        Returns:
            IngredientMatchingResult with matching results
        """
        result = IngredientMatchingResult()
        
        for item in receipt_data.items:
            if not item.name or item.name.strip() == "" or item.name == "???":
                # Skip empty or unreadable items
                continue
                
            match = self._find_best_match(item.name, poster_ingredients)
            result.add_match(match)
        
        return result
    
    def _find_best_match(self, receipt_item_name: str, poster_ingredients: Dict[str, str]) -> IngredientMatch:
        """
        Find the best match for a receipt item name
        
        Args:
            receipt_item_name: Name of the item from receipt
            poster_ingredients: Dictionary of ingredient names to IDs from Poster
            
        Returns:
            IngredientMatch with the best match found
        """
        # Normalize the receipt item name
        normalized_receipt_name = self._normalize_name(receipt_item_name)
        
        best_match = None
        best_score = 0.0
        all_scores = []
        
        # Calculate similarity with all Poster ingredients
        for poster_name, poster_id in poster_ingredients.items():
            normalized_poster_name = self._normalize_name(poster_name)
            score = self._calculate_similarity(normalized_receipt_name, normalized_poster_name)
            
            all_scores.append({
                'name': poster_name,
                'id': poster_id,
                'score': score
            })
            
            if score > best_score:
                best_score = score
                best_match = {
                    'name': poster_name,
                    'id': poster_id,
                    'score': score
                }
        
        # Determine match status
        if best_score >= self.exact_match_threshold:
            status = MatchStatus.EXACT_MATCH
        elif best_score >= self.partial_match_threshold:
            status = MatchStatus.PARTIAL_MATCH
        else:
            status = MatchStatus.NO_MATCH
        
        # Get suggested matches (top matches for manual selection)
        suggested_matches = sorted(all_scores, key=lambda x: x['score'], reverse=True)[:self.max_suggestions]
        
        return IngredientMatch(
            receipt_item_name=receipt_item_name,
            matched_ingredient_name=best_match['name'] if best_match else None,
            matched_ingredient_id=best_match['id'] if best_match else None,
            match_status=status,
            similarity_score=best_score,
            suggested_matches=suggested_matches
        )
    
    def _normalize_name(self, name: str) -> str:
        """
        Normalize ingredient name for better matching
        
        Args:
            name: Original ingredient name
            
        Returns:
            Normalized name
        """
        if not name:
            return ""
        
        # Convert to lowercase
        normalized = name.lower().strip()
        
        # Remove common words that might interfere with matching
        common_words = ['fresh', 'organic', 'premium', 'quality', 'grade', 'a', 'an', 'the']
        words = normalized.split()
        words = [word for word in words if word not in common_words]
        
        # Remove special characters and extra spaces
        normalized = ' '.join(words)
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two ingredient names
        
        Args:
            name1: First ingredient name
            name2: Second ingredient name
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not name1 or not name2:
            return 0.0
        
        # Use SequenceMatcher for fuzzy string matching
        matcher = SequenceMatcher(None, name1, name2)
        base_similarity = matcher.ratio()
        
        # Boost score for exact word matches
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if words1 and words2:
            word_overlap = len(words1.intersection(words2)) / len(words1.union(words2))
            # Combine base similarity with word overlap
            final_score = (base_similarity * 0.7) + (word_overlap * 0.3)
        else:
            final_score = base_similarity
        
        return min(final_score, 1.0)
    
    def get_similar_ingredients(self, query: str, poster_ingredients: Dict[str, str], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get similar ingredients for manual selection
        
        Args:
            query: Search query
            poster_ingredients: Dictionary of ingredient names to IDs from Poster
            limit: Maximum number of results
            
        Returns:
            List of similar ingredients with scores
        """
        normalized_query = self._normalize_name(query)
        results = []
        
        for poster_name, poster_id in poster_ingredients.items():
            normalized_poster_name = self._normalize_name(poster_name)
            score = self._calculate_similarity(normalized_query, normalized_poster_name)
            
            if score > 0.1:  # Only include results with some similarity
                results.append({
                    'name': poster_name,
                    'id': poster_id,
                    'score': score
                })
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def manual_match_ingredient(self, receipt_item_name: str, poster_ingredient_id: str, 
                               poster_ingredients: Dict[str, str]) -> IngredientMatch:
        """
        Create a manual match for an ingredient
        
        Args:
            receipt_item_name: Name of the item from receipt
            poster_ingredient_id: ID of the selected Poster ingredient
            poster_ingredients: Dictionary of ingredient names to IDs from Poster
            
        Returns:
            IngredientMatch with manual match
        """
        # Find the ingredient name by ID
        poster_ingredient_name = None
        for name, ingredient_id in poster_ingredients.items():
            if ingredient_id == poster_ingredient_id:
                poster_ingredient_name = name
                break
        
        if not poster_ingredient_name:
            return IngredientMatch(
                receipt_item_name=receipt_item_name,
                match_status=MatchStatus.NO_MATCH,
                similarity_score=0.0
            )
        
        return IngredientMatch(
            receipt_item_name=receipt_item_name,
            matched_ingredient_name=poster_ingredient_name,
            matched_ingredient_id=poster_ingredient_id,
            match_status=MatchStatus.EXACT_MATCH,  # Manual matches are considered exact
            similarity_score=1.0
        )

