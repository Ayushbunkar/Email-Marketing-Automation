from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db import get_session
from app.models.reply import Reply, ReplyStatus
from app.schemas.reply import ReplyRead, ReplyUpdate, ReplyCreate
from app.services.replies import list_replies, get_reply, create_reply, update_reply, delete_reply

router = APIRouter(prefix="/replies", tags=["replies"])

@router.post("/", response_model=ReplyRead)
async def create_new_reply(
    reply: ReplyCreate,
    session: AsyncSession = Depends(get_session)
):
    return await create_reply(session, reply)

@router.get("/", response_model=List[ReplyRead])
async def read_replies(
    status: Optional[ReplyStatus] = None,
    session: AsyncSession = Depends(get_session)
):
    return await list_replies(session, status)

@router.get("/{reply_id}", response_model=ReplyRead)
async def read_reply(
    reply_id: str,
    session: AsyncSession = Depends(get_session)
):
    reply = await get_reply(session, reply_id)
    if not reply:
        raise HTTPException(status_code=404, detail="Reply not found")
    return reply

@router.put("/{reply_id}", response_model=ReplyRead)
async def update_existing_reply(
    reply_id: str,
    reply: ReplyUpdate,
    session: AsyncSession = Depends(get_session)
):
    updated_reply = await update_reply(session, reply_id, reply)
    if not updated_reply:
        raise HTTPException(status_code=404, detail="Reply not found")
    return updated_reply

@router.delete("/{reply_id}", response_model=ReplyRead)
async def delete_existing_reply(
    reply_id: str,
    session: AsyncSession = Depends(get_session)
):
    deleted_reply = await delete_reply(session, reply_id)
    if not deleted_reply:
        raise HTTPException(status_code=404, detail="Reply not found")
    return deleted_reply