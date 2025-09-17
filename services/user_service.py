"""
User Service for managing user roles and permissions in Firestore
Handles user role assignment, whitelist management, and admin operations
"""
import asyncio
from typing import Optional, Dict, Any, List
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter


class UserService:
    """Service for managing user roles and permissions"""
    
    def __init__(self, db_instance: Optional[firestore.Client] = None):
        """
        Initialize UserService with Firestore client
        
        Args:
            db_instance: Firestore client instance. If None, will try to get global instance
        """
        self.db = db_instance
        if not self.db:
            # Try to get global Firestore instance from main.py
            try:
                import main
                self.db = main.db
            except (ImportError, AttributeError):
                print("⚠️ UserService initialized without Firestore - operations will fail")
        
        if self.db:
            print("✅ UserService initialized with Firestore instance")
        else:
            print("❌ UserService initialized without Firestore - operations will fail")
    
    async def get_user_role(self, user_id: int) -> bool:
        """
        Check if user has "user" role in Firestore
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if document exists AND role field exists AND role equals "user"
            False in all other cases
        """
        if not self.db:
            return False
        
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                return False
            
            user_data = user_doc.to_dict()
            
            # Check if 'role' key exists in the document
            if 'role' not in user_data:
                return False
            
            # Check if role equals "user"
            return user_data['role'] == "user"
                
        except Exception as e:
            print(f"❌ Error checking user role: {e}")
            return False
    
    async def set_user_role(self, user_id: int, role: str, username: str = None) -> bool:
        """
        Set user role in Firestore
        
        Args:
            user_id: Telegram user ID
            role: Role to assign ("admin" or "user")
            username: Username to store (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db:
            print("❌ Firestore not available")
            return False
        
        if role not in ['admin', 'user']:
            print(f"❌ Invalid role: {role}. Must be 'admin' or 'user'")
            return False
        
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            
            # Prepare user data
            user_data = {'role': role}
            if username:
                user_data['username'] = username
            
            # Check if user document exists
            user_doc = user_ref.get()
            if user_doc.exists:
                # Update existing user document
                user_ref.update(user_data)
                print(f"✅ Updated user {user_id} role to {role}" + (f" with username {username}" if username else ""))
            else:
                # Create new user document with role and username
                user_ref.set(user_data)
                print(f"✅ Created user {user_id} with role {role}" + (f" and username {username}" if username else ""))
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting user role: {e}")
            return False
    
    async def ensure_admin_role(self, admin_user_id: int) -> bool:
        """
        Ensure admin user has admin role, assign if not
        
        Args:
            admin_user_id: Telegram ID of admin user
            
        Returns:
            True if admin role is set, False otherwise
        """
        if not self.db:
            print("❌ Firestore not available")
            return False
        
        try:
            # Check if user has admin role by looking at the document directly
            user_ref = self.db.collection('users').document(str(admin_user_id))
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                if user_data.get('role') == 'admin':
                    print(f"✅ User {admin_user_id} already has admin role")
                    return True
            
            # Set admin role
            success = await self.set_user_role(admin_user_id, 'admin')
            if success:
                print(f"✅ Assigned admin role to user {admin_user_id}")
            else:
                print(f"❌ Failed to assign admin role to user {admin_user_id}")
            return success
                
        except Exception as e:
            print(f"❌ Error ensuring admin role: {e}")
            return False
    
    async def is_user_admin(self, user_id: int) -> bool:
        """
        Check if user has admin role
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if user is admin, False otherwise
        """
        if not self.db:
            print("❌ Firestore not available")
            return False
        
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                print(f"❌ User {user_id} document does not exist")
                return False
            
            user_data = user_doc.to_dict()
            
            # Check if 'role' key exists and equals 'admin'
            if 'role' in user_data and user_data['role'] == 'admin':
                print(f"✅ User {user_id} has admin role")
                return True
            else:
                print(f"❌ User {user_id} does not have admin role")
                return False
                
        except Exception as e:
            print(f"❌ Error checking admin role: {e}")
            return False
    
    async def is_user_whitelisted(self, username: str) -> bool:
        """
        Check if username is in whitelist
        
        Args:
            username: Telegram username (without @)
            
        Returns:
            True if user is whitelisted, False otherwise
        """
        if not self.db:
            print("❌ Firestore not available")
            return False
        
        if not username:
            return False
        
        try:
            # Convert username to lowercase and remove @ if present
            clean_username = username.lower().lstrip('@')
            
            whitelist_ref = self.db.collection('whitelist').document(clean_username)
            whitelist_doc = whitelist_ref.get()
            
            return whitelist_doc.exists
            
        except Exception as e:
            print(f"❌ Error checking whitelist: {e}")
            return False
    
    async def add_to_whitelist(self, username: str) -> bool:
        """
        Add username to whitelist
        
        Args:
            username: Telegram username (without @)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db:
            print("❌ Firestore not available")
            return False
        
        if not username:
            print("❌ Username cannot be empty")
            return False
        
        try:
            # Convert username to lowercase and remove @ if present
            clean_username = username.lower().lstrip('@')
            
            whitelist_ref = self.db.collection('whitelist').document(clean_username)
            whitelist_ref.set({})  # Empty document is sufficient
            
            print(f"✅ Added {clean_username} to whitelist")
            return True
            
        except Exception as e:
            print(f"❌ Error adding to whitelist: {e}")
            return False
    
    async def remove_from_whitelist(self, username: str) -> bool:
        """
        Remove username from whitelist
        
        Args:
            username: Telegram username (without @)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db:
            print("❌ Firestore not available")
            return False
        
        if not username:
            print("❌ Username cannot be empty")
            return False
        
        try:
            # Convert username to lowercase and remove @ if present
            clean_username = username.lower().lstrip('@')
            
            whitelist_ref = self.db.collection('whitelist').document(clean_username)
            whitelist_ref.delete()
            
            print(f"✅ Removed {clean_username} from whitelist")
            return True
            
        except Exception as e:
            print(f"❌ Error removing from whitelist: {e}")
            return False
    
    async def get_whitelist(self) -> List[str]:
        """
        Get all whitelisted usernames
        
        Returns:
            List of whitelisted usernames
        """
        if not self.db:
            print("❌ Firestore not available")
            return []
        
        try:
            whitelist_ref = self.db.collection('whitelist')
            docs = whitelist_ref.stream()
            
            usernames = [doc.id for doc in docs]
            print(f"✅ Retrieved {len(usernames)} whitelisted users")
            return usernames
            
        except Exception as e:
            print(f"❌ Error getting whitelist: {e}")
            return []
    
    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get complete user information including role
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            User data dictionary or None if not found
        """
        if not self.db:
            print("❌ Firestore not available")
            return None
        
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                user_data['user_id'] = user_id
                return user_data
            else:
                return None
                
        except Exception as e:
            print(f"❌ Error getting user info: {e}")
            return None
    
    async def set_user_display_mode(self, user_id: int, mode: str) -> bool:
        """
        Set user display mode in Firestore
        
        Args:
            user_id: Telegram user ID
            mode: Display mode ("desktop" or "mobile")
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db:
            print("❌ Firestore not available")
            return False
        
        if mode not in ['desktop', 'mobile']:
            print(f"❌ Invalid display mode: {mode}. Must be 'desktop' or 'mobile'")
            return False
        
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            
            # Check if user document exists
            user_doc = user_ref.get()
            if user_doc.exists:
                # Update existing user document
                user_ref.update({
                    'display_mode': mode
                })
                print(f"✅ Updated user {user_id} display mode to {mode}")
            else:
                # Create new user document with display mode
                user_ref.set({
                    'display_mode': mode
                })
                print(f"✅ Created user {user_id} with display mode {mode}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting user display mode: {e}")
            return False
    
    async def get_user_display_mode(self, user_id: int) -> str:
        """
        Get user display mode from Firestore
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Display mode ("desktop" or "mobile"). Returns "mobile" as default if not set.
        """
        if not self.db:
            print("❌ Firestore not available")
            # Проверяем переменную окружения для локальной разработки
            import os
            env_display_mode = os.getenv('DISPLAY_MODE', '').lower()
            if env_display_mode in ['desktop', 'mobile']:
                print(f"✅ Using display mode from environment: {env_display_mode}")
                return env_display_mode
            return "mobile"
        
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                display_mode = user_data.get('display_mode')
                
                if display_mode in ['desktop', 'mobile']:
                    print(f"✅ Retrieved user {user_id} display mode: {display_mode}")
                    return display_mode
                else:
                    print(f"⚠️ User {user_id} has invalid display mode '{display_mode}', using default 'mobile'")
                    return "mobile"
            else:
                print(f"⚠️ User {user_id} document does not exist, using default display mode 'mobile'")
                return "mobile"
                
        except Exception as e:
            print(f"❌ Error getting user display mode: {e}")
            return "mobile"


# Global instance management
_global_user_service: Optional[UserService] = None

def get_user_service(db_instance: Optional[firestore.Client] = None) -> UserService:
    """
    Get global UserService instance
    
    Args:
        db_instance: Firestore client instance. If None, will try to get global instance
        
    Returns:
        UserService instance
    """
    global _global_user_service
    
    if _global_user_service is None:
        _global_user_service = UserService(db_instance)
    
    return _global_user_service
