import logging
from telegram.ext import Application
from app.telegram.middleware.security import get_security_handler
from app.telegram.commands.system import get_system_handlers
from app.telegram.commands.campaigns import get_campaign_handlers
from app.telegram.commands.contacts import get_contacts_handlers
from app.telegram.commands.inbox import get_inbox_handlers
from app.telegram.commands.analytics import get_analytics_handlers
from app.telegram.commands.interactive import get_interactive_handlers
from app.telegram.callbacks.actions import get_callback_handlers

logger = logging.getLogger(__name__)

def register_handlers(application: Application) -> None:
    """Register all bot handlers."""
    logger.info("Registering Telegram handlers...")
    
    # 1. Security Middleware (Must be group -1 or registered first in group 0)
    # We add it to group -1 so it runs before any other handlers.
    application.add_handler(get_security_handler(), group=-1)

    # 2. System Commands
    for handler in get_system_handlers():
        application.add_handler(handler)
        
    # 3. Domain Commands
    for handler in get_campaign_handlers() + get_contacts_handlers() + get_inbox_handlers() + get_analytics_handlers():
        application.add_handler(handler)
        
    # 4. Interactive Wizards
    for handler in get_interactive_handlers():
        application.add_handler(handler)
        
    # 5. Callbacks
    for handler in get_callback_handlers():
        application.add_handler(handler)
