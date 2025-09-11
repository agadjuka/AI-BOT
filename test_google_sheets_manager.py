"""
Simple test script for GoogleSheetsManager
Run this to verify the module works correctly
"""
import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.google_sheets_manager import get_google_sheets_manager


async def test_google_sheets_manager():
    """Test basic functionality of GoogleSheetsManager"""
    
    print("🧪 Testing GoogleSheetsManager...")
    
    # Initialize manager
    manager = get_google_sheets_manager()
    
    if not manager.db:
        print("❌ Firestore not available - skipping tests")
        print("💡 Make sure to set up Firestore credentials")
        return False
    
    print("✅ Firestore connection available")
    
    # Test user ID
    test_user_id = 999999999  # Use a test user ID
    
    try:
        # Test 1: Add a test sheet
        print("\n1. Testing add_user_sheet...")
        sheet_id = await manager.add_user_sheet(
            user_id=test_user_id,
            sheet_url="https://docs.google.com/spreadsheets/d/TEST_SHEET_ID/edit",
            sheet_id="TEST_SHEET_ID",
            friendly_name="Test Sheet"
        )
        
        if sheet_id:
            print(f"✅ Sheet added successfully: {sheet_id}")
        else:
            print("❌ Failed to add sheet")
            return False
        
        # Test 2: Get user sheets
        print("\n2. Testing get_user_sheets...")
        sheets = await manager.get_user_sheets(test_user_id)
        print(f"✅ Found {len(sheets)} sheets")
        
        # Test 3: Get specific sheet
        print("\n3. Testing get_user_sheet_by_id...")
        sheet = await manager.get_user_sheet_by_id(test_user_id, sheet_id)
        if sheet:
            print(f"✅ Retrieved sheet: {sheet['friendly_name']}")
            print(f"   Default mapping: {sheet['column_mapping']}")
        else:
            print("❌ Failed to retrieve sheet")
            return False
        
        # Test 4: Update mapping
        print("\n4. Testing update_user_sheet_mapping...")
        new_mapping = {
            "check_date": "A",
            "product_name": "B",
            "quantity": "C",
            "price_per_item": "D",
            "total_price": "E",
            "store_name": "F"
        }
        
        success = await manager.update_user_sheet_mapping(
            user_id=test_user_id,
            sheet_doc_id=sheet_id,
            new_mapping=new_mapping,
            new_start_row=3
        )
        
        if success:
            print("✅ Mapping updated successfully")
        else:
            print("❌ Failed to update mapping")
            return False
        
        # Test 5: Get default sheet
        print("\n5. Testing get_default_sheet...")
        default_sheet = await manager.get_default_sheet(test_user_id)
        if default_sheet:
            print(f"✅ Default sheet: {default_sheet['friendly_name']}")
        else:
            print("❌ No default sheet found")
        
        # Test 6: Clean up - delete test sheet
        print("\n6. Cleaning up test data...")
        success = await manager.delete_user_sheet(test_user_id, sheet_id)
        if success:
            print("✅ Test sheet deleted successfully")
        else:
            print("❌ Failed to delete test sheet")
        
        print("\n🎉 All tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False


async def main():
    """Main test function"""
    print("=" * 50)
    print("GoogleSheetsManager Test Suite")
    print("=" * 50)
    
    success = await test_google_sheets_manager()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests completed successfully!")
    else:
        print("❌ Some tests failed!")
    print("=" * 50)
    
    return success


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
