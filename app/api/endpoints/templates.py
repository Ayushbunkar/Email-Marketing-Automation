from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db import get_session
from app.models.template import Template, TemplateStatus
from app.schemas.template import TemplateCreate, TemplateRead, TemplateUpdate
from app.services.templates import create_template, list_templates, get_template, update_template, delete_template

router = APIRouter(prefix="/templates", tags=["templates"])

@router.post("/", response_model=TemplateRead)
async def create_new_template(
    template: TemplateCreate,
    session: AsyncSession = Depends(get_session)
):
    return await create_template(session, **template.model_dump())

@router.get("/", response_model=List[TemplateRead])
async def read_templates(
    status: Optional[TemplateStatus] = None,
    session: AsyncSession = Depends(get_session)
):
    return await list_templates(session, status)

@router.get("/{template_id}", response_model=TemplateRead)
async def read_template(
    template_id: str,
    session: AsyncSession = Depends(get_session)
):
    template = await get_template(session, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.put("/{template_id}", response_model=TemplateRead)
async def update_existing_template(
    template_id: str,
    template: TemplateUpdate,
    session: AsyncSession = Depends(get_session)
):
    updated_template = await update_template(session, template_id, template)
    if not updated_template:
        raise HTTPException(status_code=404, detail="Template not found")
    return updated_template

@router.delete("/{template_id}", response_model=TemplateRead)
async def delete_existing_template(
    template_id: str,
    session: AsyncSession = Depends(get_session)
):
    deleted_template = await delete_template(session, template_id)
    if not deleted_template:
        raise HTTPException(status_code=404, detail="Template not found")
    return deleted_template