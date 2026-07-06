"""Sync BRMS eval client for {{SERVICE_NAME}} (requests — Django / Celery).

Config via environment — no hardcoded hosts/keys:
    BRMS_BASE_URL    e.g. {{BASE_URL}}
    BRMS_CLIENT_ID   X-Client-ID header ({{TENANT_CLIENT_ID}})
    BRMS_API_KEY     X-API-Key header ({{API_KEY}})

Targets project "{{PROJECT_SLUG}}", ruleset "{{RULESET_SLUG}}".
Sends input fields {{INPUT_FIELD_1}}, {{INPUT_FIELD_2}}; reads {{OUTPUT_FIELD_1}}, {{OUTPUT_FIELD_2}}.
"""
from __future__ import annotations

import os
import time
from typing import Any

import requests

BASE_URL = os.environ["BRMS_BASE_URL"]
CLIENT_ID = os.environ["BRMS_CLIENT_ID"]
API_KEY = os.environ["BRMS_API_KEY"]
PROJECT_SLUG = "{{PROJECT_SLUG}}"
RULESET_SLUG = "{{RULESET_SLUG}}"
TIMEOUT = (5, {{TIMEOUT_SECONDS}})  # (connect, read) — fail fast
MAX_RETRIES = {{MAX_RETRIES}}


class BRMSError(RuntimeError):
    pass


def evaluate(input_data: dict[str, Any]) -> dict[str, Any]:
    """Evaluate the ruleset; retries 429 + network errors with 1s backoff."""
    url = f"{BASE_URL}/api/v1/evaluate/ruleset/{PROJECT_SLUG}/{RULESET_SLUG}"
    headers = {
        "Content-Type": "application/json",
        "X-Client-ID": CLIENT_ID,
        "X-API-Key": API_KEY,
    }
    last_exc: Exception | None = None
    for _ in range(MAX_RETRIES + 1):
        try:
            resp = requests.post(url, json={"input_data": input_data}, headers=headers, timeout=TIMEOUT)
        except requests.RequestException as exc:
            last_exc = exc
            time.sleep(1)
            continue
        if resp.status_code == 429:
            last_exc = BRMSError("429 rate limited")
            time.sleep(1)
            continue
        if resp.status_code >= 300:
            raise BRMSError(f"BRMS eval {resp.status_code}: {resp.text}")
        return resp.json()["result"]
    raise BRMSError(f"BRMS eval failed after {MAX_RETRIES} retries: {last_exc}")
