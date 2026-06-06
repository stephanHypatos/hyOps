"""
Email integration — sends an onboarding email with documentation links to newly provisioned users.

Uses Python stdlib smtplib (no extra dependencies).

Credentials (set in .env):
    SMTP_HOST=smtp.example.com
    SMTP_PORT=587
    SMTP_USER=sender@example.com
    SMTP_PASSWORD=your_password
    EMAIL_FROM=hyOps <noreply@example.com>   # optional, defaults to SMTP_USER
"""

import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import integration_settings


def _check_config() -> None:
    cfg = integration_settings
    if not cfg.SMTP_HOST:
        raise RuntimeError("SMTP_HOST is not configured")
    if not cfg.SMTP_USER:
        raise RuntimeError("SMTP_USER is not configured")
    if not cfg.SMTP_PASSWORD:
        raise RuntimeError("SMTP_PASSWORD is not configured")


def _send_documentation_email_sync(
    to_email: str,
    firstname: str,
    org_name: str,
    docs: dict,
) -> dict:
    """
    Send an HTML onboarding email with documentation links.

    docs keys (all optional): internal_docu, generique_docu, add_docu
    Returns {"sent": True, "links_sent": int} on success.
    """
    _check_config()
    cfg = integration_settings
    from_addr = cfg.EMAIL_FROM or cfg.SMTP_USER

    doc_items = [
        ("Internal Documentation", docs.get("internal_docu")),
        ("General Documentation", docs.get("generique_docu")),
        ("Additional Documentation", docs.get("add_docu")),
    ]
    links = [(label, url) for label, url in doc_items if url]

    if links:
        link_html = "".join(
            f'<tr><td style="padding:8px 0;border-bottom:1px solid #e2e8f0">'
            f'<span style="color:#64748b;font-size:13px">{label}</span><br>'
            f'<a href="{url}" style="color:#6366f1;font-weight:600">{url}</a>'
            f'</td></tr>'
            for label, url in links
        )
        links_section = f'<table style="width:100%;border-collapse:collapse">{link_html}</table>'
    else:
        links_section = '<p style="color:#94a3b8">No documentation links have been configured yet.</p>'

    html = f"""<!DOCTYPE html>
<html>
<body style="font-family:sans-serif;color:#1e293b;max-width:580px;margin:auto;padding:32px 24px">
  <h2 style="color:#6366f1;margin-bottom:4px">Welcome, {firstname}!</h2>
  <p style="color:#64748b;margin-top:0">You have been onboarded to <strong style="color:#1e293b">{org_name}</strong>.</p>
  <p>Here are your documentation resources:</p>
  {links_section}
  <br>
  <p style="color:#94a3b8;font-size:12px;border-top:1px solid #e2e8f0;padding-top:16px">
    This message was sent automatically during your onboarding. Please do not reply.
  </p>
</body>
</html>"""

    plain_links = "\n".join(f"  {label}: {url}" for label, url in links) or "  (none configured)"
    plain = (
        f"Welcome, {firstname}!\n\n"
        f"You have been onboarded to {org_name}.\n\n"
        f"Documentation resources:\n{plain_links}\n\n"
        f"This message was sent automatically during your onboarding."
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Welcome to {org_name} — Your Documentation Links"
    msg["From"] = from_addr
    msg["To"] = to_email
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(cfg.SMTP_HOST, cfg.SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(cfg.SMTP_USER, cfg.SMTP_PASSWORD)
        server.sendmail(from_addr, [to_email], msg.as_string())

    return {"sent": True, "links_sent": len(links)}


# ── Async public interface ────────────────────────────────────────────────────

async def send_documentation_email(
    to_email: str,
    firstname: str,
    org_name: str,
    docs: dict,
) -> dict:
    return await asyncio.to_thread(
        _send_documentation_email_sync, to_email, firstname, org_name, docs
    )
