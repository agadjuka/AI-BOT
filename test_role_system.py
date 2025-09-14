"""
Test script for the role system
Tests user roles, whitelist functionality, and admin operations
"""
import asyncio
import os
from google.cloud import firestore
from services.user_service import get_user_service
from utils.role_initializer import initialize_roles_and_permissions, check_user_permissions
from config.settings import BotConfig


async def test_role_system():
    """Test the complete role system"""
    print("🧪 Testing Role System...")
    
    # Initialize Firestore
    try:
        db = firestore.Client(database='billscaner')
        print("✅ Firestore connected")
    except Exception as e:
        print(f"❌ Firestore connection failed: {e}")
        return
    
    # Test 1: Initialize roles and permissions
    print("\n🔧 Test 1: Initialize roles and permissions")
    success = await initialize_roles_and_permissions(db)
    if success:
        print("✅ Role initialization successful")
    else:
        print("❌ Role initialization failed")
        return
    
    # Test 2: Get user service
    print("\n👤 Test 2: Get user service")
    user_service = get_user_service(db)
    print("✅ User service created")
    
    # Test 3: Check admin role
    print("\n🔍 Test 3: Check admin role")
    config = BotConfig()
    admin_id = config.ADMIN_TELEGRAM_ID
    
    role = await user_service.get_user_role(admin_id)
    print(f"Admin {admin_id} role: {role}")
    
    is_admin = await user_service.is_user_admin(admin_id)
    print(f"Is admin: {is_admin}")
    
    # Test 4: Test whitelist operations
    print("\n📋 Test 4: Test whitelist operations")
    
    # Add test user to whitelist
    test_username = "test_user"
    success = await user_service.add_to_whitelist(test_username)
    print(f"Added {test_username} to whitelist: {success}")
    
    # Check if user is whitelisted
    is_whitelisted = await user_service.is_user_whitelisted(test_username)
    print(f"Is {test_username} whitelisted: {is_whitelisted}")
    
    # Get whitelist
    whitelist = await user_service.get_whitelist()
    print(f"Whitelist: {whitelist}")
    
    # Test 5: Test permission checking
    print("\n🔐 Test 5: Test permission checking")
    
    # Test admin permissions
    admin_permissions = await check_user_permissions(admin_id, "admin_user", db)
    print(f"Admin permissions: {admin_permissions}")
    
    # Test whitelisted user permissions
    whitelisted_permissions = await check_user_permissions(12345, test_username, db)
    print(f"Whitelisted user permissions: {whitelisted_permissions}")
    
    # Test non-whitelisted user permissions
    regular_permissions = await check_user_permissions(99999, "regular_user", db)
    print(f"Regular user permissions: {regular_permissions}")
    
    # Test 6: Test user info
    print("\n📊 Test 6: Test user info")
    user_info = await user_service.get_user_info(admin_id)
    print(f"Admin user info: {user_info}")
    
    # Test 7: Clean up whitelist
    print("\n🧹 Test 7: Clean up whitelist")
    success = await user_service.remove_from_whitelist(test_username)
    print(f"Removed {test_username} from whitelist: {success}")
    
    # Verify removal
    is_whitelisted = await user_service.is_user_whitelisted(test_username)
    print(f"Is {test_username} still whitelisted: {is_whitelisted}")
    
    print("\n✅ Role system test completed!")


async def test_firestore_collections():
    """Test Firestore collections structure"""
    print("\n🗄️ Testing Firestore Collections...")
    
    try:
        db = firestore.Client(database='billscaner')
        
        # Test users collection
        print("📁 Testing users collection...")
        users_ref = db.collection('users')
        users = list(users_ref.limit(5).stream())
        print(f"Found {len(users)} users in collection")
        
        for user in users:
            print(f"  - User {user.id}: {user.to_dict()}")
        
        # Test whitelist collection
        print("\n📁 Testing whitelist collection...")
        whitelist_ref = db.collection('whitelist')
        whitelist = list(whitelist_ref.limit(5).stream())
        print(f"Found {len(whitelist)} users in whitelist")
        
        for user in whitelist:
            print(f"  - Whitelisted: {user.id}")
        
        print("✅ Firestore collections test completed!")
        
    except Exception as e:
        print(f"❌ Firestore collections test failed: {e}")


if __name__ == "__main__":
    print("🚀 Starting Role System Tests...")
    
    # Run tests
    asyncio.run(test_role_system())
    asyncio.run(test_firestore_collections())
    
    print("\n🎉 All tests completed!")
