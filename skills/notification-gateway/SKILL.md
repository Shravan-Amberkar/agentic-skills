---
name: notification-gateway
description: Use to integrate, migrate to, troubleshoot, or check the status of a multi-channel notification gateway (email, SMS, WhatsApp, OTP) without asking the platform team for sample payloads. Five modes auto-detected from the request — SEND (build a ready-to-use curl + code + JSON payload), SETUP (drop a typed client into the project and wire env vars), MIGRATE (convert existing SendGrid/MSG91/Interakt vendor code to the gateway), TROUBLESHOOT (channel-specific failure checklists with the DB/log queries to run), and STATUS (look up delivery by notification id, reference, or batch). Trigger on "send email/SMS/WhatsApp/OTP", "integrate notifications", "migrate sendgrid/msg91/interakt", "notification failed / not received", or "check delivery status".
license: MIT
x-spec-version: "1.0"
---

# notification-gateway

Integrate with an event-driven, multi-channel notification gateway in one guided flow. The gateway
exposes a single HTTP API; messages are queued to Kafka and dispatched by per-channel vendor
services (email, SMS, WhatsApp), with delivery tracked per notification.

> Generic, vendor-neutral skill. Configure your own gateway URL and API key via environment
> variables — no hardcoded hosts, keys, or recipients anywhere.

## When to use
- "Send an email / SMS / WhatsApp / OTP"
- "Integrate / set up the notification gateway in this service"
- "Migrate our SendGrid / MSG91 / Interakt code to the gateway"
- "A notification failed / wasn't received — why?"
- "Check the delivery status of a notification or batch"

## Modes (auto-detect, can be chained)

### Mode 1 — SEND (interactive payload builder)
Gather: **channel** (EMAIL/SMS/WHATSAPP) → **content type** (TEMPLATE / RAW / OTP) → recipient →
channel options (email: CC/BCC, from, attachments; WhatsApp: vendor account, Message vs Track API) →
metadata (`reference_type`, `reference_id`, `batch_id`) → **priority**. Skip anything the user gave.
Then output **all three**: a ready curl, a code snippet in the project's language (using the client
template), and the raw JSON payload.

### Mode 2 — SETUP (drop-in client)
Detect language (`go.mod`→Go, `requirements.txt`/`pyproject.toml`→Python, `package.json`→Node),
copy the matching template from `assets/templates/`, replace `{{PLACEHOLDERS}}`, add env vars to
`.env.example`, and show a usage example.

### Mode 3 — MIGRATE (convert vendor code)
User pastes existing vendor SDK code; identify the vendor, map fields to the gateway payload, emit
replacement code, and explain the changes. Key mappings:
- **SendGrid**: `dynamic_template_data` → `template_vars`; keep `template_id`.
- **MSG91 Flow**: `flow_id` → `template_id`; `variables` → `template_vars`.
- **MSG91 OTP**: must use `content_type: "OTP"` (not `TEMPLATE`).
- **Interakt Message**: template name → `template_id`; `bodyValues` → ordered `template_vars` ("1","2",…).
- **Interakt Track**: event name → `template_id`; traits → `template_vars`; set `vendor_account`.

### Mode 4 — TROUBLESHOOT (channel checklists)
Give the most likely cause + the exact DB/log query to confirm + the fix. Highlights:
- **Email**: `template_vars` must match the provider template keys exactly (case-sensitive);
  attachment > 1 MB → use a pre-signed S3 URL, not inline.
- **SMS/OTP**: OTP must use `content_type: "OTP"`; phone needs country-code prefix.
- **WhatsApp**: `401 invalid token` → check vendor config (watch base64 key typos); Track vs Message
  → check `vendor_account` + `api_type`; "FAILED but delivered" → vendor response parsing (bool vs string).
- **General**: check `status_reason` in delivery tracking, `notification_logs` by `notification_id`,
  confirm the API key is active and routing rules exist for the channel + priority.

### Mode 5 — STATUS (delivery lookup)
By `notification_id` or `reference_type`+`reference_id` → query `notification_logs`; by `batch_id` →
`GET /v1/notify/batch/{batch_id}/summary`; channel-specific → `notification_{channel}_delivery_tracking`.

## Priority guide
Use the highest priority only for time-critical, user-blocking messages (OTP, security). Default
transactional messages to normal; bulk/marketing to low.

## Files
- `assets/templates/{python_client.py,go_client.go,node_client.js}` — drop-in clients (env-driven).
- `PARAMETERS.md` — every template placeholder and its source.
- `references/{decisions.md,pitfalls.md,usage-example.md}` — rationale, real fixes, payload examples.

See `references/pitfalls.md` before debugging and `references/decisions.md` for the architecture rationale.
