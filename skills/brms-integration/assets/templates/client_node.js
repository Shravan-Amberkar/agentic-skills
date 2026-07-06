// BRMS eval client for {{SERVICE_NAME}} (axios — Node.js).
// Config via environment — no hardcoded hosts/keys:
//   BRMS_BASE_URL    e.g. {{BASE_URL}}
//   BRMS_CLIENT_ID   X-Client-ID header ({{TENANT_CLIENT_ID}})
//   BRMS_API_KEY     X-API-Key header ({{API_KEY}})
// Targets project "{{PROJECT_SLUG}}", ruleset "{{RULESET_SLUG}}".
// Sends input fields {{INPUT_FIELD_1}}, {{INPUT_FIELD_2}}; reads {{OUTPUT_FIELD_1}}, {{OUTPUT_FIELD_2}}.

const axios = require("axios");

const BASE_URL = process.env.BRMS_BASE_URL;
const CLIENT_ID = process.env.BRMS_CLIENT_ID;
const API_KEY = process.env.BRMS_API_KEY;
const PROJECT_SLUG = "{{PROJECT_SLUG}}";
const RULESET_SLUG = "{{RULESET_SLUG}}";
const TIMEOUT_MS = {{TIMEOUT_SECONDS}} * 1000;
const MAX_RETRIES = {{MAX_RETRIES}};

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Evaluate the ruleset; retries 429 + network errors with 1s backoff.
async function evaluate(inputData) {
  const url = `${BASE_URL}/api/v1/evaluate/ruleset/${PROJECT_SLUG}/${RULESET_SLUG}`;
  const headers = {
    "Content-Type": "application/json",
    "X-Client-ID": CLIENT_ID, // case preserved — do not lowercase
    "X-API-Key": API_KEY,
  };
  let lastErr;
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const resp = await axios.post(url, { input_data: inputData }, { headers, timeout: TIMEOUT_MS });
      return resp.data.result;
    } catch (err) {
      const status = err.response && err.response.status;
      if (status && status !== 429 && status >= 300) {
        throw new Error(`BRMS eval ${status}: ${JSON.stringify(err.response.data)}`);
      }
      lastErr = err; // 429 or network → retry
      await sleep(1000);
    }
  }
  throw new Error(`BRMS eval failed after ${MAX_RETRIES} retries: ${lastErr}`);
}

module.exports = { evaluate };
