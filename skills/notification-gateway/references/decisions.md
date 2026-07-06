# Architecture Decisions

Why the notification gateway is built the way it is. These trade-offs are the interview-worthy part.

### Why Kafka, not direct HTTP to vendors
The gateway accepts a request, persists it, and publishes to Kafka; per-channel consumers dispatch
to vendors. This decouples the caller from vendor latency/outages, lets each channel scale and retry
independently, and gives a durable record for replay. A direct synchronous call would couple caller
uptime to vendor uptime.

### Why per-service API keys, not a shared key
Each calling service gets its own key. This attributes every notification to a source (auditing,
rate limiting, abuse containment) and lets you revoke one service without affecting others. A shared
key makes "who sent this?" unanswerable and a leak catastrophic.

### Why vendor config lives in the DB, not env vars
Vendor accounts, credentials, and routing rules change without redeploys. Storing them in a config
table (with caching) lets ops rotate a vendor or add a WhatsApp account at runtime.

### Why separate per-channel services, not a monolith
Email, SMS, and WhatsApp have different SDKs, failure modes, and throughput. Separate consumers mean
a WhatsApp vendor outage can't stall OTP SMS, and each can be tuned (concurrency, batch size) on its own.

### Why pre-signed S3 URLs for attachments
Kafka messages have a practical size limit (~1 MB). Large attachments are uploaded to object storage
and referenced by a pre-signed URL in the payload, keeping messages small and the broker healthy.

### Why priority tiers
A single queue lets bulk traffic delay time-critical OTPs. Priority tiers (with separate
consumer concurrency) keep the OTP path fast (sub-second target) regardless of marketing volume.

### Why idempotency / dedup
At-least-once Kafka delivery means a consumer can see a message twice. A dedup key (Redis) prevents
double-sending the same notification on redelivery or retry.
