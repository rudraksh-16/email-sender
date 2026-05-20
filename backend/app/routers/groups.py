"""Contact groups CRUD + membership management."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.deps import get_db
from app.models.contact import Contact, ContactGroup, contact_group_members
from app.routers.contacts import _to_read as contact_to_read
from app.schemas.group import (
    ContactGroupCreate,
    ContactGroupDetail,
    ContactGroupRead,
    ContactGroupUpdate,
)
from app.utils.errors import NotFoundError

router = APIRouter()


async def _count(db: AsyncSession, group_id: str) -> int:
    return (
        await db.execute(
            select(func.count(contact_group_members.c.contact_id)).where(
                contact_group_members.c.group_id == group_id
            )
        )
    ).scalar_one()


@router.get("", response_model=list[ContactGroupRead])
async def list_groups(db: AsyncSession = Depends(get_db)) -> list[ContactGroupRead]:
    rows = (await db.execute(select(ContactGroup).order_by(ContactGroup.name))).scalars().all()
    out: list[ContactGroupRead] = []
    for r in rows:
        out.append(
            ContactGroupRead(
                id=r.id,
                name=r.name,
                description=r.description,
                contact_count=await _count(db, r.id),
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
        )
    return out


@router.post("", response_model=ContactGroupRead, status_code=status.HTTP_201_CREATED)
async def create_group(
    payload: ContactGroupCreate, db: AsyncSession = Depends(get_db)
) -> ContactGroupRead:
    row = ContactGroup(name=payload.name, description=payload.description)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return ContactGroupRead(
        id=row.id,
        name=row.name,
        description=row.description,
        contact_count=0,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("/{group_id}", response_model=ContactGroupDetail)
async def read_group(group_id: str, db: AsyncSession = Depends(get_db)) -> ContactGroupDetail:
    row = (
        await db.execute(
            select(ContactGroup)
            .options(selectinload(ContactGroup.contacts))
            .where(ContactGroup.id == group_id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise NotFoundError(f"Group {group_id} not found")
    return ContactGroupDetail(
        id=row.id,
        name=row.name,
        description=row.description,
        contact_count=len(row.contacts),
        contacts=[contact_to_read(c) for c in row.contacts],
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.patch("/{group_id}", response_model=ContactGroupRead)
async def update_group(
    group_id: str,
    payload: ContactGroupUpdate,
    db: AsyncSession = Depends(get_db),
) -> ContactGroupRead:
    row = await db.get(ContactGroup, group_id)
    if row is None:
        raise NotFoundError(f"Group {group_id} not found")
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return ContactGroupRead(
        id=row.id,
        name=row.name,
        description=row.description,
        contact_count=await _count(db, row.id),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(group_id: str, db: AsyncSession = Depends(get_db)) -> None:
    row = await db.get(ContactGroup, group_id)
    if row is None:
        raise NotFoundError(f"Group {group_id} not found")
    await db.delete(row)
    await db.commit()


@router.post("/{group_id}/members/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_member(
    group_id: str, contact_id: str, db: AsyncSession = Depends(get_db)
) -> None:
    group = (
        await db.execute(
            select(ContactGroup)
            .options(selectinload(ContactGroup.contacts))
            .where(ContactGroup.id == group_id)
        )
    ).scalar_one_or_none()
    if group is None:
        raise NotFoundError(f"Group {group_id} not found")
    contact = await db.get(Contact, contact_id)
    if contact is None:
        raise NotFoundError(f"Contact {contact_id} not found")
    if contact not in group.contacts:
        group.contacts.append(contact)
        await db.commit()


@router.delete("/{group_id}/members/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: str, contact_id: str, db: AsyncSession = Depends(get_db)
) -> None:
    group = (
        await db.execute(
            select(ContactGroup)
            .options(selectinload(ContactGroup.contacts))
            .where(ContactGroup.id == group_id)
        )
    ).scalar_one_or_none()
    if group is None:
        raise NotFoundError(f"Group {group_id} not found")
    contact = await db.get(Contact, contact_id)
    if contact and contact in group.contacts:
        group.contacts.remove(contact)
        await db.commit()
