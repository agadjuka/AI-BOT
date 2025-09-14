"""
Role Initializer for setting up admin roles and whitelist on bot startup
"""
import asyncio
from typing import Optional, Dict
from google.cloud import firestore
from services.user_service import get_user_service
from config.settings import BotConfig


async def initialize_roles_and_permissions(db_instance: Optional[firestore.Client] = None) -> bool:
    """
    Initialize admin roles and whitelist on bot startup
    
    Args:
        db_instance: Firestore client instance
        
    Returns:
        True if initialization successful, False otherwise
    """
    if not db_instance:
        print("❌ Firestore instance not provided for role initialization")
        return False
    
    try:
        print("🔧 Initializing roles and permissions...")
        
        # Get user service
        user_service = get_user_service(db_instance)
        
        # Get admin user ID from config
        config = BotConfig()
        admin_user_id = config.ADMIN_TELEGRAM_ID
        
        print(f"🔍 Checking admin role for user {admin_user_id}...")
        
        # Ensure admin user has admin role
        admin_success = await user_service.ensure_admin_role(admin_user_id)
        
        if admin_success:
            print(f"✅ Admin role initialized for user {admin_user_id}")
        else:
            print(f"❌ Failed to initialize admin role for user {admin_user_id}")
            return False
        
        # Create whitelist collection (this will be created automatically when first document is added)
        print("🔍 Whitelist collection will be created automatically when first user is added")
        
        print("✅ Roles and permissions initialization completed")
        return True
        
    except Exception as e:
        print(f"❌ Error during role initialization: {e}")
        import traceback
        traceback.print_exc()
        return False


async def check_user_permissions(user_id: int, username: str = None, db_instance: Optional[firestore.Client] = None) -> Dict[str, bool]:
    """
    Check user permissions (admin role and whitelist status)
    
    Args:
        user_id: Telegram user ID
        username: Telegram username (optional)
        db_instance: Firestore client instance
        
    Returns:
        Dictionary with permission status
    """
    if not db_instance:
        return {
            'is_admin': False,
            'is_whitelisted': False,
            'has_access': False
        }
    
    try:
        user_service = get_user_service(db_instance)
        
        # Check admin role
        is_admin = await user_service.is_user_admin(user_id)
        
        # Check whitelist status (if username provided)
        is_whitelisted = False
        if username:
            is_whitelisted = await user_service.is_user_whitelisted(username)
        
        # User has access if they are admin OR whitelisted
        has_access = is_admin or is_whitelisted
        
        return {
            'is_admin': is_admin,
            'is_whitelisted': is_whitelisted,
            'has_access': has_access
        }
        
    except Exception as e:
        print(f"❌ Error checking user permissions: {e}")
        return {
            'is_admin': False,
            'is_whitelisted': False,
            'has_access': False
        }
