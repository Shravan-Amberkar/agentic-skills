"""Drop-in Python client for the notification gateway.

Config comes from the environment — no hardcoded URLs or keys:
    NOTIFICATION_GATEWAY_URL      e.g. {{GATEWAY_URL}}
    NOTIFICATION_GATEWAY_API_KEY  service API key ({{API_KEY}})

Service name for logs/metrics: {{SERVICE_NAME}}. HTTP timeout: {{TIMEOUT_SECONDS}}s.
"""
from __future__ import annotations

import os
from typing import Any

import requests

GATEWAY_URL = os.environ.get("NOTIFICATION_GATEWAY_URL", "{{GATEWAY_URL}}")
API_KEY = os.environ.get("NOTIFICATION_GATEWAY_API_KEY", "{{API_KEY}}")
TIMEOUT = (5, {{TIMEOUT_SECONDS}})  # (connect, read) — fail fast, never hang


class NotificationError(RuntimeError):
    pass


def _post(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        resp = requests.post(
            f"{GATEWAY_URL}/v1/notify",
            json=payload,
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:  # network / timeout
        raise NotificationError(f"gateway request failed: {exc}") from exc
    if resp.status_code >= 300:
        raise NotificationError(f"gateway returned {resp.status_code}: {resp.text}")
    return resp.json()


def send_email(to, template_id=None, template_vars=None, *, cc=None, bcc=None,
               from_email=None, priority="NORMAL", metadata=None) -> dict[str, Any]:
    return _post({
        "channel": "EMAIL", "content_type": "TEMPLATE",
        "to": to if isinstance(to, list) else [to],
        "cc": cc, "bcc": bcc, "template_id": template_id,
        "template_vars": template_vars or {}, "from_email": from_email,
        "priority": priority, "metadata": metadata,
    })


def send_email_raw(to, subject, html_body, *, priority="NORMAL", metadata=None) -> dict[str, Any]:
    return _post({
        "channel": "EMAIL", "content_type": "RAW",
        "to": to if isinstance(to, list) else [to],
        "subject": subject, "html_body": html_body,
        "priority": priority, "metadata": metadata,
    })


def send_sms(to, template_id, template_vars=None, *, priority="NORMAL", metadata=None) -> dict[str, Any]:
    return _post({
        "channel": "SMS", "content_type": "TEMPLATE", "to": to,
        "template_id": template_id, "template_vars": template_vars or {},
        "priority": priority, "metadata": metadata,
    })


def send_otp(to, template_id, otp, *, metadata=None) -> dict[str, Any]:
    # content_type MUST be "OTP" (not "TEMPLATE"); phone needs a country-code prefix.
    return _post({
        "channel": "SMS", "content_type": "OTP", "to": to,
        "template_id": template_id, "otp": otp,
        "priority": "HIGH", "metadata": metadata,
    })


def send_whatsapp(to, template_id, template_vars=None, *, vendor_account=None,
                  api_type="MESSAGE", priority="NORMAL", metadata=None) -> dict[str, Any]:
    return _post({
        "channel": "WHATSAPP", "content_type": "TEMPLATE", "to": to,
        "template_id": template_id, "template_vars": template_vars or {},
        "vendor_account": vendor_account, "api_type": api_type,
        "priority": priority, "metadata": metadata,
    })
