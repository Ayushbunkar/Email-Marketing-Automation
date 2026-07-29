from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db import get_session
from app.models.setting import Setting
from app.schemas.setting import SettingRead, SettingUpdate
from app.services.settings import get_settings, update_setting

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("/", response_model=List[SettingRead])
async def read_settings(
    session: AsyncSession = Depends(get_session)
):
    return await get_settings(session)

@router.put("/{setting_id}", response_model=SettingRead)
async def update_existing_setting(
    setting_id: str,
    setting: SettingUpdate,
    session: AsyncSession = Depends(get_session)
):
    updated_setting = await update_setting(session, setting_id, setting)
    if not updated_setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return updated_setting