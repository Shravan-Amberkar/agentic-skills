# Common Pitfalls

Real production gotchas with reproduction and fixes.

### 1. Auth headers not forwarded
**Symptom:** 401/403 even with correct credentials, or headers missing server-side.
**Cause:** An HTTP client or proxy lowercases/strips custom headers, or a service wrapper drops
non-standard headers. `X-Client-ID` and `X-API-Key` must arrive intact.
**Fix:** Set headers explicitly on the request (as the templates do); if behind a wrapper/gateway,
allowlist these headers. Verify with a direct curl first.

### 2. Cannot edit JDM on an active ruleset
**Symptom:** `400 "Cannot edit ... on active ruleset"` when PATCHing `jdm_content`.
**Cause:** Content fields can't be changed while status is `active`.
**Fix:** Include `"status": "draft"` in the same PATCH payload as the content change, then re-activate.

### 3. Ruleset not active
**Symptom:** `400 "Ruleset is not active"` on evaluate.
**Cause:** Ruleset is still `draft`/`inactive`.
**Fix:** PATCH `{"status": "active"}` before evaluating.

### 4. input_data not wrapped
**Symptom:** `400 "input_data is required"`.
**Cause:** Sending the fields at the top level instead of under `input_data`.
**Fix:** Always wrap: `{"input_data": {"tenure_months": 12, ...}}`.

### 5. Service-wrapper path params
**Symptom:** 404 even though the ruleset exists.
**Cause:** A generic service wrapper builds the URL from a `path_params` dict and the project/ruleset
slugs weren't passed, so the path is malformed.
**Fix:** Pass `path_params={"project_slug": ..., "ruleset_slug": ...}` (or use the dedicated client),
and confirm the final URL matches `/api/v1/evaluate/ruleset/{project}/{ruleset}`.

### 6. Rate limited
**Symptom:** `429 "Rate limit exceeded"` under load.
**Cause:** Exceeding the ruleset's `evaluation_rate_limit_per_sec`.
**Fix:** Back off ~1s and retry (clients do this); enable ruleset caching for hot, stable rules; or
ask the BRMS team to raise the limit.
