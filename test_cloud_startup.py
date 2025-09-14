"""
Test script for cloud version startup
"""
import asyncio
import os
from main import app, initialize_bot, db


async def test_cloud_startup():
    """Test cloud version startup process"""
    print("🚀 Testing Cloud Version Startup...")
    
    # Test 1: Check if app is created
    print("\n📱 Test 1: FastAPI app creation")
    if app is None:
        print("❌ FastAPI app not created")
        return False
    print("✅ FastAPI app created successfully")
    
    # Test 2: Check Firestore connection
    print("\n🗄️ Test 2: Firestore connection")
    if db is None:
        print("❌ Firestore not connected")
        return False
    print("✅ Firestore connected successfully")
    
    # Test 3: Test bot initialization
    print("\n🤖 Test 3: Bot initialization")
    try:
        await initialize_bot()
        print("✅ Bot initialized successfully")
    except Exception as e:
        print(f"❌ Bot initialization failed: {e}")
        return False
    
    # Test 4: Check if application is created
    print("\n🔧 Test 4: Application creation")
    try:
        from main import application
        if application is None:
            print("❌ Telegram application not created")
            return False
        print("✅ Telegram application created successfully")
    except Exception as e:
        print(f"❌ Application creation error: {e}")
        return False
    
    # Test 5: Test health check endpoint
    print("\n🏥 Test 5: Health check endpoint")
    try:
        from main import health_check
        result = await health_check()
        if result.get("status") != "ok":
            print("❌ Health check failed")
            return False
        print("✅ Health check endpoint working")
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    print("\n✅ Cloud version startup test completed successfully!")
    return True


def test_environment_variables():
    """Test required environment variables"""
    print("\n🔧 Testing Environment Variables...")
    
    required_vars = ["BOT_TOKEN", "PROJECT_ID"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    
    print("✅ All required environment variables are set")
    return True


if __name__ == "__main__":
    print("🧪 Starting Cloud Version Startup Tests...")
    
    # Test environment variables
    env_success = test_environment_variables()
    
    # Test startup process
    startup_success = asyncio.run(test_cloud_startup())
    
    if env_success and startup_success:
        print("\n🎉 Cloud version is ready for deployment!")
    else:
        print("\n❌ Cloud version has issues that need to be fixed!")
