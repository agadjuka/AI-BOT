"""
English texts for Telegram bot
Contains all message texts, buttons, errors and notifications in English
"""

TEXTS = {
    # Welcome messages
    "welcome": {
        "start_message": "Hello, {user}! 👋\n\nChoose an action:",
        "analyze_receipt": "📸 Receipt Analysis\n\nSend a photo of the receipt for analysis:",
        "main_menu": "🏠 Main Menu\n\nUse /start to begin new work.",
        "choose_language": "🌍 Choose language / Выберите язык:"
    },
    
    # Interface buttons
    "buttons": {
        # Main actions
        "analyze_receipt": "📸 Analyze Receipt",
        "generate_supply_file": "📄 Get File for Poster Upload",
        "back_to_receipt": "◀️ Back to Receipt",
        "back_to_main_menu": "◀️ Back",
        
        # Language selection
        "language_russian": "🇷🇺 Русский",
        "language_english": "🇺🇸 English",
        
        # Receipt editing
        "add_row": "➕ Add Row",
        "delete_row": "➖ Delete Row",
        "edit_line_number": "🔢 Edit Row by Number",
        "edit_total": "💰 Edit Total",
        "reanalyze": "🔄 Re-analyze",
        "upload_to_google_sheets": "📊 Upload to Google Sheets",
        
        # Field editing
        "edit_name": "📝 Name",
        "edit_quantity": "🔢 Quantity", 
        "edit_price": "💰 Price",
        "edit_total_field": "💵 Amount",
        "apply_changes": "✅ Apply",
        "cancel": "❌ Cancel",
        
        # Total actions
        "auto_calculate_total": "🧮 Calculate Automatically",
        "manual_edit_total": "✏️ Enter Manually",
        
        # Status and actions
        "finish": "Report is already ready!",
        "noop": "Unknown action"
    },
    
    # Error messages
    "errors": {
        "receipt_data_not_found": "❌ Receipt data not found",
        "operation_cancelled": "❌ Operation cancelled\n\nUse /start to begin new work.",
        "unknown_action": "Unknown action",
        "field_not_specified": "❌ Error: field not specified for editing.\nPlease select a field to edit from the menu.",
        "line_not_found": "Error: line not found",
        "data_not_found": "An error occurred, data not found.",
        "parsing_error": "Could not recognize receipt structure. Try taking a clearer photo.",
        "photo_processing_error": "An error occurred while processing the photo: {error}",
        "field_edit_error": "Error editing field: {error}",
        "total_update_error": "Error updating total amount: {error}",
        "total_update_retry": "Error updating total amount. Please try again.",
        "critical_photo_error": "❌ Critical error processing photo: {error}"
    },
    
    # Validation messages
    "validation": {
        "line_number_too_small": "Line number must be greater than 0",
        "line_number_too_large": "Line number {line_number} exceeds maximum {max_line_number}",
        "line_not_found": "Line {line_number} not found",
        "field_negative": "{field_name} cannot be negative",
        "invalid_line_format": "Invalid format. Enter only line number (e.g.: `3`):",
        "negative_value": "Value cannot be negative. Please try again.",
        "negative_total": "Total amount cannot be negative. Please try again.",
        "try_again": "Please try again:"
    },
    
    # Status messages
    "status": {
        "processing_receipt": "Processing receipt",
        "analyzing_receipt": "🔄 Re-analyzing photo...",
        "processing": "Processing...",
        "total_auto_calculated": "✅ Total automatically calculated: **{total}**",
        "line_deleted": "✅ Line {line_number} deleted! Updating table...",
        "total_updated": "✅ Total amount updated: **{total}**",
        "analysis_started": "🔍 Starting receipt analysis...",
        "analysis_completed": "✅ Analysis completed",
        "ingredients_loaded": "✅ Loaded {count} Google Sheets ingredients"
    },
    
    # Analysis messages
    "analysis": {
        "errors_found": "🔴 **Errors found in receipt data**\n\n",
        "total_matches": "✅ **Total amount matches!**\n",
        "total_mismatch": "❗ **Total amount mismatch! Difference: {difference}**\n",
        "auto_calculated": "*(automatically calculated)*",
        "editing_line": "**Editing line {line_number}:** {status_icon}\n\n",
        "editing_total": "**Editing total:**\n\n",
        "current_total": "💰 **Current total amount:** {total}\n",
        "calculated_total": "🧮 **Automatically calculated amount:** {calculated_total}\n\n",
        "choose_action": "Choose an action:",
        "choose_field": "Choose field to edit:",
        "field_name": "📝 **Name:** {name}\n",
        "field_quantity": "🔢 **Quantity:** {quantity}\n", 
        "field_price": "💰 **Price:** {price}\n",
        "field_total": "💵 **Amount:** {total}\n\n",
        "deleting_line": "🗑️ Deleting line\n\nEnter line number to delete:",
        "editing_line_input": "✏️ Editing line\n\nEnter line number to edit:",
        "editing_total_input": "💰 Editing total amount\n\nEnter new total amount:",
        "field_display_names": {
            "name": "product name",
            "quantity": "quantity", 
            "price": "price",
            "total": "amount"
        },
        "field_edit_input": "✏️ Editing {field_name} for line {line_number}\n\nEnter new value:",
        "new_item_name": "New item"
    },
    
    # Ingredient matching messages
    "matching": {
        "no_ingredients": "No ingredients to match.",
        "matching_title": "**Ingredient Matching:**\n",
        "statistics": "📊 **Statistics:** Total: {total} | 🟢 Exact: {exact} | 🟡 Partial: {partial} | 🔴 Not found: {none}\n",
        "table_header": "{'№':<2} | {'Product':<{name_width}} | {'Poster':<{name_width}} | {'Status':<4}",
        "manual_instructions": "**Manual matching instructions:**\n\n1. Select suggestion number for automatic matching\n2. Or enter '0' to skip this ingredient\n3. Or enter 'search: <name>' to find other options\n\nExamples:\n• `1` - select first suggestion\n• `0` - skip\n• `search: tomato` - find options with 'tomato'",
        "no_search_results": "Nothing found for query '{query}'.",
        "search_results": "**Search results for '{query}':**\n"
    },
    
    # Google Sheets messages
    "sheets": {
        "ingredients_loaded": "✅ Loaded {count} Google Sheets ingredients on demand",
        "no_data_for_upload": "❌ **No data to upload**\n\nFirst, you need to load and analyze a receipt.\nClick 'Analyze Receipt' and upload a receipt photo."
    },
    
    # File messages
    "files": {
        "no_data": "No data to display",
        "table_header": "{'№':^{number_width}} | {'Product':<{product_width}} | {'Qty':^{quantity_width}} | {'Price':^{price_width}} | {'Amount':>{total_width}} | {'':^{status_width}}",
        "total_label": "Total:"
    }
}