from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import TimestampedDTO


class SmtpAccountBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(gt=0, lt=65536)
    username: str | None = None
    use_tls: bool = True
    use_ssl: bool = False
    from_email: EmailStr
    from_name: str | None = None
    max_per_minute: int = Field(default=30, gt=0)
    max_per_hour: int = Field(default=500, gt=0)
    max_per_day: int = Field(default=2000, gt=0)
    is_default: bool = False


class SmtpAccountCreate(SmtpAccountBase):
    password: str | None = None


class SmtpAccountUpdate(BaseModel):
    name: str | None = None
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    use_tls: bool | None = None
    use_ssl: bool | None = None
    from_email: EmailStr | None = None
    from_name: str | None = None
    max_per_minute: int | None = None
    max_per_hour: int | None = None
    max_per_day: int | None = None
    is_default: bool | None = None


class SmtpAccountRead(SmtpAccountBase, TimestampedDTO):
    id: str
    has_password: bool


class SmtpTestResult(BaseModel):
    ok: bool
    error: str | None = None
