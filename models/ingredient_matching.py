"""
Data models for ingredient matching
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class MatchStatus(Enum):
    """Status of ingredient matching"""
    EXACT_MATCH = "exact"      # 100% совпадение
    PARTIAL_MATCH = "partial"  # Частичное совпадение (желтый эмодзи)
    NO_MATCH = "no_match"      # Нет совпадения (красный эмодзи)


@dataclass
class IngredientMatch:
    """Model for ingredient matching result"""
    receipt_item_name: str
    matched_ingredient_name: Optional[str] = None
    matched_ingredient_id: Optional[str] = None
    match_status: MatchStatus = MatchStatus.NO_MATCH
    similarity_score: float = 0.0
    suggested_matches: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.suggested_matches is None:
            self.suggested_matches = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'receipt_item_name': self.receipt_item_name,
            'matched_ingredient_name': self.matched_ingredient_name,
            'matched_ingredient_id': self.matched_ingredient_id,
            'match_status': self.match_status.value,
            'similarity_score': self.similarity_score,
            'suggested_matches': self.suggested_matches
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IngredientMatch':
        """Create from dictionary"""
        return cls(
            receipt_item_name=data.get('receipt_item_name', ''),
            matched_ingredient_name=data.get('matched_ingredient_name'),
            matched_ingredient_id=data.get('matched_ingredient_id'),
            match_status=MatchStatus(data.get('match_status', 'no_match')),
            similarity_score=data.get('similarity_score', 0.0),
            suggested_matches=data.get('suggested_matches', [])
        )


@dataclass
class IngredientMatchingResult:
    """Model for complete ingredient matching result"""
    matches: List[IngredientMatch] = None
    total_items: int = 0
    exact_matches: int = 0
    partial_matches: int = 0
    no_matches: int = 0
    
    def __post_init__(self):
        if self.matches is None:
            self.matches = []
    
    def add_match(self, match: IngredientMatch) -> None:
        """Add a match to the result"""
        self.matches.append(match)
        self.total_items += 1
        
        if match.match_status == MatchStatus.EXACT_MATCH:
            self.exact_matches += 1
        elif match.match_status == MatchStatus.PARTIAL_MATCH:
            self.partial_matches += 1
        else:
            self.no_matches += 1
    
    def get_emoji_for_status(self, status: MatchStatus) -> str:
        """Get emoji for match status"""
        if status == MatchStatus.EXACT_MATCH:
            return "🟢"  # Зеленый
        elif status == MatchStatus.PARTIAL_MATCH:
            return "🟡"  # Желтый
        else:
            return "🔴"  # Красный
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'matches': [match.to_dict() for match in self.matches],
            'total_items': self.total_items,
            'exact_matches': self.exact_matches,
            'partial_matches': self.partial_matches,
            'no_matches': self.no_matches
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IngredientMatchingResult':
        """Create from dictionary"""
        matches = [IngredientMatch.from_dict(match_data) for match_data in data.get('matches', [])]
        return cls(
            matches=matches,
            total_items=data.get('total_items', 0),
            exact_matches=data.get('exact_matches', 0),
            partial_matches=data.get('partial_matches', 0),
            no_matches=data.get('no_matches', 0)
        )

