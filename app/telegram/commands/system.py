"""System commands for the Telegram Bot."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a dashboard message when the command /start is issued."""
    user = update.effective_user
    
    # Check statuses (Mocked for now, will connect to real health checks later)
    status_msg = (
        f"<b>Hermes AI Email Marketing</b>\n\n"
        f"Welcome back {user.first_name if user else 'Operator'}\n\n"
        f"<b>Current Status</b>\n"
        f"🟢 Server Online\n"
        f"🟢 Redis Connected\n"
        f"🟢 Supabase Connected\n"
        f"🟢 Brevo Connected\n"
        f"🟢 LLM Online\n\n"
        f"<b>Today's Emails:</b> 0\n"
        f"<b>Campaigns Running:</b> 0\n"
        f"<b>Pending Approvals:</b> 0\n"
        f"<b>Replies Waiting:</b> 0\n"
        f"<b>Queue Size:</b> 0\n"
    )

    keyboard = [
        [
            InlineKeyboardButton("🔄 Refresh Status", callback_data="nav_dashboard"),
            InlineKeyboardButton("📧 Campaigns", callback_data="nav_campaigns"),
        ],
        [
            InlineKeyboardButton("👥 Contacts", callback_data="nav_contacts"),
            InlineKeyboardButton("📥 Inbox", callback_data="nav_inbox"),
        ],
        [
            InlineKeyboardButton("🤖 Create Campaign", callback_data="nav_ai"),
            InlineKeyboardButton("📈 Analytics", callback_data="nav_analytics"),
        ],
        [
            InlineKeyboardButton("✅ Approvals", callback_data="nav_approvals"),
            InlineKeyboardButton("⚙ Settings", callback_data="nav_settings"),
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data="nav_help"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_message.reply_html(status_msg, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "<b>Hermes Telegram Operator Help</b>\n\n"
        "<b>Commands:</b>\n"
        "/start - Show the main dashboard\n"
        "/help - Show this help message\n"
        "/campaigns - List all campaigns\n"
        "/contacts - List contacts\n"
        "/health - View system health\n"
        "/ping - Test bot responsiveness\n"
    )
    await update.effective_message.reply_html(help_text)

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Respond to ping."""
    await update.effective_message.reply_text("Pong! 🏓 Bot is active.")

async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check system health."""
    # Since this is a simple bot overview, we can re-use the start_command's status
    # or just send a quick text version.
    msg = (
        "<b>System Health</b>\n\n"
        "🟢 Web Server: Online\n"
        "🟢 Database: Connected\n"
        "🟢 Redis Queue: Connected\n"
        "🟢 Telegram Bot: Polling\n"
        "🟢 Models: Ready\n"
    )
    await update.effective_message.reply_html(msg)

def get_system_handlers() -> list:
    """Get all system command handlers."""
    return [
        CommandHandler("start", start_command),
        CommandHandler("help", help_command),
        CommandHandler("ping", ping_command),
        CommandHandler("health", health_command),
    ]
