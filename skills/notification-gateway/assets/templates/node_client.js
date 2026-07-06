// Drop-in Node.js client (Node 18+, native fetch) for the notification gateway.
// Config comes from the environment — no hardcoded URLs or keys:
//   NOTIFICATION_GATEWAY_URL      e.g. {{GATEWAY_URL}}
//   NOTIFICATION_GATEWAY_API_KEY  service API key ({{API_KEY}})
// Service name for logs/metrics: {{SERVICE_NAME}}. HTTP timeout: {{TIMEOUT_SECONDS}}s.

const GATEWAY_URL = process.env.NOTIFICATION_GATEWAY_URL || "{{GATEWAY_URL}}";
const API_KEY = process.env.NOTIFICATION_GATEWAY_API_KEY || "{{API_KEY}}";
const TIMEOUT_MS = {{TIMEOUT_SECONDS}} * 1000;

async function post(payload) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const resp = await fetch(`${GATEWAY_URL}/v1/notify`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    if (!resp.ok) {
      throw new Error(`gateway returned ${resp.status}: ${await resp.text()}`);
    }
    return await resp.json();
  } finally {
    clearTimeout(timer);
  }
}

const toList = (v) => (Array.isArray(v) ? v : [v]);

function sendEmail(to, templateId, templateVars = {}, opts = {}) {
  return post({ channel: "EMAIL", content_type: "TEMPLATE", to: toList(to),
    cc: opts.cc, bcc: opts.bcc, template_id: templateId, template_vars: templateVars,
    from_email: opts.fromEmail, priority: opts.priority || "NORMAL", metadata: opts.metadata });
}

function sendSMS(to, templateId, templateVars = {}, opts = {}) {
  return post({ channel: "SMS", content_type: "TEMPLATE", to, template_id: templateId,
    template_vars: templateVars, priority: opts.priority || "NORMAL", metadata: opts.metadata });
}

// content_type MUST be "OTP" (not "TEMPLATE"); phone needs a country-code prefix.
function sendOTP(to, templateId, otp, opts = {}) {
  return post({ channel: "SMS", content_type: "OTP", to, template_id: templateId,
    otp, priority: "HIGH", metadata: opts.metadata });
}

function sendWhatsApp(to, templateId, templateVars = {}, opts = {}) {
  return post({ channel: "WHATSAPP", content_type: "TEMPLATE", to, template_id: templateId,
    template_vars: templateVars, vendor_account: opts.vendorAccount,
    api_type: opts.apiType || "MESSAGE", priority: opts.priority || "NORMAL", metadata: opts.metadata });
}

module.exports = { sendEmail, sendSMS, sendOTP, sendWhatsApp };
