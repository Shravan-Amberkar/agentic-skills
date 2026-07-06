# Usage Examples

All values are placeholders — no real recipients, keys, or hostnames.

### Email with template + CC + custom from
```json
{
  "channel": "EMAIL", "content_type": "TEMPLATE",
  "to": ["user@example.com"], "cc": ["ops@example.com"],
  "template_id": "welcome_v2",
  "template_vars": {"first_name": "Asha", "plan": "Pro"},
  "from_email": "noreply@example.com",
  "priority": "NORMAL",
  "metadata": {"reference_type": "signup", "reference_id": "u_123"}
}
```

### Email with attachment (pre-signed URL)
```json
{
  "channel": "EMAIL", "content_type": "TEMPLATE", "to": ["user@example.com"],
  "template_id": "invoice", "template_vars": {"amount": "1999"},
  "attachments": [{"url": "https://s3.example.com/presigned/invoice.pdf", "name": "invoice.pdf"}]
}
```

### SMS via template
```json
{"channel": "SMS", "content_type": "TEMPLATE", "to": "+910000000000",
 "template_id": "payment_reminder", "template_vars": {"due": "₹500"}}
```

### OTP (note content_type)
```json
{"channel": "SMS", "content_type": "OTP", "to": "+910000000000",
 "template_id": "otp_login", "otp": "123456", "priority": "HIGH"}
```

### WhatsApp — Message API
```json
{"channel": "WHATSAPP", "content_type": "TEMPLATE", "to": "+910000000000",
 "template_id": "order_shipped", "template_vars": {"1": "Asha", "2": "TRK123"},
 "vendor_account": "default", "api_type": "MESSAGE"}
```

### WhatsApp — Track (event-based) API
```json
{"channel": "WHATSAPP", "content_type": "TEMPLATE", "to": "+910000000000",
 "template_id": "cart_abandoned", "template_vars": {"item": "Shoes"},
 "vendor_account": "marketing", "api_type": "TRACK"}
```

### Batch send
```json
{"channel": "EMAIL", "content_type": "TEMPLATE", "to": ["a@example.com"],
 "template_id": "newsletter", "metadata": {"batch_id": "batch_2026_06"}}
```

### Python integration
```python
from notify_client import send_otp, send_email

send_otp("+910000000000", template_id="otp_login", otp="123456")
send_email("user@example.com", template_id="welcome_v2",
           template_vars={"first_name": "Asha"})
```
