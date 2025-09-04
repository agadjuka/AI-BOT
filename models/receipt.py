"""
Data models for receipt processing
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class ReceiptItem:
    """Model for a single receipt item"""
    line_number: int
    name: str
    quantity: float
    price: float
    total: float
    status: str = "needs_review"
    auto_calculated: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'line_number': self.line_number,
            'name': self.name,
            'quantity': self.quantity,
            'price': self.price,
            'total': self.total,
            'status': self.status,
            'auto_calculated': self.auto_calculated
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReceiptItem':
        """Create from dictionary"""
        return cls(
            line_number=data.get('line_number', 0),
            name=data.get('name', ''),
            quantity=data.get('quantity', 0.0),
            price=data.get('price', 0.0),
            total=data.get('total', 0.0),
            status=data.get('status', 'needs_review'),
            auto_calculated=data.get('auto_calculated', False)
        )


@dataclass
class ReceiptData:
    """Model for complete receipt data"""
    items: List[ReceiptItem] = field(default_factory=list)
    grand_total_text: str = "0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'items': [item.to_dict() for item in self.items],
            'grand_total_text': self.grand_total_text
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReceiptData':
        """Create from dictionary"""
        items = [ReceiptItem.from_dict(item_data) for item_data in data.get('items', [])]
        return cls(
            items=items,
            grand_total_text=data.get('grand_total_text', '0')
        )
    
    def add_item(self, item: ReceiptItem) -> None:
        """Add item to receipt"""
        self.items.append(item)
    
    def remove_item(self, line_number: int) -> bool:
        """Remove item by line number"""
        original_count = len(self.items)
        self.items = [item for item in self.items if item.line_number != line_number]
        
        if len(self.items) < original_count:
            # Renumber remaining items
            for i, item in enumerate(self.items, 1):
                item.line_number = i
            return True
        return False
    
    def get_item(self, line_number: int) -> Optional[ReceiptItem]:
        """Get item by line number"""
        for item in self.items:
            if item.line_number == line_number:
                return item
        return None
    
    def update_item(self, line_number: int, **kwargs) -> bool:
        """Update item by line number"""
        item = self.get_item(line_number)
        if item:
            for key, value in kwargs.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            return True
        return False
    
    def calculate_total_sum(self) -> float:
        """Calculate total sum of all items"""
        return sum(item.total for item in self.items if item.total > 0)
    
    def get_max_line_number(self) -> int:
        """Get maximum line number"""
        if not self.items:
            return 0
        return max(item.line_number for item in self.items)
