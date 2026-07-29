"""Security middleware for Telegram bot."""
import logging
from telegram import Update
from telegram.ext import TypeHandler, ContextTypes
from app.config import settings

logger = logging.getLogger(__name__)

async def security_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Verify the user is an authorized admin."""
    if not update.effective_user:
        return

    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id) if update.effective_chat else ""
    admin_ids = [id_str.strip() for id_str in settings.TELEGRAM_ADMIN_IDS.split(",") if id_str.strip()]
    
    if user_id not in admin_ids and chat_id not in admin_ids:
        logger.warning(f"Unauthorized access attempt from Telegram user ID: {user_id} in chat {chat_id}")
        # Stop propagation to other handlers
        raise context.application.StopPropagation()
        
    # User is authorized, log action
    logger.info(f"Authorized Telegram admin action from {user_id} in {chat_id}: {update.effective_message.text if update.effective_message else 'Callback/Other'}")

def get_security_handler() -> TypeHandler:
    """Return a handler that checks security on every update."""
    return TypeHandler(Update, security_check)
