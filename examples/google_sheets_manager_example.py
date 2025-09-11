"""
Example usage of GoogleSheetsManager
Demonstrates how to use the Google Sheets management module
"""
import asyncio
from services.google_sheets_manager import get_google_sheets_manager


async def example_usage():
    """Example of how to use GoogleSheetsManager"""
    
    # Initialize the manager (will use global Firestore instance from main.py)
    manager = get_google_sheets_manager()
    
    user_id = 123456789  # Example Telegram user ID
    
    print("=== Google Sheets Manager Example ===\n")
    
    # 1. Add a new sheet for the user
    print("1. Adding a new Google Sheet...")
    sheet_doc_id = await manager.add_user_sheet(
        user_id=user_id,
        sheet_url="https://docs.google.com/spreadsheets/d/1ABC123DEF456/edit",
        sheet_id="1ABC123DEF456",
        friendly_name="My Receipts"
    )
    
    if sheet_doc_id:
        print(f"✅ Sheet added with ID: {sheet_doc_id}")
    else:
        print("❌ Failed to add sheet")
        return
    
    # 2. Get all user sheets
    print("\n2. Getting all user sheets...")
    sheets = await manager.get_user_sheets(user_id)
    print(f"Found {len(sheets)} sheets:")
    for sheet in sheets:
        print(f"  - {sheet['friendly_name']} (ID: {sheet['doc_id']}, Default: {sheet['is_default']})")
    
    # 3. Get specific sheet by ID
    print(f"\n3. Getting specific sheet by ID: {sheet_doc_id}")
    sheet = await manager.get_user_sheet_by_id(user_id, sheet_doc_id)
    if sheet:
        print(f"Sheet details: {sheet['friendly_name']}")
        print(f"Column mapping: {sheet['column_mapping']}")
        print(f"Data start row: {sheet['data_start_row']}")
    
    # 4. Update column mapping
    print("\n4. Updating column mapping...")
    new_mapping = {
        "check_date": "A",
        "product_name": "B",
        "quantity": "C", 
        "price_per_item": "D",
        "total_price": "E",
        "store_name": "F"  # Adding a new column
    }
    
    success = await manager.update_user_sheet_mapping(
        user_id=user_id,
        sheet_doc_id=sheet_doc_id,
        new_mapping=new_mapping,
        new_start_row=3
    )
    
    if success:
        print("✅ Column mapping updated successfully")
    else:
        print("❌ Failed to update column mapping")
    
    # 5. Add another sheet to test default assignment
    print("\n5. Adding another sheet...")
    sheet2_doc_id = await manager.add_user_sheet(
        user_id=user_id,
        sheet_url="https://docs.google.com/spreadsheets/d/2XYZ789ABC123/edit",
        sheet_id="2XYZ789ABC123",
        friendly_name="Backup Receipts"
    )
    
    if sheet2_doc_id:
        print(f"✅ Second sheet added with ID: {sheet2_doc_id}")
    
    # 6. Set the second sheet as default
    print("\n6. Setting second sheet as default...")
    success = await manager.set_default_sheet(user_id, sheet2_doc_id)
    if success:
        print("✅ Default sheet updated")
    
    # 7. Get default sheet
    print("\n7. Getting default sheet...")
    default_sheet = await manager.get_default_sheet(user_id)
    if default_sheet:
        print(f"Default sheet: {default_sheet['friendly_name']} (ID: {default_sheet['doc_id']})")
    
    # 8. List all sheets again to see changes
    print("\n8. Final list of sheets:")
    sheets = await manager.get_user_sheets(user_id)
    for sheet in sheets:
        print(f"  - {sheet['friendly_name']} (ID: {sheet['doc_id']}, Default: {sheet['is_default']})")
    
    # 9. Delete the first sheet
    print(f"\n9. Deleting first sheet: {sheet_doc_id}")
    success = await manager.delete_user_sheet(user_id, sheet_doc_id)
    if success:
        print("✅ Sheet deleted successfully")
    
    # 10. Check remaining sheets
    print("\n10. Remaining sheets after deletion:")
    sheets = await manager.get_user_sheets(user_id)
    for sheet in sheets:
        print(f"  - {sheet['friendly_name']} (ID: {sheet['doc_id']}, Default: {sheet['is_default']})")
    
    print("\n=== Example completed ===")


if __name__ == "__main__":
    # Run the example
    asyncio.run(example_usage())
