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
    
    async def get_user_role(self, user_id: int) -> Optional[str]:
        """
        Get user role from Firestore
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            User role ("admin" or "user") or None if not found
        """
        if not self.db:
            print("❌ Firestore not available")
            return None
        
        try:
            user_ref = self.db.collection('users').document(str(user_id))
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                return user_data.get('role', 'user')  # Default to 'user' if role not set
            else:
                return None
                
        except Exception as e:
            print(f"❌ Error getting user role: {e}")
            return None
    
    async def set_user_role(self, user_id: int, role: str) -> bool:
        """
        Set user role in Firestore
        
        Args:
            user_id: Telegram user ID
            role: Role to assign ("admin" or "user")
            
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
            
            # Check if user document exists
            user_doc = user_ref.get()
            if user_doc.exists:
                # Update existing user document
                user_ref.update({'role': role})
                print(f"✅ Updated user {user_id} role to {role}")
            else:
                # Create new user document with role
                user_ref.set({'role': role})
                print(f"✅ Created user {user_id} with role {role}")
            
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
            current_role = await self.get_user_role(admin_user_id)
            
            if current_role == 'admin':
                print(f"✅ User {admin_user_id} already has admin role")
                return True
            else:
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
        role = await self.get_user_role(user_id)
        return role == 'admin'
    
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
