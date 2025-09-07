#!/usr/bin/env python3
"""
Detailed import test to find the hanging issue
"""

print("Starting detailed import test...")

try:
    print("1. Testing BaseCallbackHandler import...")
    from handlers.base_callback_handler import BaseCallbackHandler
    print("✅ BaseCallbackHandler imported successfully")
except Exception as e:
    print(f"❌ Error importing BaseCallbackHandler: {e}")
    import traceback
    traceback.print_exc()

try:
    print("2. Testing ReceiptEditCallbackHandler import...")
    from handlers.receipt_edit_callback_handler import ReceiptEditCallbackHandler
    print("✅ ReceiptEditCallbackHandler imported successfully")
except Exception as e:
    print(f"❌ Error importing ReceiptEditCallbackHandler: {e}")
    import traceback
    traceback.print_exc()

try:
    print("3. Testing IngredientMatchingCallbackHandler import...")
    from handlers.ingredient_matching_callback_handler import IngredientMatchingCallbackHandler
    print("✅ IngredientMatchingCallbackHandler imported successfully")
except Exception as e:
    print(f"❌ Error importing IngredientMatchingCallbackHandler: {e}")
    import traceback
    traceback.print_exc()

try:
    print("4. Testing GoogleSheetsCallbackHandler import...")
    from handlers.google_sheets_callback_handler import GoogleSheetsCallbackHandler
    print("✅ GoogleSheetsCallbackHandler imported successfully")
except Exception as e:
    print(f"❌ Error importing GoogleSheetsCallbackHandler: {e}")
    import traceback
    traceback.print_exc()

try:
    print("5. Testing FileGenerationCallbackHandler import...")
    from handlers.file_generation_callback_handler import FileGenerationCallbackHandler
    print("✅ FileGenerationCallbackHandler imported successfully")
except Exception as e:
    print(f"❌ Error importing FileGenerationCallbackHandler: {e}")
    import traceback
    traceback.print_exc()

try:
    print("6. Testing CallbackHandlers import...")
    from handlers.callback_handlers import CallbackHandlers
    print("✅ CallbackHandlers imported successfully")
except Exception as e:
    print(f"❌ Error importing CallbackHandlers: {e}")
    import traceback
    traceback.print_exc()

print("Detailed import test completed!")
