from __future__ import annotations

from sqlalchemy import Boolean, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuid_str


class SmtpAccount(Base, TimestampMixin):
    __tablename__ = "smtp_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255))
    password_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    use_tls: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    use_ssl: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    from_email: Mapped[str] = mapped_column(String(255), nullable=False)
    from_name: Mapped[str | None] = mapped_column(String(255))
    max_per_minute: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    max_per_hour: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    max_per_day: Mapped[int] = mapped_column(Integer, default=2000, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
