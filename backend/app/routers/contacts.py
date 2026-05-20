"""Contacts CRUD + CSV import."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.models.contact import Contact
from app.schemas.contact import (
    ContactCreate,
    ContactImportResult,
    ContactRead,
    ContactUpdate,
)
from app.schemas.common import Page
from app.services import csv_parser
from app.utils.errors import NotFoundError, ValidationError

router = APIRouter()


def _to_read(row: Contact) -> ContactRead:
    extra = json.loads(row.extra_json) if row.extra_json else {}
    return ContactRead(
        id=row.id,
        email=row.email,
        first_name=row.first_name,
        last_name=row.last_name,
        extra=extra,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("", response_model=Page[ContactRead])
async def list_contacts(
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> Page[ContactRead]:
    stmt = select(Contact)
    count_stmt = select(func.count(Contact.id))
    if q:
        like = f"%{q}%"
        cond = or_(
            Contact.email.ilike(like),
            Contact.first_name.ilike(like),
            Contact.last_name.ilike(like),
        )
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    stmt = stmt.order_by(Contact.email).limit(limit).offset(offset)
    rows = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(count_stmt)).scalar_one()
    return Page(items=[_to_read(r) for r in rows], total=total, limit=limit, offset=offset)


@router.post("", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
async def create_contact(
    payload: ContactCreate, db: AsyncSession = Depends(get_db)
) -> ContactRead:
    row = Contact(
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        extra_json=json.dumps(payload.extra) if payload.extra else None,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _to_read(row)


@router.get("/{contact_id}", response_model=ContactRead)
async def read_contact(contact_id: str, db: AsyncSession = Depends(get_db)) -> ContactRead:
    row = await db.get(Contact, contact_id)
    if row is None:
        raise NotFoundError(f"Contact {contact_id} not found")
    return _to_read(row)


@router.patch("/{contact_id}", response_model=ContactRead)
async def update_contact(
    contact_id: str,
    payload: ContactUpdate,
    db: AsyncSession = Depends(get_db),
) -> ContactRead:
    row = await db.get(Contact, contact_id)
    if row is None:
        raise NotFoundError(f"Contact {contact_id} not found")
    data = payload.model_dump(exclude_unset=True)
    if "extra" in data:
        row.extra_json = json.dumps(data.pop("extra"))
    for field, value in data.items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return _to_read(row)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(contact_id: str, db: AsyncSession = Depends(get_db)) -> None:
    row = await db.get(Contact, contact_id)
    if row is None:
        raise NotFoundError(f"Contact {contact_id} not found")
    await db.delete(row)
    await db.commit()


@router.post("/import", response_model=ContactImportResult)
async def import_contacts(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
) -> ContactImportResult:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise ValidationError("Upload a .csv file")
    raw = await file.read()
    rows = csv_parser.parse_bytes(raw)

    created = 0
    updated = 0
    skipped = 0
    errors: list[str] = []

    for row in rows:
        email = row.get("email")
        if not email:
            skipped += 1
            continue
        existing = (
            await db.execute(select(Contact).where(Contact.email == email))
        ).scalar_one_or_none()

        extra = {k: v for k, v in row.items() if k not in {"email", "first_name", "last_name"}}
        extra_json = json.dumps(extra) if extra else None

        if existing is None:
            db.add(
                Contact(
                    email=email,
                    first_name=row.get("first_name") or None,
                    last_name=row.get("last_name") or None,
                    extra_json=extra_json,
                )
            )
            created += 1
        else:
            existing.first_name = row.get("first_name") or existing.first_name
            existing.last_name = row.get("last_name") or existing.last_name
            existing.extra_json = extra_json or existing.extra_json
            updated += 1

    await db.commit()
    return ContactImportResult(created=created, updated=updated, skipped=skipped, errors=errors)
