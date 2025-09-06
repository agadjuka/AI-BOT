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
        self.min_match_threshold = 0.4  # 40% minimum similarity to consider any match
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
        
        # Only set matched ingredient if similarity is above minimum threshold
        if best_score >= self.min_match_threshold:
            matched_name = best_match['name'] if best_match else None
            matched_id = best_match['id'] if best_match else None
        else:
            matched_name = None
            matched_id = None
        
        return IngredientMatch(
            receipt_item_name=receipt_item_name,
            matched_ingredient_name=matched_name,
            matched_ingredient_id=matched_id,
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
        
        # Remove common words that might interfere with matching (but keep important food words)
        common_words = ['fresh', 'organic', 'premium', 'quality', 'grade', 'a', 'an', 'the', 'kg', 'g', 'ml', 'l']
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
        
        # Get words from both names
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if words1 and words2:
            # Calculate exact word overlap
            exact_word_overlap = len(words1.intersection(words2)) / len(words1.union(words2))
            
            # Calculate partial word matches (substring matches)
            partial_matches = 0
            total_words = len(words1.union(words2))
            
            for word1 in words1:
                for word2 in words2:
                    # Check if one word contains the other (partial match)
                    if word1 in word2 or word2 in word1:
                        partial_matches += 1
                        break
            
            partial_word_overlap = partial_matches / total_words if total_words > 0 else 0
            
            # Use the better of exact or partial word overlap
            word_overlap = max(exact_word_overlap, partial_word_overlap)
            
            # If there's any word overlap, boost the score significantly
            if word_overlap > 0:
                # If there's exact word match, it should be at least partial match
                if exact_word_overlap > 0:
                    final_score = max(0.6, (base_similarity * 0.4) + (word_overlap * 0.6))
                else:
                    # Partial word match should also be considered
                    final_score = max(0.4, (base_similarity * 0.5) + (word_overlap * 0.5))
            else:
                # No word overlap, use base similarity
                final_score = base_similarity
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
        print(f"DEBUG: get_similar_ingredients called with query '{query}' and {len(poster_ingredients)} ingredients")
        normalized_query = self._normalize_name(query)
        print(f"DEBUG: Normalized query: '{normalized_query}'")
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
        final_results = results[:limit]
        print(f"DEBUG: Found {len(final_results)} results (from {len(results)} total matches)")
        if final_results:
            print(f"DEBUG: Top result: {final_results[0]['name']} (score: {final_results[0]['score']:.3f})")
        return final_results
    
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

