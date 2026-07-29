"""Contact service for CRM operations."""

from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.contact import Contact, ContactStatus, LifecycleStage


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
    result = await session.execute(select(Contact).where(Contact.email == email))
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
            lifecycle_stage=lifecycle_stage.value if hasattr(lifecycle_stage, "value") else (lifecycle_stage or LifecycleStage.LEAD.value),
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
            contact.lifecycle_stage = lifecycle_stage.value if hasattr(lifecycle_stage, "value") else lifecycle_stage
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


async def create_contact(
    session: AsyncSession,
    email: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone: Optional[str] = None,
    company: Optional[str] = None,
    job_title: Optional[str] = None,
    status: ContactStatus = ContactStatus.ACTIVE,
    custom_fields: Optional[Dict[str, Any]] = None,
) -> Contact:
    attributes = custom_fields or {}
    if phone:
        attributes["phone"] = phone
    if job_title:
        attributes["job_title"] = job_title

    contact = Contact(
        email=email,
        first_name=first_name,
        last_name=last_name,
        company=company,
        status=status.value if hasattr(status, "value") else status,
        attributes=attributes,
    )
    session.add(contact)
    await session.commit()
    await session.refresh(contact)
    return contact


async def list_contacts(
    session: AsyncSession,
    status: Optional[ContactStatus] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Contact]:
    """List contacts with optional status filter."""
    query = select(Contact)

    if status:
        query = query.where(Contact.status == status)

    query = query.order_by(Contact.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_contact(session: AsyncSession, contact_id: str) -> Optional[Contact]:
    """Get a contact by ID."""
    result = await session.execute(select(Contact).where(Contact.id == contact_id))
    return result.scalar_one_or_none()


async def update_contact(
    session: AsyncSession,
    contact_id: str,
    contact_data: Dict[str, Any],
) -> Optional[Contact]:
    """Update a contact."""
    result = await session.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if contact:
        # Handle special fields that belong in attributes
        attributes = contact.attributes.copy() if contact.attributes else {}
        
        if "phone" in contact_data:
            attributes["phone"] = contact_data.pop("phone")
        if "job_title" in contact_data:
            attributes["job_title"] = contact_data.pop("job_title")
        if "custom_fields" in contact_data:
            attributes.update(contact_data.pop("custom_fields") or {})
            
        contact.attributes = attributes

        for key, value in contact_data.items():
            if hasattr(contact, key) and not isinstance(getattr(type(contact), key, None), property):
                if hasattr(value, "value"):  # Handle enums
                    value = value.value
                setattr(contact, key, value)
                
        await session.commit()
        await session.refresh(contact)
    return contact


async def delete_contact(
    session: AsyncSession,
    contact_id: str,
) -> Optional[Contact]:
    """Delete a contact."""
    result = await session.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if contact:
        await session.delete(contact)
        await session.commit()
    return contact
