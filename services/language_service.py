from google.cloud import firestore
import os
from typing import Optional

class LanguageService:
    def __init__(self):
        self.db = None
        try:
            # Use the same database as main files (billscaner)
            self.db = firestore.Client(database='billscaner')
            print("✅ Language service initialized with Firestore (database: billscaner)")
        except Exception as e:
            print(f"⚠️ Firestore not available, using local storage: {e}")
            self.db = None

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

def get_language_service():
    """Get the global LanguageService instance"""
    global _language_service
    if _language_service is None:
        _language_service = LanguageService()
    return _language_service