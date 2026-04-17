"""Tests for cronwrap alerting module."""

import os
from unittest.mock import MagicMock, patch
import pytest

from cronwrap.alerting import AlertConfig, send_failure_alert


def _make_config(**kwargs):
    defaults = dict(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_user="user",
        smtp_password="secret",
        from_addr="alerts@example.com",
        to_addrs=["ops@example.com"],
        use_tls=True,
    )
    defaults.update(kwargs)
    return AlertConfig(**defaults)


def test_send_failure_alert_no_recipients():
    config = _make_config(to_addrs=[])
    result = send_failure_alert(config, "backup.sh", 1, "", "error", 3)
    assert result is False


def test_send_failure_alert_smtp_success():
    config = _make_config()
    mock_server = MagicMock()
    mock_smtp_cls = MagicMock(return_value=__import__('contextlib').nullcontext(mock_server))

    with patch("cronwrap.alerting.smtplib.SMTP") as mock_smtp:
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
        result = send_failure_alert(config, "my_job.sh", 2, "output", "err", 1)

    assert result is True
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("user", "secret")
    mock_server.sendmail.assert_called_once()


def test_send_failure_alert_smtp_failure():
    config = _make_config()
    import smtplib
    with patch("cronwrap.alerting.smtplib.SMTP") as mock_smtp:
        mock_smtp.return_value.__enter__ = MagicMock(side_effect=smtplib.SMTPException("fail"))
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
        result = send_failure_alert(config, "job", 1, "", "", 1)
    assert result is False


def test_alert_config_from_env():
    env = {
        "CRONWRAP_SMTP_HOST": "mail.example.com",
        "CRONWRAP_SMTP_PORT": "465",
        "CRONWRAP_SMTP_USER": "u",
        "CRONWRAP_SMTP_PASSWORD": "p",
        "CRONWRAP_ALERT_FROM": "from@example.com",
        "CRONWRAP_ALERT_TO": "a@example.com, b@example.com",
        "CRONWRAP_SMTP_TLS": "false",
    }
    with patch.dict(os.environ, env):
        cfg = AlertConfig.from_env()

    assert cfg.smtp_host == "mail.example.com"
    assert cfg.smtp_port == 465
    assert cfg.to_addrs == ["a@example.com", "b@example.com"]
    assert cfg.use_tls is False


def test_alert_config_from_env_defaults():
    with patch.dict(os.environ, {}, clear=True):
        cfg = AlertConfig.from_env()
    assert cfg.smtp_host == "localhost"
    assert cfg.to_addrs == []
    assert cfg.use_tls is True
