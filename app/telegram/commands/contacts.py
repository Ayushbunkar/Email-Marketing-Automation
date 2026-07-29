"""Contacts commands for Telegram."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from app.db import async_session_factory
from app.services.contacts import list_contacts

logger = logging.getLogger(__name__)

async def contacts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List recent contacts."""
    async with async_session_factory() as session:
        contacts = await list_contacts(session)
        
    if not contacts:
        await update.effective_message.reply_text("No contacts found.")
        return
        
    msg = "<b>Recent Contacts:</b>\n\n"
    # Show top 5 contacts
    for contact in contacts[:5]:
        name = f"{contact.first_name} {contact.last_name}".strip() or "Unnamed"
        msg += f"👤 <b>{name}</b>\n"
        msg += f"📧 {contact.email}\n"
        msg += f"🏷 Stage: {contact.lifecycle_stage}\n"
        msg += f"🟢 Status: {contact.status}\n\n"
        
    if len(contacts) > 5:
        msg += f"<i>...and {len(contacts) - 5} more. View Dashboard for all.</i>"
        
    # Example of inline buttons per contact or general action
    keyboard = [[InlineKeyboardButton("Open Dashboard", callback_data="nav_dashboard")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
        
    await update.effective_message.reply_html(msg, reply_markup=reply_markup)

async def import_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help with importing contacts."""
    msg = (
        "<b>Import Contacts</b>\n\n"
        "To import contacts in bulk, please use the Web Dashboard.\n"
        "1. Open Dashboard -> Contacts\n"
        "2. Click 'Import CSV'\n"
        "3. Map your columns\n"
    )
    await update.message.reply_html(msg)

def get_contacts_handlers() -> list:
    """Get all contacts command handlers."""
    return [
        CommandHandler("contacts", contacts_command),
        CommandHandler("import", import_command),
    ]
