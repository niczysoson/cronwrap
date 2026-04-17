"""Alerting module for cronwrap — sends notifications on job failure."""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AlertConfig:
    """Configuration for email alerting."""
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_addr: str = "cronwrap@localhost"
    to_addrs: list = field(default_factory=list)
    use_tls: bool = True

    @classmethod
    def from_env(cls) -> "AlertConfig":
        """Build AlertConfig from environment variables."""
        to_addrs_raw = os.environ.get("CRONWRAP_ALERT_TO", "")
        to_addrs = [a.strip() for a in to_addrs_raw.split(",") if a.strip()]
        return cls(
            smtp_host=os.environ.get("CRONWRAP_SMTP_HOST", "localhost"),
            smtp_port=int(os.environ.get("CRONWRAP_SMTP_PORT", "587")),
            smtp_user=os.environ.get("CRONWRAP_SMTP_USER"),
            smtp_password=os.environ.get("CRONWRAP_SMTP_PASSWORD"),
            from_addr=os.environ.get("CRONWRAP_ALERT_FROM", "cronwrap@localhost"),
            to_addrs=to_addrs,
            use_tls=os.environ.get("CRONWRAP_SMTP_TLS", "true").lower() == "true",
        )


def send_failure_alert(
    config: AlertConfig,
    command: str,
    returncode: int,
    stdout: str,
    stderr: str,
    attempts: int,
) -> bool:
    """Send an email alert for a failed cron job. Returns True if sent successfully."""
    if not config.to_addrs:
        return False

    subject = f"[cronwrap] Job failed: {command[:60]}"
    body = (
        f"Cron job failed after {attempts} attempt(s).\n\n"
        f"Command: {command}\n"
        f"Return code: {returncode}\n\n"
        f"--- stdout ---\n{stdout or '(empty)'}\n\n"
        f"--- stderr ---\n{stderr or '(empty)'}\n"
    )

    msg = MIMEMultipart()
    msg["From"] = config.from_addr
    msg["To"] = ", ".join(config.to_addrs)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
            if config.use_tls:
                server.starttls()
            if config.smtp_user and config.smtp_password:
                server.login(config.smtp_user, config.smtp_password)
            server.sendmail(config.from_addr, config.to_addrs, msg.as_string())
        return True
    except smtplib.SMTPException:
        return False
