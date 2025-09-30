"""Simple SMTP helper used for alerting flows."""
from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText
from typing import Iterable, Sequence


def _ensure_iterable(addresses: Iterable[str] | str) -> Sequence[str]:
    if isinstance(addresses, str):
        return [addresses]
    return list(addresses)


def send_email(to_addresses: Iterable[str] | str, subject: str, body: str) -> None:
    """Send a plain-text email using environment-driven SMTP settings."""
    server_host = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    server_port = int(os.getenv("MAIL_PORT", "587"))
    use_tls = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    username = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    sender = os.getenv("MAIL_FROM", username or "no-reply@orcaquant.local")

    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = subject
    message["From"] = sender
    recipients = _ensure_iterable(to_addresses)
    message["To"] = ", ".join(recipients)

    with smtplib.SMTP(server_host, server_port, timeout=10) as smtp:
        if use_tls:
            smtp.starttls()
        if username and password:
            smtp.login(username, password)
        smtp.sendmail(sender, recipients, message.as_string())
