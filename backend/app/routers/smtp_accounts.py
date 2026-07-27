"""SMTP account CRUD + connection test."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.models.smtp_account import SmtpAccount
from app.schemas.smtp_account import (
    SmtpAccountCreate,
    SmtpAccountRead,
    SmtpAccountUpdate,
    SmtpTestResult,
)
from app.services import crypto, smtp_sender
from app.utils.errors import NotFoundError, SmtpSendError

router = APIRouter()


def _to_read(row: SmtpAccount) -> SmtpAccountRead:
    return SmtpAccountRead(
        id=row.id,
        name=row.name,
        host=row.host,
        port=row.port,
        username=row.username,
        use_tls=row.use_tls,
        use_ssl=row.use_ssl,
        from_email=row.from_email,
        from_name=row.from_name,
        max_per_minute=row.max_per_minute,
        max_per_hour=row.max_per_hour,
        max_per_day=row.max_per_day,
        is_default=row.is_default,
        has_password=bool(row.password_encrypted),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def _clear_other_defaults(db: AsyncSession, except_id: str | None) -> None:
    rows = (await db.execute(select(SmtpAccount).where(SmtpAccount.is_default.is_(True)))).scalars()
    for r in rows:
        if r.id != except_id:
            r.is_default = False


@router.get("", response_model=list[SmtpAccountRead])
async def list_accounts(db: AsyncSession = Depends(get_db)) -> list[SmtpAccountRead]:
    rows = (await db.execute(select(SmtpAccount).order_by(SmtpAccount.created_at))).scalars().all()
    return [_to_read(r) for r in rows]


@router.post("", response_model=SmtpAccountRead, status_code=status.HTTP_201_CREATED)
async def create_account(
    payload: SmtpAccountCreate, db: AsyncSession = Depends(get_db)
) -> SmtpAccountRead:
    row = SmtpAccount(
        name=payload.name,
        host=payload.host,
        port=payload.port,
        username=payload.username,
        password_encrypted=crypto.encrypt(payload.password) if payload.password else None,
        use_tls=payload.use_tls,
        use_ssl=payload.use_ssl,
        from_email=payload.from_email,
        from_name=payload.from_name,
        max_per_minute=payload.max_per_minute,
        max_per_hour=payload.max_per_hour,
        is_default=payload.is_default,
    )
    db.add(row)
    if payload.is_default:
        await _clear_other_defaults(db, except_id=None)
    await db.commit()
    await db.refresh(row)
    return _to_read(row)


@router.get("/{account_id}", response_model=SmtpAccountRead)
async def read_account(account_id: str, db: AsyncSession = Depends(get_db)) -> SmtpAccountRead:
    row = await db.get(SmtpAccount, account_id)
    if row is None:
        raise NotFoundError(f"SMTP account {account_id} not found")
    return _to_read(row)


@router.patch("/{account_id}", response_model=SmtpAccountRead)
async def update_account(
    account_id: str,
    payload: SmtpAccountUpdate,
    db: AsyncSession = Depends(get_db),
) -> SmtpAccountRead:
    row = await db.get(SmtpAccount, account_id)
    if row is None:
        raise NotFoundError(f"SMTP account {account_id} not found")

    data = payload.model_dump(exclude_unset=True)
    password = data.pop("password", None)
    for field, value in data.items():
        setattr(row, field, value)
    if password is not None:
        row.password_encrypted = crypto.encrypt(password) if password else None
    if data.get("is_default"):
        await _clear_other_defaults(db, except_id=row.id)
    await db.commit()
    await db.refresh(row)
    return _to_read(row)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(account_id: str, db: AsyncSession = Depends(get_db)) -> None:
    row = await db.get(SmtpAccount, account_id)
    if row is None:
        raise NotFoundError(f"SMTP account {account_id} not found")
    await db.delete(row)
    await db.commit()


@router.post("/{account_id}/test", response_model=SmtpTestResult)
async def test_account(account_id: str, db: AsyncSession = Depends(get_db)) -> SmtpTestResult:
    row = await db.get(SmtpAccount, account_id)
    if row is None:
        raise NotFoundError(f"SMTP account {account_id} not found")
    try:
        await smtp_sender.test_connection(row)
    except SmtpSendError as exc:
        return SmtpTestResult(ok=False, error=exc.message)
    return SmtpTestResult(ok=True)
