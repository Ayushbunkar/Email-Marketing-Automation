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
    name = update.message.text
    
    # Check if a campaign with this name already exists
    from sqlalchemy.future import select
    from app.models.campaign import Campaign
    try:
        async with async_session_factory() as session:
            result = await session.execute(select(Campaign).where(Campaign.name == name))
            if result.scalar_one_or_none():
                await update.message.reply_text(
                    "❌ <b>Duplicated campaign!</b>\n"
                    "A campaign with this name already exists.\n\n"
                    "Please type a different name:",
                    parse_mode="HTML"
                )
                return NAME
    except Exception as e:
        logger.error(f"Error checking duplicate campaign name: {e}")
        
    context.user_data['campaign_name'] = name
    
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
            new_camp = await create_campaign(
                session=session,
                name=context.user_data['campaign_name'],
                goal=context.user_data['campaign_goal'],
                campaign_type=context.user_data['campaign_type'],
                created_by="telegram"
            )
            # Create a mock template for now
            from app.services.templates import create_template
            subject = f"Exciting news about: {new_camp.goal}"
            body_markdown = (
                f"Special Announcement: {new_camp.goal}\n\n"
                f"Hello {{{{first_name}}}},\n\n"
                f"We wanted to reach out regarding our upcoming {new_camp.goal}.\n"
                f"This is a fantastic opportunity for you to get involved and take advantage of what we're offering.\n\n"
                f"If you have any questions, feel free to reply directly to this email.\n\n"
                f"Best regards,\n"
                f"Pixel Punch"
            )
            
            await create_template(
                session=session,
                campaign_id=new_camp.id,
                subject=subject,
                body_markdown=body_markdown
            )
            
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [
                InlineKeyboardButton("🚀 Launch Campaign", callback_data=f"launch_{new_camp.id}"),
                InlineKeyboardButton("✏️ Edit Draft", callback_data=f"edit_draft_{new_camp.id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        draft_msg = (
            f"✅ <b>Campaign Draft Created!</b>\n\n"
            f"<b>Subject:</b> {subject}\n"
            f"<b>Body:</b>\n<i>{body_markdown}</i>\n\n"
            f"Click below to launch instantly, or open Dashboard to edit."
        )
            
        await update.message.reply_html(
            draft_msg,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Failed to create campaign via Telegram: {e}")
        await update.message.reply_text(f"Error creating campaign: {e}", reply_markup=ReplyKeyboardRemove())
        
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the wizard."""
    await update.message.reply_text("Wizard cancelled.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

from telegram.ext import CallbackQueryHandler

EDIT_BODY = 10

async def edit_draft_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the edit draft wizard."""
    query = update.callback_query
    await query.answer()
    campaign_id = query.data.replace("edit_draft_", "")
    context.user_data['edit_camp_id'] = campaign_id
    
    from app.services.templates import list_templates
    from app.db import async_session_factory
    
    current_body = ""
    try:
        async with async_session_factory() as session:
            templates = await list_templates(session, campaign_id=campaign_id)
            if templates:
                current_body = templates[0].body_markdown
    except Exception:
        pass
        
    msg = (
        "✏️ <b>Please type the new body for this email.</b>\n\n"
        "💡 <i>Tip: You can use {{first_name}} to automatically insert the contact's name!</i>\n\n"
        "Here is your current draft to copy and edit:\n\n"
        f"<code>{current_body}</code>"
    )
    
    from telegram import ForceReply
    await query.message.reply_html(msg, reply_markup=ForceReply(selective=True))
    return EDIT_BODY

async def save_draft_body(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save the new body to the template."""
    new_body = update.message.text
    campaign_id = context.user_data['edit_camp_id']
    from app.services.templates import list_templates, update_template
    
    try:
        async with async_session_factory() as session:
            templates = await list_templates(session, campaign_id=campaign_id)
            if templates:
                await update_template(session, templates[0].id, {"body_markdown": new_body})
        
        # Show the updated draft
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [
                InlineKeyboardButton("🚀 Launch Campaign", callback_data=f"launch_{campaign_id}"),
                InlineKeyboardButton("✏️ Edit Again", callback_data=f"edit_draft_{campaign_id}")
            ]
        ]
        await update.message.reply_html(
            f"✅ <b>Draft Updated!</b>\n\n<b>New Body:</b>\n<i>{new_body}</i>",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error editing draft: {e}")
        await update.message.reply_text(f"Error updating draft.", reply_markup=ReplyKeyboardRemove())
        
    context.user_data.clear()
    return ConversationHandler.END


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
    
    edit_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_draft_start, pattern="^edit_draft_")],
        states={
            EDIT_BODY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_draft_body)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    return [conv_handler, edit_handler]
