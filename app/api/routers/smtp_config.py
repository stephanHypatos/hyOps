"""
SMTP configuration endpoints — singleton row (id=1).
GET  /smtp-config/        → return current config (password masked)
PUT  /smtp-config/        → upsert full config
POST /smtp-config/test    → send a test email to a given address
"""

import smtplib
import asyncio
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from app.database.models import SmtpConfig
from app.database.session import SessionDep

router = APIRouter(prefix="/smtp-config", tags=["SMTP Config"])

_MASK = "••••••••"


# ── Schemas ───────────────────────────────────────────────────────────────────

class SmtpConfigRead(BaseModel):
    host: Optional[str] = None
    port: int = 587
    username: Optional[str] = None
    password_set: bool = False          # never expose the actual password
    from_name: Optional[str] = None
    from_email: Optional[str] = None
    use_tls: bool = True
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SmtpConfigUpdate(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None      # only updated when explicitly provided
    from_name: Optional[str] = None
    from_email: Optional[str] = None
    use_tls: Optional[bool] = None


class SmtpTestRequest(BaseModel):
    to_email: str


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_or_create(session: SessionDep) -> SmtpConfig:
    cfg = await session.get(SmtpConfig, 1)
    if cfg is None:
        cfg = SmtpConfig(id=1)
        session.add(cfg)
        await session.commit()
        await session.refresh(cfg)
    return cfg


def _to_read(cfg: SmtpConfig) -> SmtpConfigRead:
    return SmtpConfigRead(
        host=cfg.host,
        port=cfg.port,
        username=cfg.username,
        password_set=bool(cfg.password),
        from_name=cfg.from_name,
        from_email=cfg.from_email,
        use_tls=cfg.use_tls,
        updated_at=cfg.updated_at,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/", response_model=SmtpConfigRead)
async def get_smtp_config(session: SessionDep):
    cfg = await _get_or_create(session)
    return _to_read(cfg)


@router.put("/", response_model=SmtpConfigRead)
async def upsert_smtp_config(data: SmtpConfigUpdate, session: SessionDep):
    cfg = await _get_or_create(session)
    update = data.model_dump(exclude_none=True)
    update["updated_at"] = datetime.utcnow()
    cfg.sqlmodel_update(update)
    session.add(cfg)
    await session.commit()
    await session.refresh(cfg)
    return _to_read(cfg)


@router.post("/test")
async def test_smtp(req: SmtpTestRequest, session: SessionDep):
    """Send a test email to verify the SMTP configuration."""
    cfg = await _get_or_create(session)

    if not cfg.host:
        raise HTTPException(status_code=400, detail="SMTP host is not configured.")
    if not cfg.username:
        raise HTTPException(status_code=400, detail="SMTP username is not configured.")
    if not cfg.password:
        raise HTTPException(status_code=400, detail="SMTP password is not configured.")

    from_addr = (
        f"{cfg.from_name} <{cfg.from_email}>"
        if cfg.from_name and cfg.from_email
        else cfg.from_email or cfg.username
    )

    def _send():
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "hyOps — SMTP Test Email"
        msg["From"] = from_addr
        msg["To"] = req.to_email
        msg.attach(MIMEText(
            "This is a test email sent from hyOps to verify your SMTP configuration.",
            "plain"
        ))
        msg.attach(MIMEText(
            "<p>This is a <strong>test email</strong> sent from <strong>hyOps</strong> "
            "to verify your SMTP configuration.</p>",
            "html"
        ))
        with smtplib.SMTP(cfg.host, cfg.port) as server:
            server.ehlo()
            if cfg.use_tls:
                server.starttls()
            server.login(cfg.username, cfg.password)
            server.sendmail(from_addr, [req.to_email], msg.as_string())

    try:
        await asyncio.to_thread(_send)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"SMTP error: {str(e)}")

    return {"sent": True, "to": req.to_email}
