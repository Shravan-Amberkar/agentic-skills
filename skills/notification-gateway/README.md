# notification-gateway (Agent Skill)

Integrate, migrate to, troubleshoot, and check the status of a multi-channel notification gateway
(email · SMS · WhatsApp · OTP) — without hunting for sample payloads. Vendor-neutral and
environment-driven; works with any gateway that exposes the documented API.

## Install
```bash
npx skills add Shravan-Amberkar/notification-gateway
# or copy this directory into your project's .claude/skills/
```

## The 5 modes
| Mode | Say something like | What you get |
|---|---|---|
| **SEND** | "send an OTP / email / WhatsApp" | curl + code snippet + raw JSON payload |
| **SETUP** | "integrate the notification gateway" | typed client dropped in, env vars wired |
| **MIGRATE** | "migrate our SendGrid/MSG91/Interakt code" | replacement code + what changed |
| **TROUBLESHOOT** | "the notification failed / wasn't received" | likely cause + DB/log query + fix |
| **STATUS** | "check delivery status / batch summary" | the right lookup by id / reference / batch |

## Channels & content types
| Channel | Content types |
|---|---|
| EMAIL | TEMPLATE, RAW (subject + html_body) |
| SMS | TEMPLATE, **OTP** |
| WHATSAPP | TEMPLATE (Message or Track API) |

## Environment variables
| Var | Purpose |
|---|---|
| `NOTIFICATION_GATEWAY_URL` | Gateway base URL |
| `NOTIFICATION_GATEWAY_API_KEY` | Per-service API key |

## Architecture (at a glance)
```
caller --HTTP--> [gateway] --persist--> DB
                     |
                     +--publish--> Kafka --> [email consumer]   --> email vendor
                                         --> [sms consumer]     --> SMS vendor
                                         --> [whatsapp consumer]--> WhatsApp vendor
                                         delivery tracked per notification_id
```

## Top 3 pitfalls
1. **OTP not received** → `content_type` must be `OTP`, not `TEMPLATE`.
2. **Blank email variables** → `template_vars` keys must match the provider template exactly (case-sensitive).
3. **Large attachment fails** → use a pre-signed S3 URL (Kafka ~1 MB message limit).

See [`references/pitfalls.md`](references/pitfalls.md), [`references/decisions.md`](references/decisions.md),
and [`references/usage-example.md`](references/usage-example.md). Template placeholders are documented in
[`PARAMETERS.md`](PARAMETERS.md).

## License
MIT © Shravan Amberkar
