---
name: postgres-schema-reviewer
description: Use when reviewing PostgreSQL schema changes, migrations, or table designs before they ship. Checks TIMESTAMP vs TIMESTAMPTZ correctness, missing indexes on foreign keys and common query predicates, naming consistency (e.g. request_id vs correlation_id, singular vs plural), nullability and default hygiene, money stored as numeric not float, partitioning candidates for large append-only tables, and unsafe migration operations that take heavy locks (adding NOT NULL with a default on old PG, non-CONCURRENT index creation, rewriting column types). Trigger when the user shares a SQL migration, a CREATE TABLE / ALTER TABLE statement, an ORM model, or asks to review a database schema or migration.
license: MIT
---

# PostgreSQL Schema Reviewer

Review Postgres schemas and migrations with the eye of an engineer who has run them against
large production tables. Output concrete, prioritized findings — not generic advice.

## When to use
- User shares a migration file, `CREATE TABLE`/`ALTER TABLE`, or ORM model
- "Review this schema / migration / table design"
- Designing a new table or changing an existing one

## Review checklist

**Types**
- Use `TIMESTAMPTZ` for all points in time, never `TIMESTAMP` (which silently drops zone info).
- Money/amounts: `NUMERIC(precision, scale)`, never `float`/`double`.
- Prefer `BIGINT` identity / UUID over `INT` for keys likely to grow; `text` over `varchar(n)` unless a real limit exists.
- Enums: prefer a lookup table or a `CHECK` constraint over native `ENUM` (which is painful to alter).

**Integrity & hygiene**
- Every foreign key column should usually have a supporting index (PG does **not** auto-create it).
- Flag nullable columns that should be `NOT NULL`; flag missing sensible `DEFAULT`s.
- Add `created_at TIMESTAMPTZ NOT NULL DEFAULT now()` and `updated_at` where appropriate.
- Unique/business constraints expressed in the DB, not just app code.

**Naming consistency**
- Consistent casing (snake_case), consistent singular/plural table naming, consistent id naming
  across services (`request_id` vs `correlation_id` must mean the same thing everywhere).

**Indexes & scale**
- Indexes on columns used in `WHERE`, `JOIN`, `ORDER BY`; composite index column order matches query predicates.
- Large append-only tables (audit, events, logs, notifications) → consider **range/list partitioning**
  (e.g. monthly) and `pg_partman`.
- Watch for redundant/duplicate indexes and over-indexing on write-heavy tables.

**Migration safety (the dangerous part)**
- `CREATE INDEX` on a big table must be `CREATE INDEX CONCURRENTLY` (and cannot run in a txn block).
- Adding a column with a volatile default, or `SET NOT NULL`, can rewrite/lock the table on older PG —
  prefer add-nullable → backfill in batches → add constraint `NOT VALID` → `VALIDATE CONSTRAINT`.
- Changing a column type rewrites the table and takes an `ACCESS EXCLUSIVE` lock — call it out.
- Dropping a column/table: confirm it's safe; suggest a deprecation step first.

## Output format

Give findings grouped by severity:
1. **Blocking** — will cause downtime, data loss, or correctness bugs (e.g. naked `CREATE INDEX`
   on a hot table, `TIMESTAMP` for timestamps, money as float).
2. **Should fix** — missing FK index, missing NOT NULL, naming inconsistency.
3. **Consider** — partitioning, constraint tightening, index review.

For each finding: the exact line/object, *why* it matters in production, and the corrected SQL.
End with a one-line verdict: safe to ship / fix blockers first.
