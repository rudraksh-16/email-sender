"""Attachment upload + retrieval."""
from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.models.attachment import Attachment
from app.schemas.attachment import AttachmentRead
from app.services import attachment_store
from app.utils.errors import NotFoundError, ValidationError

router = APIRouter()


@router.post("", response_model=AttachmentRead, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
) -> AttachmentRead:
    filename = file.filename or "upload.bin"
    declared_mime = file.content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    data = await file.read()
    if not data:
        raise ValidationError("Empty upload")
    stored_name, size = attachment_store.store_bytes(data, filename=filename, mime_type=declared_mime)

    row = Attachment(
        filename=filename,
        stored_name=stored_name,
        mime_type=declared_mime,
        size_bytes=size,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return AttachmentRead.model_validate(row, from_attributes=True)


@router.get("/{attachment_id}")
async def download_attachment(
    attachment_id: str, db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    row = await db.get(Attachment, attachment_id)
    if row is None:
        raise NotFoundError(f"Attachment {attachment_id} not found")
    fh = attachment_store.open_blob(row.stored_name)
    return StreamingResponse(
        fh,
        media_type=row.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{Path(row.filename).name}"'},
    )


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(attachment_id: str, db: AsyncSession = Depends(get_db)) -> None:
    row = await db.get(Attachment, attachment_id)
    if row is None:
        raise NotFoundError(f"Attachment {attachment_id} not found")
    attachment_store.delete(row.stored_name)
    await db.delete(row)
    await db.commit()
