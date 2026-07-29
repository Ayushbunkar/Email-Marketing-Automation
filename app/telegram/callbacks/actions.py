"""Callback handlers for Telegram Inline Keyboards."""
import logging
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from app.telegram.commands.campaigns import campaigns_command
from app.telegram.commands.contacts import contacts_command
from app.telegram.commands.inbox import inbox_command
from app.telegram.commands.analytics import analytics_command

logger = logging.getLogger(__name__)

async def navigation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle navigation callbacks from the main dashboard."""
    query = update.callback_query
    await query.answer()

    data = query.data
    
    if data == "nav_dashboard":
        # Delete the previous message to prevent duplicate dashboards piling up
        try:
            await query.message.delete()
        except:
            pass
        from app.telegram.commands.system import start_command
        await start_command(update, context)
    elif data == "nav_campaigns":
        await campaigns_command(update, context)
    elif data == "nav_contacts":
        await contacts_command(update, context)
    elif data == "nav_inbox" or data == "nav_replies":
        await inbox_command(update, context)
    elif data == "nav_analytics":
        await analytics_command(update, context)
    elif data == "nav_help":
        from app.telegram.commands.system import help_command
        await help_command(update, context)
    elif data == "nav_settings":
        msg = (
            "⚙ <b>Settings</b>\n\n"
            "This bot operates securely under your Hermes Workspace.\n"
            "To manage workspace preferences (billing, team members, integrations), please use the React Dashboard.\n\n"
            "Bot ID: <code>" + str(context.bot.id) + "</code>"
        )
        await query.message.reply_html(msg)
    elif data == "nav_approvals":
        # Show pending approvals
        # Re-use inbox command for now as approvals are primarily replies in this MVP
        await inbox_command(update, context)
    elif data.startswith("launch_"):
        campaign_id = data.replace("launch_", "")
        from app.db import async_session_factory
        from app.services.campaigns import update_campaign_status
        from app.models.campaign import CampaignStatus
        import asyncio
        
        try:
            # Step 1: Initialize
            await query.edit_message_text(
                "🚀 <b>Launch Sequence Initiated</b>\n"
                "▓░░░░░░░░░ [10%]\n"
                "<i>Identifying target audience segment...</i>",
                parse_mode="HTML"
            )
            
            async with async_session_factory() as session:
                await update_campaign_status(session, campaign_id, CampaignStatus.APPROVED, approved_by="telegram")
                
                # DEV MODE SAFETY: Fetch or create specific test contact
                from app.models.contact import Contact, ContactStatus
                from sqlalchemy.future import select
                
                dev_email = "ayushbunkar636@gmail.com"
                result = await session.execute(select(Contact).where(Contact.email == dev_email))
                dev_contact = result.scalar_one_or_none()
                
                if not dev_contact:
                    dev_contact = Contact(
                        email=dev_email,
                        first_name="Ayush",
                        last_name="Bunkar",
                        status=ContactStatus.ACTIVE
                    )
                    session.add(dev_contact)
                    await session.commit()
                
                contacts = [dev_contact]
                
                # Fetch the campaign for syncing
                from app.models.campaign import Campaign
                camp_result = await session.execute(select(Campaign).where(Campaign.id == campaign_id))
                campaign = camp_result.scalar_one_or_none()
                
                # Fetch the template
                from app.services.templates import list_templates
                templates = await list_templates(session, campaign_id=campaign_id)
                template = templates[0] if templates else None
                template_id = template.id if template else None
                
                # Step 2: Simulate Template Compilation
                await asyncio.sleep(1)
                await query.edit_message_text(
                    "🚀 <b>Launch Sequence</b>\n"
                    "▓▓▓▓░░░░░░ [40%]\n"
                    f"<i>Compiling email templates for {len(contacts)} contacts...</i>",
                    parse_mode="HTML"
                )
                
                # Step 3: Queue and Send
                await asyncio.sleep(1)
                await query.edit_message_text(
                    "🚀 <b>Launch Sequence</b>\n"
                    "▓▓▓▓▓▓▓░░░ [70%]\n"
                    "<i>Transmitting to Brevo API...</i>",
                    parse_mode="HTML"
                )
                
                from app.services.messages import create_message, send_message, MessageStatus, get_provider
                from app.config import settings
                from datetime import datetime
                
                # Actually send the emails via the provider
                for contact in contacts:
                    msg_obj = await create_message(
                        session=session,
                        campaign_id=campaign_id,
                        step_index=None,
                        contact_id=contact.id,
                        template_id=template_id,
                        scheduled_for=datetime.utcnow(),
                        status=MessageStatus.APPROVED
                    )
                    # This physically triggers the Brevo API request!
                    await send_message(session, msg_obj)
                
                # SYNC TO BREVO DASHBOARD
                provider = get_provider()
                if hasattr(provider, 'create_marketing_campaign') and campaign and template:
                    import markdown
                    html_body = markdown.markdown(template.body_markdown) if template.body_markdown else ""
                    from_email = campaign.from_email if campaign and campaign.from_email else settings.FROM_EMAIL
                    
                    await provider.create_marketing_campaign(
                        name=campaign.name,
                        subject=template.subject or "Notification from Hermes",
                        html_content=html_body,
                        sender_email=from_email,
                        sender_name=settings.FROM_NAME
                    )
            
            # Step 4: Complete
            await query.edit_message_text(
                "✅ <b>Campaign Successfully Launched!</b>\n"
                "▓▓▓▓▓▓▓▓▓▓ [100%]\n\n"
                f"📨 <i>[DEV MODE] Safely sent 1 test email exclusively to:</i>\n"
                "<b>ayushbunkar636@gmail.com</b>\n\n"
                "📊 You can verify this in your Brevo Dashboard -> Transactional -> Logs.",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to launch: {e}")
            await query.message.reply_text(f"Failed to launch: {e}")
    else:
        await query.message.reply_html(f"Unrecognized action: {data}")

def get_callback_handlers() -> list:
    """Get all callback handlers."""
    return [
        CallbackQueryHandler(navigation_callback, pattern="^(nav_|launch_)"),
    ]
