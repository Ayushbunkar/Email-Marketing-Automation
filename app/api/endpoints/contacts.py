from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from app.db import get_session
from app.models.contact import Contact, ContactStatus, LifecycleStage
from app.schemas.contact import ContactCreate, ContactRead, ContactUpdate
from app.services.contacts import create_contact, list_contacts, get_contact, update_contact, delete_contact

router = APIRouter(prefix="/contacts", tags=["contacts"])

@router.post("/", response_model=ContactRead)
async def create_new_contact(
    contact: ContactCreate,
    session: AsyncSession = Depends(get_session)
):
    try:
        return await create_contact(
            session=session,
            email=contact.email,
            first_name=contact.first_name,
            last_name=contact.last_name,
            phone=contact.phone,
            company=contact.company,
            job_title=contact.job_title,
            status=contact.status,
            custom_fields=contact.custom_fields,
        )
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Contact with this email already exists")

@router.get("/", response_model=List[ContactRead])
async def read_contacts(
    stage: Optional[LifecycleStage] = None,
    status: Optional[ContactStatus] = None,
    text: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    return await list_contacts(session, stage, status, text)

@router.get("/{contact_id}", response_model=ContactRead)
async def read_contact(
    contact_id: str,
    session: AsyncSession = Depends(get_session)
):
    contact = await get_contact(session, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.put("/{contact_id}", response_model=ContactRead)
async def update_existing_contact(
    contact_id: str,
    contact: ContactUpdate,
    session: AsyncSession = Depends(get_session)
):
    updated_contact = await update_contact(session, contact_id, contact.model_dump(exclude_unset=True))
    if not updated_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return updated_contact

@router.delete("/{contact_id}", response_model=ContactRead)
async def delete_existing_contact(
    contact_id: str,
    session: AsyncSession = Depends(get_session)
):
    deleted_contact = await delete_contact(session, contact_id)
    if not deleted_contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return deleted_contact