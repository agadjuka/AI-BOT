from google.cloud import firestore
import os
from typing import Optional

class LanguageService:
    def __init__(self, db_instance=None):
        # Use the global Firestore instance from main.py if available
        self.db = db_instance
        if self.db:
            print("✅ Language service initialized with global Firestore instance")
        else:
            print("⚠️ Language service initialized without Firestore - languages won't be saved")

    def save_user_language(self, user_id: int, language: str) -> bool:
        """Save user language to Firestore"""
        if not self.db:
            return False
        try:
            doc_ref = self.db.collection('user_languages').document(str(user_id))
            doc_ref.set({'language': language})
            return True
        except Exception as e:
            print(f"Error saving language: {e}")
            return False

    def get_user_language(self, user_id: int) -> Optional[str]:
        """Get user language from Firestore"""
        if not self.db:
            return None
        try:
            doc_ref = self.db.collection('user_languages').document(str(user_id))
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict().get('language')
            return None
        except Exception as e:
            print(f"Error getting language: {e}")
            return None


# Global LanguageService instance
_language_service = None

def get_language_service(db_instance=None):
    """Get the global LanguageService instance"""
    global _language_service
    if _language_service is None:
        _language_service = LanguageService(db_instance)
    return _language_service