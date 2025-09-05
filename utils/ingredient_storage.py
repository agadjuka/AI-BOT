"""
Storage utilities for ingredient matching results
"""
import json
import os
import time
from typing import Optional, Dict, Any
from models.ingredient_matching import IngredientMatchingResult


class IngredientStorage:
    """Utility class for persistent storage of ingredient matching results"""
    
    def __init__(self, storage_dir: str = "data", max_age_hours: int = 1):
        self.storage_dir = storage_dir
        self.max_age_hours = max_age_hours
        self._ensure_storage_dir()
        # Clean up old files on initialization
        self._cleanup_old_files()
    
    def _ensure_storage_dir(self):
        """Ensure storage directory exists"""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
    
    def _get_storage_file(self, user_id: int, receipt_hash: str = None) -> str:
        """Get storage file path for user and receipt"""
        if receipt_hash:
            return os.path.join(self.storage_dir, f"ingredient_matching_{user_id}_{receipt_hash}.json")
        else:
            return os.path.join(self.storage_dir, f"ingredient_matching_{user_id}.json")
    
    def save_matching_result(self, user_id: int, matching_result: IngredientMatchingResult, 
                           changed_indices: set = None, receipt_hash: str = None) -> bool:
        """
        Save ingredient matching result for user and receipt
        
        Args:
            user_id: Telegram user ID
            matching_result: IngredientMatchingResult to save
            changed_indices: Set of manually changed indices
            receipt_hash: Hash of the receipt to bind matching to specific receipt
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            storage_data = {
                'matching_result': matching_result.to_dict(),
                'changed_indices': list(changed_indices) if changed_indices else []
            }
            
            file_path = self._get_storage_file(user_id, receipt_hash)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(storage_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Ошибка при сохранении сопоставлений для пользователя {user_id}: {e}")
            return False
    
    def load_matching_result(self, user_id: int, receipt_hash: str = None) -> Optional[tuple]:
        """
        Load ingredient matching result for user and receipt
        
        Args:
            user_id: Telegram user ID
            receipt_hash: Hash of the receipt to load matching for
            
        Returns:
            Tuple of (IngredientMatchingResult, changed_indices) or None if not found
        """
        try:
            file_path = self._get_storage_file(user_id, receipt_hash)
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                storage_data = json.load(f)
            
            matching_result = IngredientMatchingResult.from_dict(storage_data['matching_result'])
            changed_indices = set(storage_data.get('changed_indices', []))
            
            return matching_result, changed_indices
        except Exception as e:
            print(f"Ошибка при загрузке сопоставлений для пользователя {user_id}: {e}")
            return None
    
    def clear_matching_result(self, user_id: int, receipt_hash: str = None) -> bool:
        """
        Clear ingredient matching result for user and receipt
        
        Args:
            user_id: Telegram user ID
            receipt_hash: Hash of the receipt to clear matching for
            
        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            file_path = self._get_storage_file(user_id, receipt_hash)
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            print(f"Ошибка при очистке сопоставлений для пользователя {user_id}: {e}")
            return False
    
    def has_matching_result(self, user_id: int, receipt_hash: str = None) -> bool:
        """
        Check if user has saved matching result for receipt
        
        Args:
            user_id: Telegram user ID
            receipt_hash: Hash of the receipt to check
            
        Returns:
            True if has saved result, False otherwise
        """
        file_path = self._get_storage_file(user_id, receipt_hash)
        return os.path.exists(file_path)
    
    def _cleanup_old_files(self) -> None:
        """Clean up files older than max_age_hours"""
        try:
            current_time = time.time()
            max_age_seconds = self.max_age_hours * 3600  # Convert hours to seconds
            
            if not os.path.exists(self.storage_dir):
                return
            
            for filename in os.listdir(self.storage_dir):
                if filename.startswith('ingredient_matching_') and filename.endswith('.json'):
                    file_path = os.path.join(self.storage_dir, filename)
                    try:
                        file_age = current_time - os.path.getmtime(file_path)
                        if file_age > max_age_seconds:
                            os.remove(file_path)
                            print(f"Удален устаревший файл сопоставления: {filename}")
                    except (OSError, IOError) as e:
                        print(f"Ошибка при удалении файла {filename}: {e}")
        except Exception as e:
            print(f"Ошибка при очистке старых файлов: {e}")
    
    def cleanup_old_files(self) -> None:
        """Public method to clean up old files (can be called manually)"""
        self._cleanup_old_files()
