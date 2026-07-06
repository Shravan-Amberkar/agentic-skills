# Common Pitfalls

Real issues and their fixes. Check here before deep-debugging.

### 1. OTP not received
**Symptom:** OTP SMS never arrives; status looks "sent".
**Cause:** `content_type` was set to `TEMPLATE` instead of `OTP`, so it routed down the wrong path.
**Fix:** Use `content_type: "OTP"` and include the `otp` field. Ensure the phone has a country-code prefix.

### 2. Email template variables blank
**Symptom:** Email arrives but merge fields are empty.
**Cause:** `template_vars` keys don't match the provider template variables exactly (case-sensitive).
**Fix:** Copy the variable names from the provider template verbatim; don't rename or change case.

### 3. Large attachment fails
**Symptom:** Send fails or message is dropped when attaching a big file.
**Cause:** The attachment pushed the Kafka message over the ~1 MB limit.
**Fix:** Upload to object storage and pass a pre-signed URL instead of inlining the bytes.

### 4. Wrong "source" in logs
**Symptom:** Notifications show up attributed to the wrong service.
**Cause:** A shared or copied API key — source is derived from the key.
**Fix:** Use this service's own `NOTIFICATION_GATEWAY_API_KEY`; never reuse another service's key.

### 5. WhatsApp 401 invalid token
**Symptom:** WhatsApp sends return 401.
**Cause:** Wrong/expired vendor token, often a base64 key copy-paste typo in vendor config.
**Fix:** Re-check the vendor config row; re-copy the key carefully; confirm the account is active.

### 6. Duplicate notifications
**Symptom:** Recipient gets the same message twice.
**Cause:** Kafka at-least-once redelivery without a dedup guard, or a client retry after a timeout
that actually succeeded.
**Fix:** Send a stable `metadata.reference_id`/dedup key so the gateway can ignore duplicates; make
client retries idempotent.

### 7. "FAILED" but actually delivered (WhatsApp)
**Symptom:** Status shows FAILED though the user received the message.
**Cause:** Vendor response parsing treated a boolean `result` as a string.
**Fix:** Parse the vendor's success field by its real type; reconcile status from the delivery webhook.
