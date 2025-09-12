"""
English texts for Telegram bot
Contains all message texts, buttons, errors and notifications in English
"""

EN_TRANSLATIONS = {
    # Welcome messages
    "welcome": {
        "start_message": "Hello, {user}! 👋\n\nChoose an action:",
        "analyze_receipt": "📸 Receipt Analysis\n\nSend a photo of the receipt for analysis:",
        "main_menu": "🏠 Main Menu\n\nUse /start to begin new work.",
        "choose_language": "🌍 Choose language / Choose language:",
        "dashboard": {
            "welcome_message": "👤 Personal Dashboard\n\nWelcome, {user}!\n\nChoose a setting:",
            "buttons": {
                "language_settings": "🌍 Language Settings",
                "google_sheets_management": "⚙️ Google Sheets"
            }
        }
    },
    
    # Interface buttons
    "buttons": {
        # Main actions
        "analyze_receipt": "📸 Analyze receipt",
        "generate_supply_file": "📄 Get file for poster upload",
        "back_to_receipt": "◀️ Back to receipt",
        "back_to_main_menu": "◀️ Back",
        "dashboard": "👤 Dashboard",
        
        
        # Receipt editing
        "add_row": "➕ Add row",
        "delete_row": "➖ Delete row",
        "edit_line_number": "🔢 Edit row by number",
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
        "fix_line": "Fix line {line_number}",
        
        # Total actions
        "auto_calculate_total": "🧮 Calculate automatically",
        "manual_edit_total": "✏️ Enter manually",
        
        # Status and actions
        "finish": "Report is ready!",
        "noop": "Unknown action"
    },
    
    # Error messages
    "errors": {
        "receipt_data_not_found": "❌ Receipt data not found",
        "operation_cancelled": "❌ Operation cancelled\n\nUse /start to begin new work.",
        "unknown_action": "Unknown action",
        "unsupported_language": "❌ Unsupported language",
        "language_fallback": "❌ Unsupported language. Russian language set as default.",
        "field_not_specified": "❌ Error: field for editing not specified.\nPlease select a field for editing from the menu.",
        "line_not_found": "Error: line not found",
        "data_not_found": "An error occurred, data not found.",
        "parsing_error": "Failed to recognize receipt structure. Try taking a clearer photo.",
        "photo_processing_error": "An error occurred while processing the photo: {error}",
        "field_edit_error": "Error editing field: {error}",
        "total_update_error": "Error updating total amount: {error}",
        "total_update_retry": "Error updating total amount. Please try again.",
        "critical_photo_error": "❌ Critical error processing photo",
        "invalid_update_object": "Invalid update object",
        "failed_to_edit_message": "Failed to edit message {message_id}: {error}",
        "failed_to_delete_message": "Failed to delete message {message_id}: {error}",
        "failed_to_delete_temporary_message": "Failed to delete temporary message {message_id}: {error}",
        "photos_already_processing": "❌ Photos are already being processed. Please wait for completion.",
        "too_many_photos": "❌ Too many photos. Maximum {max_photos} photos allowed at once.",
        "multiple_photos_error": "❌ Error processing multiple photos: {error}",
        "no_successful_photos": "❌ No photos were processed successfully. Please try again with clearer photos.",
        "no_photos_in_group": "❌ No photos found in the media group."
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
        "try_again": "Please try again:",
        "no_items": "No product items",
        "incorrect_line_numbering": "Incorrect line numbering: {line_numbers}, expected: {expected_numbers}",
        "missing_name_field": "Missing name field in line {line_number}",
        "missing_status_field": "Missing status field in line {line_number}",
        "missing_quantity_field": "Missing quantity field in line {line_number}",
        "missing_price_field": "Missing price field in line {line_number}",
        "missing_total_field": "Missing total field in line {line_number}",
        "calculation_warning": "Warning: Line {line_number} - calculations don't match: {quantity} * {price} = {expected_total}, but receipt shows {total}",
        "data_correct": "Data is correct",
        "line_number_correct": "Line number is correct",
        "field_cannot_be_empty": "{field_name} cannot be empty",
        "invalid_numeric_format": "Invalid {field_name} format. Enter a number",
        "value_correct": "Value is correct",
        "field_too_long": "{field_name} is too long (maximum 100 characters)"
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
        "ingredients_loaded": "✅ Loaded {count} ingredients from Google Sheets",
        "processing_multiple_photos": "📸 Processing {total} photos... ({processed}/{total})",
        "processing_multiple_photos_progress": "📸 Processing photos...\n\n✅ Successful: {successful}\n❌ Failed: {failed}\n📊 Progress: {processed}/{total}",
        "multiple_photos_completed": "✅ Multiple photos processing completed!\n\n📊 Results:\n• Total photos: {total}\n• Successful: {successful}\n• Failed: {failed}"
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
        "new_item_name": "New item",
        "deleting_item_confirmation": "🗑️ Deleting item {item_number}\n\nConfirm deletion (yes/no):"
    },
    
    # Ingredient matching messages
    "matching": {
        "no_ingredients": "No ingredients for matching.",
        "matching_title": "**Ingredient matching:**\n",
        "statistics": "📊 **Statistics:** Total: {total} | 🟢 Exact: {exact} | 🟡 Partial: {partial} | 🔴 Not found: {none}\n",
        "table_header": "{'№':<2} | {'Product':<{name_width}} | {'Poster':<{name_width}} | {'Status':<4}",
        "manual_instructions": "**Manual matching instructions:**\n\n1. Select suggestion number for automatic matching\n2. Or enter '0' to skip this ingredient\n3. Or enter 'search: <name>' to search for other options\n\nExamples:\n• `1` - select first suggestion\n• `0` - skip\n• `search: tomato` - find options with 'tomato'",
        "no_search_results": "Nothing found for query '{query}'.",
        "search_results": "**Search results for '{query}':**\n",
        
        # Input processing messages
        "matching_data_not_found": "Error: matching data not found.",
        "failed_to_delete_message": "Failed to delete user message: {error}",
        "enter_search_query": "Enter search query after 'search:'",
        "ingredient_skipped": "✅ Skipped ingredient: {ingredient_name}",
        "ingredient_matched": "✅ Matched: {receipt_item} → {matched_ingredient}",
        "invalid_suggestion_number": "Invalid number. Enter a number from 1 to {max_number} or 0 to skip.",
        "invalid_format": "Invalid format. Enter suggestion number, 0 to skip or 'search: query' to search.",
        "processing_error": "Error processing manual matching: {error}",
        "try_again": "An error occurred. Please try again.",
        
        # Search messages
        "search_results_title": "**Search results for '{query}':**\n\n",
        "found_variants": "Found variants: **{count}**\n\n",
        "select_ingredient": "**Select ingredient for matching:**\n",
        "no_suitable_variants": "❌ **No suitable variants found for '{query}'**\n\nTry another search query or return to overview.",
        "nothing_found": "❌ **Nothing found for '{query}'**\n\nTry another search query or return to overview.",
        "no_suitable_results": "No suitable variants found for '{query}' (with probability > 50%).",
        "search_nothing_found": "Nothing found for '{query}'.",
        
        # Search buttons
        "new_search": "🔍 New search",
        "back_to_receipt": "📋 Back to overview",
        "skip_ingredient": "⏭️ Skip",
        "back": "◀️ Back",
        
        # Position matching messages
        "invalid_line_number": "Invalid line number. Enter a number from 1 to {max_lines}",
        "line_selected": "Line {line_number} selected. Now enter ingredient name from poster for search:",
        "invalid_line_format": "Invalid format. Enter only line number (e.g.: `3`):",
        
        # Matching progress
        "matching_progress": "**Ingredient matching** ({current}/{total})\n\n",
        "current_item": "**Current item:** {item_name}\n\n",
        "auto_matched": "✅ **Automatically matched:** {ingredient_name}\n\n",
        "continue_instruction": "Press /continue to go to next item.",
        
        # Final result
        "rematch_ingredients": "🔄 Rematch ingredients",
        "back_to_receipt_final": "📋 Back to receipt",
        
        # Callback messages for ingredient matching
        "callback": {
            "results_not_found": "❌ Matching results not found",
            "manual_matching": "✏️ Manual matching",
            "show_table": "📊 Show table",
            "back_to_edit": "◀️ Back",
            "auto_match_all": "🔄 Automatic matching",
            "matching_overview_title": "🔍 **Ingredient matching overview**\n\n",
            "statistics_title": "📊 **Statistics:**\n",
            "matched_count": "✅ Matched: {count}\n",
            "partial_count": "⚠️ Partial: {count}\n",
            "no_match_count": "❌ Not matched: {count}\n",
            "total_positions": "📝 Total positions: {count}\n\n",
            "choose_action": "Choose an action:",
            "position_selection_title": "🔍 **Select position for matching:**\n\n",
            "invalid_position_index": "❌ Invalid position index",
            "invalid_suggestion_number": "❌ Invalid suggestion number",
            "matching_position_title": "🔍 **Matching position {position}:**\n\n",
            "receipt_item": "📝 **Receipt item:** {item_name}\n\n",
            "suggestions_title": "💡 **Suggestions:**\n",
            "no_suggestions": "❌ No suggestions found\n",
            "manual_search": "🔍 Manual search",
            "skip_item": "❌ Skip",
            "back_to_list": "◀️ Back to list",
            "matching_completed": "✅ **Matching completed!**\n\n",
            "matched_item": "📝 **Item:** {item_name}\n",
            "matched_ingredient": "🎯 **Ingredient:** {ingredient_name}\n",
            "similarity_score": "📊 **Similarity:** {score:.2f}\n\n",
            "continue_to_next": "Moving to next position...",
            "next_position": "➡️ Next position",
            "matching_finished": "🎉 **Matching completed!**\n\n",
            "results_title": "📊 **Results:**\n",
            "matched_percentage": "📈 Percentage: {percentage:.1f}%\n\n",
            "all_matched": "🎯 All positions successfully matched!",
            "remaining_items": "⚠️ Remaining to match: {count} positions",
            "back_to_editing": "◀️ Back to editing",
            "changes_applied": "✅ Matching changes applied!\n\nMoving to next step...",
            "search_ingredient": "🔍 Search ingredient\n\nEnter ingredient name for search:",
            "back_without_changes": "✅ Back without saving changes\n\nChanges were not saved.",
            "cancel_back": "❌ Cancel back\n\nContinuing with current data."
        }
    },
    
    # Google Sheets Management messages
    "sheets_management": {
        "title": "📊 Google Sheets Management",
        "no_sheets_description": "You don't have any connected sheets yet. Let's add the first one!",
        "has_sheets_description": "Here are your connected sheets. The sheet with a star (⭐) is used by default for receipt uploads.",
        "add_new_sheet_instruction": "📊 **Add New Google Sheet**\n\nThis feature is coming soon! You will be able to add and configure your Google Sheets here.",
        "buttons": {
            "add_new_sheet": "➕ Add new sheet",
            "back_to_dashboard": "⬅️ Back"
        }
    },
    
    # Add new sheet messages
    "add_sheet": {
        "step1_title": "📄 Adding Table (Step 1 of 3)",
        "step1_instruction": "To connect a table, follow these steps:\n\n📝 1. Create a new Google Sheet, or use an existing one (make sure there's no confidential information).\n\n🔗 2. Click 'Share' button in the top right corner.\n\n📧 3. In the 'Add people and groups' field, paste this email:\n\n<code>{service_email}</code>\n\n✅ 4. Make sure you gave <b>Editor</b> permissions.\n\n📋 5. Copy the sheet link from your browser and send it to me in the next message.",
        "step2_title": "📝 Choose a Name (Step 2 of 3)",
        "step2_instruction": "✅ Great, access granted! Now choose a simple name for the table so you won't get confused. For example: <i>Home Expenses</i>.",
        "step3_title": "📊 Table Configuration (Step 3 of 3)",
        "step3_instruction": "Perfect! Table connected. By default, data will be written as follows:",
        "step3_question": "Use these settings or configure your own?",
        "table_headers": {
            "date": "Date",
            "product": "Product", 
            "quantity": "Qty",
            "price": "Price",
            "sum": "Sum"
        },
        "step3_success": "🎉 Table '{sheet_name}' successfully added!",
        "buttons": {
            "cancel": "⬅️ Cancel",
            "use_default": "✅ Use default",
            "configure_manual": "✏️ Configure manually"
        },
        "errors": {
            "invalid_url": "🤔 Can't access the table. Please double-check that you gave <b>Editor</b> permissions specifically for this email. Try sending the link again.",
            "invalid_sheet_id": "❌ Could not extract table ID from the link. Please send a correct Google Sheet link.",
            "save_failed": "⚠️ Error saving the table. Please try again.",
            "jwt_error": "⚠️ Access check issue. Continuing with table addition process."
        }
    },
    
    # Google Sheets messages
    "sheets": {
        "ingredients_loaded": "✅ Loaded {count} ingredients from Google Sheets on demand",
        "no_data_for_upload": "❌ **No data for upload**\n\nFirst you need to upload and analyze a receipt.\nClick 'Analyze receipt' and upload a receipt photo.",
        
        # Google Sheets search messages
        "no_line_selected": "Error: no line selected for matching.",
        "dictionary_not_loaded": "Error: Google Sheets dictionary not loaded.",
        "no_search_results": "No results found for '{query}' in Google Sheets.",
        "no_item_selected": "Error: no item selected for search.",
        "ingredients_loaded_for_search": "✅ Loaded {count} Google Sheets ingredients for search",
        "using_cached_ingredients": "✅ Using already loaded {count} Google Sheets ingredients",
        "search_results_title": "**Google Sheets search results for '{query}':**\n\n",
        "back_button": "◀️ Back",
        
        # Callback messages for Google Sheets
        "callback": {
            "matching_results_not_found": "❌ Matching results not found",
            "choose_action_for_matching": "Choose an action for working with matching:",
            "preview_data_not_found": "❌ Data for preview not found",
            "upload_preview_title": "📊 **Google Sheets upload preview**",
            "uploading_data": "📤 Uploading data to Google Sheets...",
            "receipt_data_not_found": "Receipt data not found",
            "upload_successful": "Upload successful",
            "upload_error": "❌ Upload error: {message}",
            "matching_data_not_found": "Error: matching data not found.",
            "dictionary_not_loaded": "Failed to load Google Sheets ingredients dictionary.\nCheck configuration settings.",
            "all_positions_processed": "✅ All positions processed!",
            "choose_position_for_matching": "**Choose position for matching**",
            "matching_updated": "✅ Matching updated!",
            "data_successfully_uploaded": "✅ **Data successfully uploaded to Google Sheets!**",
            "no_upload_data_for_undo": "No data about last upload to undo",
            "no_data_to_undo": "No data to undo",
            "undo_upload_failed": "Failed to undo upload: {message}",
            "unexpected_error": "❌ **Critical error**\n\nUnexpected error occurred while uploading to Google Sheets:\n`{error}`",
            "no_receipt_data_for_file": "❌ No receipt data for file generation.",
            "no_matching_data_for_file": "❌ No Google Sheets matching data for file generation.",
            "excel_generation_error": "❌ Error creating Excel file.",
            "excel_generation_error_detailed": "❌ Error creating Excel file: {error}",
            "matching_table_title": "**Matching with Google Sheets ingredients:**",
            "no_ingredients_for_matching": "No ingredients for matching.",
            "table_header": "№ | Name                 | Google Sheets        | Status",
            "manual_matching_editor_title": "**Google Sheets matching editor**",
            "current_item": "**Item:** {item_name}",
            "choose_suitable_ingredient": "**Choose suitable ingredient:**",
            "no_suitable_options": "❌ **No suitable options found**",
            "undo_error_title": "❌ **{error_message}**",
            "undo_error_info": "Information about last upload not found.",
            "undo_successful": "✍️ **Upload successfully undone!**",
            "cancelled_rows": "📊 **Cancelled rows:** {row_count}",
            "worksheet_name": "📋 **Worksheet:** {worksheet_name}",
            "undo_time": "🕒 **Undo time:** {time}",
            "data_deleted_from_sheets": "Data was deleted from Google Sheets.",
            "excel_file_created": "📄 **Excel file with receipt data created!**",
            "excel_success_title": "✅ **Excel file successfully created!**",
            "excel_success_description": "File contains the same data that was uploaded to Google Sheets.",
            "file_available_for_download": "⏰ **File will be available for download for 5 minutes**",
            "no_data_to_display": "No data to display",
            "date_header": "Date",
            "volume_header": "Vol",
            "price_header": "price",
            "product_header": "Product",
            "total_label": "Total:",
            "new_item_name": "New item",
            "invalid_item_index": "Error: invalid item index.",
            "invalid_suggestion_index": "Error: invalid suggestion index.",
            "invalid_search_result_index": "Error: invalid search result index.",
            "matched_successfully": "✅ Matched: {receipt_item} → {ingredient_name}",
            "edit_matching": "✏️ Edit matching",
            "preview": "👁️ Preview",
            "back_to_receipt": "◀️ Back to receipt",
            "upload_to_google_sheets": "✅ Upload to Google Sheets",
            "back": "◀️ Back",
            "select_position_for_matching": "🔍 Select position for matching",
            "search": "🔍 Search",
            "undo_upload": "↩️ Undo upload",
            "generate_file": "📄 Generate file",
            "upload_new_receipt": "📸 Upload new receipt",
            "back_to_receipt_button": "📋 Back to receipt",
            "preview_google_sheets": "👁️ Preview Google Sheets"
        }
    },
    
    # File messages
    "files": {
        "no_data": "No data to display",
        "table_header": "{'№':^{number_width}} | {'Product':<{product_width}} | {'Qty':^{quantity_width}} | {'Price':^{price_width}} | {'Amount':>{total_width}} | {'':^{status_width}}",
        "total_label": "Total:"
    },
    
    # File generation messages
    "file_generation": {
        "generating_file": "📄 Generating file...",
        "file_ready": "📄 File for {file_type} upload ready!",
        "success_title": "✅ **{file_type} file successfully generated!**",
        "filename": "📁 **Filename:** {filename}",
        "positions_count": "📊 **Positions:** {count}",
        "generation_date": "📅 **Date:** {date}",
        "show_table": "📊 Show table",
        "back_to_edit": "◀️ Back to editing",
        "download_poster_file": "📄 Download poster file",
        "download_google_sheets_file": "📊 Download Google Sheets file",
        "matching_table_title": "📊 **Ingredient matching table:**",
        "table_header": "| № | Receipt item | Ingredient | Status | Similarity |",
        "table_separator": "|---|---|---|---|---|",
        "legend_title": "💡 **Legend:**",
        "legend_matched": "✅ - Matched",
        "legend_partial": "⚠️ - Partially matched",
        "legend_not_matched": "❌ - Not matched",
        "not_matched": "Not matched",
        "error_generating_file": "❌ Error generating file: {error}",
        "google_sheets_handler_unavailable": "❌ Google Sheets handler not available for Excel generation",
        "ingredient_matching_handler_unavailable": "❌ Ingredient matching handler not available",
        "matching_results_not_found": "❌ Matching results not found",
        "receipt_data_not_found": "❌ Receipt data not found"
    },
    
    # Common messages and helpers
    "common": {
        "no_data_to_display": "No data to display",
        "page": "Page {page}",
        "unknown_ingredient_type": "DEBUG: Unknown ingredient type: {ingredient_type}",
        "loaded_poster_ingredients": "DEBUG: Loaded {count} poster ingredients",
        "loaded_google_sheets_ingredients": "✅ Loaded {count} Google Sheets ingredients on demand",
        "debug_first_ingredients": "DEBUG: First 5 ingredients: {ingredients}",
        "navigation_buttons": {
            "first_page": "⏮️",
            "previous_page": "◀️", 
            "next_page": "▶️",
            "last_page": "⏭️"
        },
        "status_emojis": {
            "confirmed": "✅",
            "error": "🔴",
            "partial": "⚠️",
            "no_match": "❌",
            "exact_match": "🟢",
            "matched": "✅",
            "partial_match": "🟡",
            "unknown": "❓"
        }
    },
    
    # Formatting messages
    "formatters": {
        "no_data_to_display": "No data to display",
        "table_headers": {
            "number": "№",
            "product": "Product",
            "quantity": "Qty",
            "price": "Price",
            "amount": "Amount"
        },
        "total_label": "Total:"
    }
    
}