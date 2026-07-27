"""Agent tools for campaign planning and execution."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, CampaignStatus, CampaignType
from app.models.contact import Contact, LifecycleStage
from app.models.suppression import Suppression
from app.models.template import Template


@dataclass
class ToolResult:
    """Tool execution result."""

    success: bool
    content: str
    error: Optional[str] = None


class AgentTools:
    """Agent tools for campaign planning and execution."""

    def __init__(self, session: AsyncSession = None):
        """Initialize the agent tools."""
        self.session = session

    async def search_contacts(
        self,
        stage: Optional[LifecycleStage] = None,
        text: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Search contacts by stage and text."""
        if not self.session:
            return []

        query = select(Contact)

        if stage:
            query = query.where(Contact.lifecycle_stage == stage)

        if text:
            query = query.where(
                func.or_(
                    Contact.first_name.ilike(f"%{text}%"),
                    Contact.last_name.ilike(f"%{text}%"),
                    Contact.email.ilike(f"%{text}%"),
                )
            )

        result = await self.session.execute(query.limit(limit))
        contacts = result.scalars().all()

        return [
            {
                "id": str(c.id),
                "email": c.email,
                "first_name": c.first_name,
                "last_name": c.last_name,
                "company": c.company,
                "lifecycle_stage": c.lifecycle_stage,
                "status": c.status,
            }
            for c in contacts
        ]

    async def create_campaign(
        self,
        name: str,
        goal: str,
        campaign_type: CampaignType,
        segment_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new campaign."""
        if not self.session:
            return {"id": "campaign_id", "name": name, "status": "draft"}

        from uuid import uuid4

        from app.models.campaign import Campaign

        campaign = Campaign(
            id=uuid4(),
            name=name,
            goal=goal,
            campaign_type=campaign_type,
            status=CampaignStatus.DRAFT,
            segment_id=segment_id,
        )
        self.session.add(campaign)
        await self.session.commit()

        return {
            "id": str(campaign.id),
            "name": campaign.name,
            "status": campaign.status,
        }

    async def create_template(
        self,
        campaign_id: str,
        subject: str,
        body_markdown: str,
        variant_label: str = "A",
    ) -> Dict[str, Any]:
        """Create a template for a campaign."""
        if not self.session:
            return {"id": "template_id", "campaign_id": campaign_id, "subject": subject}

        from uuid import uuid4

        template = Template(
            id=uuid4(),
            campaign_id=campaign_id,
            subject=subject,
            body_markdown=body_markdown,
            variant_label=variant_label,
        )
        self.session.add(template)
        await self.session.commit()

        return {
            "id": str(template.id),
            "campaign_id": campaign_id,
            "subject": subject,
        }

    async def get_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get a campaign by ID."""
        if not self.session:
            return None

        result = await self.session.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()

        if not campaign:
            return None

        return {
            "id": str(campaign.id),
            "name": campaign.name,
            "goal": campaign.goal,
            "campaign_type": campaign.campaign_type,
            "status": campaign.status,
            "segment_id": str(campaign.segment_id) if campaign.segment_id else None,
        }

    async def update_campaign_status(
        self,
        campaign_id: str,
        status: CampaignStatus,
    ) -> bool:
        """Update campaign status."""
        if not self.session:
            return True

        result = await self.session.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()

        if not campaign:
            return False

        campaign.status = status
        await self.session.commit()
        return True

    async def get_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Get a contact by ID."""
        if not self.session:
            return None

        result = await self.session.execute(
            select(Contact).where(Contact.id == contact_id)
        )
        contact = result.scalar_one_or_none()

        if not contact:
            return None

        return {
            "id": str(contact.id),
            "email": contact.email,
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "company": contact.company,
            "lifecycle_stage": contact.lifecycle_stage,
            "status": contact.status,
        }

    async def get_templates(self, campaign_id: str) -> List[Dict[str, Any]]:
        """Get templates for a campaign."""
        if not self.session:
            return []

        result = await self.session.execute(
            select(Template).where(Template.campaign_id == campaign_id)
        )
        templates = result.scalars().all()

        return [
            {
                "id": str(t.id),
                "campaign_id": str(t.campaign_id),
                "subject": t.subject,
                "body_markdown": t.body_markdown,
                "variant_label": t.variant_label,
            }
            for t in templates
        ]

    async def analyze_reply(
        self,
        reply_text: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze a reply and suggest response."""
        # This would use LLM in a real implementation
        return {
            "classification": "question",
            "confidence": 0.9,
            "suggested_response": "Thank you for your question!",
        }

    async def generate_copy(
        self,
        goal: str,
        audience: Dict[str, Any],
        tone: str = "professional",
    ) -> Dict[str, Any]:
        """Generate email copy using LLM."""
        # This would use LLM in a real implementation
        return {
            "subject": "Subject line",
            "body_markdown": "# Email body\n\nContent here.",
            "preheader": "Preheader text",
        }

    async def get_suppression_list(self) -> List[str]:
        """Get list of suppressed emails."""
        if not self.session:
            return []

        result = await self.session.execute(select(Suppression.email))
        suppressions = result.scalars().all()
        return suppressions

    async def is_suppressed(self, email: str) -> bool:
        """Check if an email is suppressed."""
        if not self.session:
            return False

        result = await self.session.execute(
            select(Suppression).where(Suppression.email == email)
        )
        return result.scalar_one_or_none() is not None

    async def get_segment_contacts(self, segment_id: str) -> List[Dict[str, Any]]:
        """Get contacts in a segment."""
        if not self.session:
            return []

        result = await self.session.execute(
            select(Contact).where(Contact.segment_id == segment_id)
        )
        contacts = result.scalars().all()

        return [
            {
                "id": str(c.id),
                "email": c.email,
                "first_name": c.first_name,
                "last_name": c.last_name,
            }
            for c in contacts
        ]

    async def get_campaign_metrics(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign metrics."""
        if not self.session:
            return {"sent": 0, "delivered": 0, "opened": 0, "clicked": 0, "bounce": 0}

        from app.models.event import Event, EventType
        from app.models.message import Message, MessageStatus

        # Count messages
        result = await self.session.execute(
            select(func.count()).where(Message.campaign_id == campaign_id)
        )
        total_messages = result.scalar_one()

        # Count sent messages
        result = await self.session.execute(
            select(func.count()).where(
                Message.campaign_id == campaign_id, Message.status == MessageStatus.SENT
            )
        )
        sent_count = result.scalar_one()

        # Count events by type
        result = await self.session.execute(
            select(Event.type, func.count())
            .where(Event.campaign_id == campaign_id)
            .group_by(Event.type)
        )
        events = result.fetchall()

        event_counts = {e[0]: e[1] for e in events}

        return {
            "total": total_messages,
            "sent": sent_count,
            "delivered": event_counts.get(EventType.DELIVERED, 0),
            "opened": event_counts.get(EventType.OPEN, 0),
            "clicked": event_counts.get(EventType.CLICK, 0),
            "bounce": event_counts.get(EventType.BOUNCE_HARD, 0)
            + event_counts.get(EventType.BOUNCE_SOFT, 0),
            "complaint": event_counts.get(EventType.COMPLAINT, 0),
            "unsubscribe": event_counts.get(EventType.UNSUBSCRIBE, 0),
        }
