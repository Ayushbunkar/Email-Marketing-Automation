from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db import get_session
from app.models.inbox import InboxMessage
from app.schemas.inbox import InboxMessageRead, InboxMessageUpdate
from app.services.inbox import list_messages, get_message, update_message_status, delete_message

router = APIRouter(prefix="/inbox", tags=["inbox"])

@router.get("/", response_model=List[InboxMessageRead])
async def read_messages(
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    return await list_messages(session, status)

@router.get("/{message_id}", response_model=InboxMessageRead)
async def read_message(
    message_id: str,
    session: AsyncSession = Depends(get_session)
):
    message = await get_message(session, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message

@router.put("/{message_id}/status", response_model=InboxMessageRead)
async def update_message_status_endpoint(
    message_id: str,
    status: str,
    session: AsyncSession = Depends(get_session)
):
    updated_message = await update_message_status(session, message_id, status)
    if not updated_message:
        raise HTTPException(status_code=404, detail="Message not found")
    return updated_message

@router.delete("/{message_id}", response_model=InboxMessageRead)
async def delete_message_endpoint(
    message_id: str,
    session: AsyncSession = Depends(get_session)
):
    deleted_message = await delete_message(session, message_id)
    if not deleted_message:
        raise HTTPException(status_code=404, detail="Message not found")
    return deleted_message