from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class FileGeneratorInterface(ABC):
    """Interface for file generation operations."""
    
    @abstractmethod
    def generate_supply_file(self, data: Dict[str, Any], **kwargs) -> str:
        """
        Generate a supply file from the provided data.
        
        Args:
            data: Dictionary containing the data to generate the file from
            **kwargs: Additional keyword arguments for customization
            
        Returns:
            str: Path to the generated file or file content
        """
        pass
    
    @abstractmethod
    def generate_excel_file(self, data: Dict[str, Any], **kwargs) -> str:
        """
        Generate an Excel file from the provided data.
        
        Args:
            data: Dictionary containing the data to generate the file from
            **kwargs: Additional keyword arguments for customization
            
        Returns:
            str: Path to the generated file or file content
        """
        pass
    
    @abstractmethod
    def generate_google_sheets_file(self, data: Dict[str, Any], **kwargs) -> str:
        """
        Generate a Google Sheets file from the provided data.
        
        Args:
            data: Dictionary containing the data to generate the file from
            **kwargs: Additional keyword arguments for customization
            
        Returns:
            str: Path to the generated file or file content
        """
        pass
    
    @abstractmethod
    def format_matching_table(self, matching_data: List[Dict[str, Any]], **kwargs) -> str:
        """
        Format matching table data for display or file generation.
        
        Args:
            matching_data: List of dictionaries containing matching data
            **kwargs: Additional keyword arguments for customization
            
        Returns:
            str: Formatted table content
        """
        pass
