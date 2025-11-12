
# Slack Events Service

Clean, modular service for handling Slack Events API callbacks.

## Module Structure

```
services/slack_events/
├── __init__.py                    # Package initialization
├── deduplication.py              # Event de-duplication with MongoDB TTL
├── slack_user_manager.py         # Bot membership event handler
├── slack_event_models.py         # Data models (EventContext, BotEventInfo)
├── slack_event_helpers.py        # Reusable utility functions
├── slack_config.py               # Centralized Slack configuration management
├── slack_channel_repository.py   # Repository pattern for channel data access
├── slack_events_service.py       # Event dispatch service (instantiate and register handlers)
├── README.md                     # This file
└── HELPERS_README.md             # Documentation for helper functions
```

## Modules

### deduplication.py
- **Purpose**: Prevent duplicate event processing
- **Functions**:
  - `ensure_dedup_collection()` - Creates TTL index
  - `is_event_processed(event_id) -> bool` - Check and mark events
- **Features**:
  - MongoDB TTL collection (10-minute expiry)
  - Atomic insert for deduplication
  - Lazy index creation

### slack_event_models.py
- **Purpose**: Data models for Slack events
- **Classes**:
  - `EventContext` - Structured event representation
  - `BotEventInfo` - Bot-specific event information
- **Features**:
  - Type-safe event data structures
  - Consistent interface across event types

### slack_event_helpers.py
- **Purpose**: Reusable utility functions for event processing
- **Functions**:
  - `extract_event()` - Parse event context from payload
  - `get_bot_user_id()` - Extract bot ID from authorizations
  - `resolve_event_time()` - Get event timestamp with fallbacks
  - `is_bot_event()` - Check if event is about the bot
  - `create_bot_event_info()` - Create structured bot event info
  - `log_bot_event()` - Log events in consistent format
- **Features**:
  - Common operations for all event handlers
  - Extensible event rules system
  - Consistent logging and error handling

### slack_config.py
- **Purpose**: Centralized Slack configuration management
- **Class**: `SlackEventConfig` (Singleton)
- **Methods**:
  - `get_configured_connector()` - Get configured SlackConnector
- **Features**:
  - Singleton pattern for consistent configuration
  - Matches SlackPipelineFactory configuration
  - Handles configuration errors gracefully

### slack_channel_repository.py
- **Purpose**: Repository pattern for channel data operations
- **Class**: `SlackChannelRepository`
- **Methods**:
  - `find_by_channel_id()` - Find channel by ID
  - `update_membership()` - Update bot membership status
  - `create_channel()` - Create new channel document
  - `get_or_create_channel()` - Get existing or create new channel
- **Features**:
  - Clean abstraction for MongoDB operations
  - Automatic API fallback with minimal channel creation
  - Consistent error handling and logging

### slack_user_manager.py
- **Purpose**: Handle Slack bot membership events
- **Class**: `SlackUserManager`
- **Methods**:
  - `handle_member_joined(payload)` - Bot joins channel (backward compatibility)
  - `handle_member_left(payload)` - Bot leaves/removed from channel (backward compatibility)
  - `handle(payload)` - Main unified event handler
- **Features**:
  - Uses repository pattern for data access
  - Leverages helper functions for consistent processing
  - Clean separation of concerns

### slack_events_service.py
- **Purpose**: Event dispatch and handler registration
- **API**:
  - `process_event(payload)` - Dispatch payload to the correct handler
  - `register_handler(handler_cls)` - Register a handler class
- **Features**:
  - Singleton service with centralized registry
  - Clean public API used by tasks/endpoints

## Usage

### In Celery Task
```python
from services.slack_events.slack_events_service import SlackEventService
from services.slack_events.handlers.channel_created_handler import ChannelCreatedEventHandler

@CeleryApp().app.task(bind=True)
def process_slack_events_task(self, payload):
    event_service = SlackEventService()
    event_service.register_class(ChannelCreatedEventHandler)
    try:
        event_service.dispatch(payload)
    except Exception as e:
        raise self.retry(exc=e)
```

## Bot ID Management

### Current Bot ID
**Bot User ID:** `U08P1DCLX08` (extracted dynamically from `payload.authorizations[0].user_id`)

### Bot ID Extraction
```python
def _get_bot_user_id(self, payload: Dict[str, Any]) -> Optional[str]:
    authorizations = payload.get('authorizations', [])
    if authorizations and len(authorizations) > 0:
        return authorizations[0].get('user_id')
    return None
```

### Key Design Principles
- ✅ **Dynamic Extraction:** Never hardcode bot IDs
- ✅ **Workspace Aware:** Each workspace gets different bot ID  
- ✅ **Event Validation:** Only process events for our bot
- ✅ **Resilient:** Handles bot ID changes automatically

### Bot ID Change Scenarios
See `SLACK_EVENTS_SETUP.md` for complete details on when bot ID might change.

**TL;DR:** Bot ID is stable unless you:
- Delete/recreate the Slack app
- Install in different workspaces  
- Migrate from legacy bots

## Using Helper Functions

The helper modules make it easy to create new event handlers:

```python
from .slack_event_helpers import (
    extract_event, 
    get_bot_user_id, 
    is_bot_event,
    BOT_MEMBERSHIP_EVENT_RULES
)

def my_event_handler(payload):
    ctx = extract_event(payload)
    bot_id = get_bot_user_id(payload)
    
    is_about_bot, action = is_bot_event(ctx, bot_id, BOT_MEMBERSHIP_EVENT_RULES)
    if is_about_bot:
        # Process the event...
        pass
```

For detailed examples, see `HELPERS_README.md`.

## Adding New Event Types

### Method 1: Direct Registration (Recommended)

1. **Add handler** in `event_handlers.py`:
```python
def handle_new_event_type(event: Dict[str, Any], bot_user_id: str, event_time: float):
    """Handle new event type."""
    # Your logic here
    pass
```

2. **Register handler** in `processor.py` (add to EVENT_HANDLERS dict):
```python
EVENT_HANDLERS = {
    'member_joined_channel': handle_member_joined_channel,
    'group_left': handle_member_left_channel,
    'new_event_type': handle_new_event_type,  # Add this line
}
```

3. **Subscribe** in Slack app settings:
   - Go to Event Subscriptions
   - Add bot event: `new_event_type`

### Method 2: Dynamic Registration

You can also register handlers at runtime:

```python
from services.slack_events import register_event_handler

def my_custom_handler(event, bot_user_id, event_time):
    # Your custom logic
    pass

register_event_handler('custom_event_type', my_custom_handler)
```

## Design Principles

✅ **Separation of Concerns**: Each module has a single responsibility  
✅ **Clean Interfaces**: Simple, testable functions  
✅ **No Business Logic in Endpoints**: Endpoints only handle HTTP concerns  
✅ **No Business Logic in Tasks**: Tasks only handle Celery concerns  
✅ **Reusable Components**: Functions can be imported and tested independently  

## Testing

Each module can be tested independently:

```python
# Test deduplication
from services.slack_events.deduplication import is_event_processed
assert is_event_processed("Ev123") == False
assert is_event_processed("Ev123") == True  # Second time is duplicate

# Test event handler
from services.slack_events.event_handlers import handle_member_joined_channel
handle_member_joined_channel(event, bot_id, timestamp)
```

## MongoDB Collections

### data_sources.slack_event_dedup
- **Purpose**: Event de-duplication
- **Schema**: `{_id: event_id, createdAt: timestamp}`
- **TTL**: 600 seconds (10 minutes)

### data_sources.channels
- **Purpose**: Channel membership tracking
- **Schema**: `{channel_id, is_app_member, last_updated, ...}`
- **Updates**: Minimal (only membership fields)

## Error Handling

All functions include proper error handling:
- Deduplication: Returns `False` (not processed) on error
- Event handlers: Log errors and continue
- Processor: Raises exceptions for Celery retry

## Logging

All operations are logged with appropriate levels:
- `INFO`: Normal operations, event processing
- `WARNING`: Non-critical issues (missing fields, etc.)
- `ERROR`: Critical errors requiring attention
- `DEBUG`: Detailed information for troubleshooting


