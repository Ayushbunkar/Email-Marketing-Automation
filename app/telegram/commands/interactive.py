"""Interactive wizard commands for Telegram."""
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler
from app.db import async_session_factory
from app.services.campaigns import create_campaign
from app.schemas.campaign import CampaignCreate

logger = logging.getLogger(__name__)

# States
NAME, GOAL, AUDIENCE, CONFIRM = range(4)

async def create_campaign_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the campaign creation wizard."""
    # If triggered by a button, we must answer it
    if update.callback_query:
        await update.callback_query.answer()
        
    from telegram import ForceReply
    await update.effective_message.reply_text(
        "Let's create a new Campaign.\n"
        "First, what is the name of this campaign?",
        reply_markup=ForceReply(selective=True)
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save name and ask for goal."""
    context.user_data['campaign_name'] = update.message.text
    
    reply_keyboard = [['broadcast', 'sequence']]
    await update.message.reply_text(
        "Great! What is the type of this campaign?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return GOAL

async def get_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save goal/type and ask for audience/goal details."""
    context.user_data['campaign_type'] = update.message.text.lower()
    
    from telegram import ForceReply
    await update.message.reply_text(
        "Got it. What is the goal or topic of this email? (e.g., Promote our new summer sale)",
        reply_markup=ForceReply(selective=True)
    )
    return AUDIENCE

async def get_audience(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save goal and confirm."""
    context.user_data['campaign_goal'] = update.message.text
    
    # Normally we'd call the LLM here to generate the template and save it.
    # For now, we will just create a draft campaign.
    reply_keyboard = [['Yes, Create Draft', 'Cancel']]
    
    summary = (
        f"<b>Campaign Summary</b>\n"
        f"Name: {context.user_data['campaign_name']}\n"
        f"Type: {context.user_data['campaign_type']}\n"
        f"Goal: {context.user_data['campaign_goal']}\n\n"
        "Create this draft campaign now?"
    )
    
    await update.message.reply_html(
        summary,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return CONFIRM

async def confirm_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Create the campaign in the database."""
    text = update.message.text
    
    if text == 'Cancel':
        await update.message.reply_text("Campaign creation cancelled.", reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return ConversationHandler.END
        
    try:
        async with async_session_factory() as session:
            payload = CampaignCreate(
                name=context.user_data['campaign_name'],
                goal=context.user_data['campaign_goal'],
                status="draft",
            )
            # In a real app we'd attach audience and generate templates
            new_camp = await create_campaign(session, payload)
            
        await update.message.reply_html(
            f"✅ Campaign created successfully as a draft!\nOpen the dashboard to edit and launch it.",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        logger.error(f"Failed to create campaign via Telegram: {e}")
        await update.message.reply_text(f"Error creating campaign.", reply_markup=ReplyKeyboardRemove())
        
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the wizard."""
    await update.message.reply_text("Wizard cancelled.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

from telegram.ext import CallbackQueryHandler

def get_interactive_handlers() -> list:
    """Get conversation handlers."""
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("createcampaign", create_campaign_start),
            CallbackQueryHandler(create_campaign_start, pattern="^nav_ai$")
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_goal)],
            AUDIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_audience)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_creation)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    return [conv_handler]
