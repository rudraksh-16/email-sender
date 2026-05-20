"""Email templates CRUD + preview render."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.models.template import Template
from app.schemas.template import (
    TemplateCreate,
    TemplatePreviewRequest,
    TemplatePreviewResult,
    TemplateRead,
    TemplateUpdate,
)
from app.services import html_sanitizer, mail_merge, text_fallback
from app.utils.errors import NotFoundError

router = APIRouter()


@router.get("", response_model=list[TemplateRead])
async def list_templates(db: AsyncSession = Depends(get_db)) -> list[TemplateRead]:
    rows = (await db.execute(select(Template).order_by(Template.name))).scalars().all()
    return [TemplateRead.model_validate(r, from_attributes=True) for r in rows]


@router.post("", response_model=TemplateRead, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: TemplateCreate, db: AsyncSession = Depends(get_db)
) -> TemplateRead:
    row = Template(**payload.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return TemplateRead.model_validate(row, from_attributes=True)


@router.get("/{template_id}", response_model=TemplateRead)
async def read_template(template_id: str, db: AsyncSession = Depends(get_db)) -> TemplateRead:
    row = await db.get(Template, template_id)
    if row is None:
        raise NotFoundError(f"Template {template_id} not found")
    return TemplateRead.model_validate(row, from_attributes=True)


@router.patch("/{template_id}", response_model=TemplateRead)
async def update_template(
    template_id: str,
    payload: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
) -> TemplateRead:
    row = await db.get(Template, template_id)
    if row is None:
        raise NotFoundError(f"Template {template_id} not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return TemplateRead.model_validate(row, from_attributes=True)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(template_id: str, db: AsyncSession = Depends(get_db)) -> None:
    row = await db.get(Template, template_id)
    if row is None:
        raise NotFoundError(f"Template {template_id} not found")
    await db.delete(row)
    await db.commit()


@router.post("/{template_id}/preview", response_model=TemplatePreviewResult)
async def preview_template(
    template_id: str,
    payload: TemplatePreviewRequest,
    db: AsyncSession = Depends(get_db),
) -> TemplatePreviewResult:
    row = await db.get(Template, template_id)
    if row is None:
        raise NotFoundError(f"Template {template_id} not found")
    subject = mail_merge.render(row.subject, payload.data)
    body_raw = mail_merge.render(row.body_html, payload.data)
    body_html = html_sanitizer.sanitize(body_raw)
    body_text = text_fallback.to_text(body_html)
    return TemplatePreviewResult(subject=subject, body_html=body_html, body_text=body_text)
