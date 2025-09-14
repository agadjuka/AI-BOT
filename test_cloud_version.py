"""
Test script for cloud version role system
"""
import asyncio
from main import app, db
from utils.role_initializer import initialize_roles_and_permissions, check_user_permissions
from services.user_service import get_user_service
from config.settings import BotConfig


async def test_cloud_role_system():
    """Test role system in cloud version context"""
    print("🧪 Testing Cloud Version Role System...")
    
    if not db:
        print("❌ Firestore not available in cloud version")
        return False
    
    print("✅ Firestore available in cloud version")
    
    # Test 1: Initialize roles and permissions
    print("\n🔧 Test 1: Initialize roles and permissions")
    try:
        success = await initialize_roles_and_permissions(db)
        if success:
            print("✅ Role initialization successful in cloud version")
        else:
            print("❌ Role initialization failed in cloud version")
            return False
    except Exception as e:
        print(f"❌ Role initialization error: {e}")
        return False
    
    # Test 2: Check admin role
    print("\n🔍 Test 2: Check admin role")
    try:
        user_service = get_user_service(db)
        config = BotConfig()
        admin_id = config.ADMIN_TELEGRAM_ID
        
        has_user_role = await user_service.get_user_role(admin_id)
        print(f"Admin {admin_id} has user role: {has_user_role}")
        
        is_admin = await user_service.is_user_admin(admin_id)
        print(f"Is admin: {is_admin}")
        
        if not is_admin:
            print("❌ Admin role not set correctly")
            return False
            
    except Exception as e:
        print(f"❌ Admin role check error: {e}")
        return False
    
    # Test 3: Test whitelist operations
    print("\n📋 Test 3: Test whitelist operations")
    try:
        # Add test user to whitelist
        test_username = "cloud_test_user"
        success = await user_service.add_to_whitelist(test_username)
        print(f"Added {test_username} to whitelist: {success}")
        
        if not success:
            print("❌ Failed to add user to whitelist")
            return False
        
        # Check if user is whitelisted
        is_whitelisted = await user_service.is_user_whitelisted(test_username)
        print(f"Is {test_username} whitelisted: {is_whitelisted}")
        
        if not is_whitelisted:
            print("❌ User not found in whitelist")
            return False
        
        # Clean up
        await user_service.remove_from_whitelist(test_username)
        print(f"✅ Cleaned up test user")
        
    except Exception as e:
        print(f"❌ Whitelist operations error: {e}")
        return False
    
    # Test 4: Test permission checking
    print("\n🔐 Test 4: Test permission checking")
    try:
        # Test admin permissions
        admin_permissions = await check_user_permissions(admin_id, "admin_user", db)
        print(f"Admin permissions: {admin_permissions}")
        
        if not admin_permissions['has_access']:
            print("❌ Admin should have access")
            return False
        
        # Test whitelisted user permissions
        whitelisted_permissions = await check_user_permissions(12345, test_username, db)
        print(f"Whitelisted user permissions: {whitelisted_permissions}")
        
        # Test non-whitelisted user permissions
        regular_permissions = await check_user_permissions(99999, "regular_user", db)
        print(f"Regular user permissions: {regular_permissions}")
        
        if regular_permissions['has_access']:
            print("❌ Regular user should not have access")
            return False
        
    except Exception as e:
        print(f"❌ Permission checking error: {e}")
        return False
    
    print("\n✅ Cloud version role system test completed successfully!")
    return True


def test_fastapi_endpoints():
    """Test FastAPI endpoints"""
    print("\n🌐 Testing FastAPI endpoints...")
    
    try:
        # Test health check endpoint
        from main import health_check
        print("✅ Health check endpoint available")
        
        # Test debug endpoint
        from main import debug_info
        print("✅ Debug endpoint available")
        
        # Test keepalive endpoint
        from main import keepalive_check
        print("✅ Keepalive endpoint available")
        
        print("✅ All FastAPI endpoints available")
        return True
        
    except Exception as e:
        print(f"❌ FastAPI endpoints error: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting Cloud Version Tests...")
    
    # Test FastAPI endpoints
    fastapi_success = test_fastapi_endpoints()
    
    # Test role system
    role_success = asyncio.run(test_cloud_role_system())
    
    if fastapi_success and role_success:
        print("\n🎉 All cloud version tests passed!")
    else:
        print("\n❌ Some cloud version tests failed!")
