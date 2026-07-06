---
name: kafka-consumer-builder
description: Use when building a Kafka (or Redpanda) consumer or producer and you want it to be production-safe rather than a naive read loop. Generates an idempotent consumer with explicit offset management, a dedicated consumer group id per service, at-least-once processing with deduplication, bounded retries with backoff, a dead-letter topic (DLQ) for poison messages, graceful rebalance handling, and structured logging/metrics. Also generates idempotent producers with keys for partition affinity. Trigger when the user asks to write/scaffold a Kafka consumer or producer, fix consumer rebalance loops or duplicate processing, or add a DLQ/retry strategy to an existing consumer.
license: MIT
---

# Kafka Consumer Builder

Build Kafka consumers and producers that survive production: rebalances, redeliveries, poison
messages, and restarts. Defaults assume **at-least-once** delivery, so consumers MUST be idempotent.

## When to use
- "Write/scaffold a Kafka consumer or producer"
- "I'm getting duplicate processing / a consumer rebalance loop"
- "Add retries / a dead-letter queue to my consumer"

## Hard rules (apply unless told otherwise)

1. **Unique consumer group id per logical service.** Sharing a group id across different services
   or unrelated deployments causes endless rebalance loops and stolen partitions — the single most
   common Kafka incident. Name it `<service>-<purpose>`.
2. **Idempotent processing.** Derive an idempotency key from the message (e.g. an event id or a
   business key). Check a dedupe store (DB unique constraint or Redis SETNX) before side effects.
3. **Manual offset commits after successful processing**, not auto-commit. Commit only once the
   work (and any DB write) is durable. Prefer committing in batches for throughput.
4. **Bounded retries + DLQ.** Retry transient failures with exponential backoff and a max attempt
   count; after that, publish to `<topic>.dlq` with the error and original headers, then commit so
   the partition is not blocked by one poison message.
5. **Graceful shutdown / rebalance.** Stop polling on shutdown, finish the in-flight batch, commit,
   then leave the group cleanly.
6. **Observability.** Emit metrics for lag, processed, retried, dead-lettered; log with the message
   key, partition, offset, and a request/correlation id.

## Producer guidance
- Set a partition **key** so related events land on the same partition (ordering per key).
- Use idempotent producer settings (`enable.idempotence=true`, acks=all) to avoid duplicates on retry.
- Include headers: event id, schema version, `correlation_id`, timestamp.

## Steps
1. Confirm language (Go: `confluent-kafka-go` or `franz-go`; Python: `aiokafka`/`confluent-kafka`),
   topic(s), and the message schema.
2. Generate the consumer with the rules above; wire the dedupe store and DLQ.
3. Add a producer helper for emitting to the DLQ and any downstream topics.
4. Add metrics + structured logging and a clean shutdown path.
5. Include a short README documenting the group id, topics, DLQ name, and retry policy.

## Reference — DLQ decision (pseudocode)
```
for msg in poll():
    key = idempotency_key(msg)
    if seen(key): commit(msg); continue
    try:
        process(msg)            # side effects must be idempotent
        mark_seen(key)
        commit(msg)
    except Transient as e:
        if msg.attempt < MAX_RETRIES: retry_with_backoff(msg)
        else: to_dlq(msg, e); commit(msg)
    except Permanent as e:
        to_dlq(msg, e); commit(msg)
```
Never let a single bad message block the partition. Never process side effects without a dedupe guard.
