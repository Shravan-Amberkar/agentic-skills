# Parameters

Every placeholder used in `assets/templates/` is documented here. Bijection invariant: every token in
a template file has a row below, and every row maps to a token used in at least one template file.

| Placeholder | Description | Example | Default |
|-------------|-------------|---------|---------|
| `{{BASE_URL}}` | Base URL of the BRMS deployment (no trailing slash) | `https://brms.example.com` | _(required)_ |
| `{{TENANT_CLIENT_ID}}` | Value for the `X-Client-ID` auth header | `your-org_1234` | _(required)_ |
| `{{API_KEY}}` | Value for the `X-API-Key` auth header | `brms_<tenant>_<secret>_prod` | _(required)_ |
| `{{PROJECT_SLUG}}` | Slug of the BRMS project containing the ruleset | `charge-engine` | _(required)_ |
| `{{RULESET_SLUG}}` | Slug of the ruleset to evaluate | `tenure-adjustment` | _(required)_ |
| `{{RULESET_NAME}}` | Display name for the JDM decision table | `Tenure Adjustment Rules` | _(required for JDM)_ |
| `{{SERVICE_NAME}}` | Calling service name (docstring/logging) | `lead-service` | _(required)_ |
| `{{INPUT_FIELD_1}}` | First input field sent in `input_data` | `tenure_months` | _(required)_ |
| `{{INPUT_FIELD_2}}` | Second input field (remove column if unused) | `loan_amount` | _(optional)_ |
| `{{OUTPUT_FIELD_1}}` | First output field in `result` | `effect_type` | _(required)_ |
| `{{OUTPUT_FIELD_2}}` | Second output field (remove column if unused) | `effect_value` | _(optional)_ |
| `{{TIMEOUT_SECONDS}}` | HTTP client timeout (seconds) | `5` | `5` |
| `{{MAX_RETRIES}}` | Retry attempts on 429 + network errors | `3` | `3` |
| `{{HIT_POLICY}}` | Decision table hit policy: `first` or `collect` | `first` | `first` |
| `{{NODE_ID_INPUT}}` | UUID for the JDM inputNode | `79938875-…` | `uuid()` |
| `{{NODE_ID_TABLE}}` | UUID for the JDM decisionTableNode | `5a2ae902-…` | `uuid()` |
| `{{NODE_ID_OUTPUT}}` | UUID for the JDM outputNode | `a026cee2-…` | `uuid()` |
| `{{EDGE_ID_1}}` | UUID for edge inputNode → decisionTableNode | `72bab8f8-…` | `uuid()` |
| `{{EDGE_ID_2}}` | UUID for edge decisionTableNode → outputNode | `eaf2f265-…` | `uuid()` |

> Never hardcode real URLs, keys, or tenant ids. Clients read config from the environment; these
> placeholders exist only for SETUP/INTEGRATE-mode replacement and documentation.
