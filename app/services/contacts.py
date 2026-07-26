"""Contact service for CRM operations."""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.contact import Contact, LifecycleStage, ContactStatus


async def search_contacts(
    session: AsyncSession,
    stage: Optional[LifecycleStage] = None,
    status: Optional[ContactStatus] = None,
    text: Optional[str] = None,
    limit: int = 50,
) -> List[Contact]:
    """Search contacts with filters."""
    query = select(Contact)

    if stage:
        query = query.where(Contact.lifecycle_stage == stage)
    if status:
        query = query.where(Contact.status == status)
    if text:
        query = query.where(
            func.or_(
                Contact.email.ilike(f"%{text}%"),
                Contact.first_name.ilike(f"%{text}%"),
                Contact.last_name.ilike(f"%{text}%"),
                Contact.company.ilike(f"%{text}%"),
            )
        )

    query = query.order_by(Contact.created_at.desc()).limit(limit)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_contact_by_email(session: AsyncSession, email: str) -> Optional[Contact]:
    """Get a contact by email."""
    result = await session.execute(
        select(Contact).where(Contact.email == email)
    )
    return result.scalar_one_or_none()


async def upsert_contact(
    session: AsyncSession,
    email: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    company: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    lifecycle_stage: Optional[LifecycleStage] = None,
    consent_source: Optional[str] = None,
) -> Contact:
    """Upsert a contact."""
    contact = await get_contact_by_email(session, email)

    if contact is None:
        contact = Contact(
            email=email,
            first_name=first_name,
            last_name=last_name,
            company=company,
            attributes=attributes or {},
            lifecycle_stage=lifecycle_stage or LifecycleStage.LEAD,
            consent_source=consent_source,
        )
        session.add(contact)
    else:
        if first_name:
            contact.first_name = first_name
        if last_name:
            contact.last_name = last_name
        if company:
            contact.company = company
        if attributes:
            contact.attributes.update(attributes)
        if lifecycle_stage:
            contact.lifecycle_stage = lifecycle_stage
        if consent_source:
            contact.consent_source = consent_source

    await session.commit()
    return contact


async def get_contact_count(
    session: AsyncSession,
    stage: Optional[LifecycleStage] = None,
    status: Optional[ContactStatus] = None,
) -> int:
    """Get contact count with filters."""
    query = select(func.count(Contact.id))

    if stage:
        query = query.where(Contact.lifecycle_stage == stage)
    if status:
        query = query.where(Contact.status == status)

    result = await session.execute(query)
    return result.scalar_one()