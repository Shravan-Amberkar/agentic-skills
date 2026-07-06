# Template Parameters

Every placeholder used in `assets/templates/` is documented here, and every row below appears in
all three client templates (`python_client.py`, `go_client.go`, `node_client.js`). Replace these
during SETUP mode.

| Placeholder | Description | Source |
|-------------|-------------|--------|
| `{{GATEWAY_URL}}` | Notification gateway base URL | `NOTIFICATION_GATEWAY_URL` env var |
| `{{API_KEY}}` | Per-service API key | `NOTIFICATION_GATEWAY_API_KEY` env var |
| `{{SERVICE_NAME}}` | Calling service name (must match the API key's owner) | User provides during setup |
| `{{TIMEOUT_SECONDS}}` | HTTP read timeout in seconds | Default: 10 |

> Never hardcode real URLs, keys, phone numbers, or emails. The clients read config from the
> environment; the placeholders exist only as documented fallbacks for SETUP-mode replacement.
