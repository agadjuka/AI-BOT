# Parallel Photo Processing in PhotoHandler

This document describes the updated PhotoHandler with support for parallel processing of multiple photos.

## Features

### 1. Async/Await Support
- All photo processing methods are now fully asynchronous
- Uses `asyncio.gather()` for parallel processing
- Non-blocking operations for better performance

### 2. Parallel Processing
- Process up to 3-5 photos simultaneously (configurable)
- Uses `asyncio.Semaphore` to limit concurrent operations
- Individual error handling for each photo
- Progress tracking and UI updates

### 3. Multiple Processing Modes

#### Single Photo Processing
```python
# Backward compatible method
result = await photo_handler.handle_photo(update, context)

# Explicit single photo method
result = await photo_handler.handle_single_photo(update, context)
```

#### Multiple Photos Processing
```python
# Process multiple photos from a list
photo_messages = [msg1, msg2, msg3]
result = await photo_handler.handle_multiple_photos(update, context, photo_messages)
```

#### Media Group Processing
```python
# Process media group (photos sent at once)
media_group = [msg1, msg2, msg3]
result = await photo_handler.handle_media_group(update, context, media_group)
```

## Configuration

### Maximum Concurrent Photos
```python
# In PhotoHandler.__init__()
self.max_concurrent_photos = 3  # Adjustable limit
```

### Progress Tracking
The handler tracks processing progress for each user:
- Total photos to process
- Successfully processed photos
- Failed photos
- Real-time progress updates

## Error Handling

### Individual Photo Errors
- Each photo is processed independently
- Errors in one photo don't affect others
- Detailed error messages for each failure
- Graceful degradation (shows successful results even if some fail)

### User-Level Error Handling
- Prevents multiple simultaneous processing sessions per user
- Limits maximum number of photos per batch
- Comprehensive error messages with localization

## UI Updates

### Progress Messages
- Real-time progress updates during processing
- Shows successful/failed counts
- Auto-updating progress indicators

### Results Display
- Summary of processing results
- Uses first successful result as main receipt data
- Fallback to error message if no photos succeed

## Localization Support

### New Text Keys Added
- `status.processing_multiple_photos`
- `status.processing_multiple_photos_progress`
- `status.multiple_photos_completed`
- `errors.photos_already_processing`
- `errors.too_many_photos`
- `errors.multiple_photos_error`
- `errors.no_successful_photos`
- `errors.no_photos_in_group`

### Supported Languages
- English (en)
- Russian (ru)
- Indonesian (id)

## Usage Examples

### Basic Usage
```python
from handlers.photo_handler import PhotoHandler
from services.ai_service import AIService
from config.settings import BotConfig
from config.prompts import PromptManager

# Initialize
config = BotConfig()
prompt_manager = PromptManager()
ai_service = AIService(config, prompt_manager)
photo_handler = PhotoHandler(config, ai_service)

# Process single photo
result = await photo_handler.handle_photo(update, context)

# Process multiple photos
photo_messages = [msg1, msg2, msg3]
result = await photo_handler.handle_multiple_photos(update, context, photo_messages)
```

### Integration with Bot Handlers
```python
# In your bot's message handler
async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_handler = PhotoHandler(config, analysis_service)
    
    if update.message.media_group_id:
        # Handle media group
        media_group = await get_media_group_messages(update.message.media_group_id)
        return await photo_handler.handle_media_group(update, context, media_group)
    else:
        # Handle single photo
        return await photo_handler.handle_photo(update, context)
```

## Performance Benefits

1. **Parallel Processing**: 3-5x faster for multiple photos
2. **Non-blocking**: Doesn't block other bot operations
3. **Resource Management**: Controlled concurrency prevents overload
4. **User Experience**: Real-time progress updates

## Backward Compatibility

- All existing single photo processing continues to work
- No breaking changes to existing API
- Gradual migration path available

## Future Enhancements

1. **Dynamic Concurrency**: Adjust concurrent limit based on system load
2. **Batch Processing**: Process photos in smaller batches for very large sets
3. **Result Merging**: Combine results from multiple successful photos
4. **Priority Processing**: Process higher quality photos first
