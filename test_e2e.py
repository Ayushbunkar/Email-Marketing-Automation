import asyncio
import os
from dotenv import load_dotenv

# Load env before importing app
load_dotenv()

from app.db import async_session_factory
from app.models.campaign import Campaign, CampaignStatus
from app.models.template import Template
from app.models.contact import Contact, ContactStatus
from app.models.message import MessageStatus
from app.services.messages import create_message, send_message, get_provider
from app.config import settings

async def test_e2e():
    print("Testing End-to-End Hermes Backend Workflow...")
    
    async with async_session_factory() as session:
        # 1. Fetch or create a test contact
        dev_email = "ayushbunkar636@gmail.com"
        from sqlalchemy.future import select
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
            print("Created Contact.")
        else:
            print("Found Contact.")
            
        # 2. Create a fake Campaign
        campaign = Campaign(
            name="E2E Test Campaign",
            goal="Test integration",
            type="broadcast",
            status=CampaignStatus.APPROVED,
            settings={"from_email": "marketing@pixelpunch.org"},
            created_by="test_script"
        )
        session.add(campaign)
        await session.commit()
        await session.refresh(campaign)
        print("Created Campaign ID:", campaign.id)
        
        # 3. Create a fake Template
        template = Template(
            campaign_id=campaign.id,
            subject="Hello from Hermes E2E Test!",
            body_markdown="This is an automated test from the Hermes backend to prove end-to-end functionality is working flawlessly.",
        )
        session.add(template)
        await session.commit()
        await session.refresh(template)
        print("Created Template ID:", template.id)
        
        # 4. Create Message
        from datetime import datetime
        msg_obj = await create_message(
            session=session,
            campaign_id=campaign.id,
            step_index=None,
            contact_id=dev_contact.id,
            template_id=template.id,
            scheduled_for=datetime.utcnow(),
            status=MessageStatus.APPROVED
        )
        print("Created Message ID:", msg_obj.id)
        
        # 5. Send Transactional Message
        success = await send_message(session, msg_obj)
        print(f"Sent Transactional Message! Success: {success}")
        if not success:
            await session.refresh(msg_obj)
            print("Error reason:", msg_obj.error)
            
        # 6. Sync to Brevo Campaigns
        provider = get_provider()
        if hasattr(provider, 'create_marketing_campaign'):
            import markdown
            html_body = markdown.markdown(template.body_markdown) if template.body_markdown else ""
            
            camp_result = await provider.create_marketing_campaign(
                name=campaign.name,
                subject=template.subject,
                html_content=html_body,
                sender_email=campaign.from_email,
                sender_name=settings.FROM_NAME
            )
            print("Brevo Campaign Sync Result:", camp_result)
            
        await provider.close()

if __name__ == "__main__":
    asyncio.run(test_e2e())
