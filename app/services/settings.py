"""Settings service layer."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.setting import Setting
from app.schemas.setting import SettingUpdate


async def get_settings(session: AsyncSession) -> List[Setting]:
    """Get all settings."""
    result = await session.execute(select(Setting))
    return list(result.scalars().all())


async def get_setting_by_key(session: AsyncSession, key: str) -> Optional[Setting]:
    """Get a setting by key."""
    result = await session.execute(select(Setting).where(Setting.key == key))
    return result.scalars().first()


async def update_setting(
    session: AsyncSession, setting_id: str, setting_data: SettingUpdate
) -> Optional[Setting]:
    """Update a setting."""
    result = await session.execute(
        select(Setting).where(Setting.id == setting_id)
    )
    setting = result.scalars().first()
    if not setting:
        return None

    update_data = setting_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(setting, key, value)

    await session.commit()
    await session.refresh(setting)
    return setting
