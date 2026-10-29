---
id: beecount-sync-projection-contracts
scope: project
type: architecture
status: active
tags: [sync, projections, lww, migrations, partial-updates]
updated: 2026-09-19
---

# Post-0010/0011 Sync And Projection Contracts

- After migration 0010, account, category, tag, and exchange-rate overrides are user-global. Their `sync_changes` rows use `scope='user'`, the caller’s `user_id`, and `ledger_id=NULL`; projections are keyed by `(user_id, sync_id)`. Transactions and budgets remain ledger-scoped and are keyed by `(ledger_id, sync_id)`. Ignore a legacy client’s ledger ID for user-global entities.
- Accepted pushes append a `SyncChange` and update the relevant projection in the same batch transaction. Projections are the current read/materialization source; post-0011 code no longer writes full `ledger_snapshot` upserts. Migration 0011 deletes only legacy snapshot upserts and preserves snapshot delete events. Current implementation and tests supersede older sync prose that describes snapshots as authoritative.
- Conflict resolution is deterministic LWW over `(updated_at, device_id)`, with future client timestamps clamped to server time plus five seconds. An older tuple is rejected; an identical tuple is an accepted idempotent replay without another row. PostgreSQL materialization is protected by a transaction advisory lock per ledger; SQLite tests cover deterministic behavior, not the advisory lock itself.
- Mobile changes are partial patches. Missing or `None` fields are filled from the existing projection before upsert, so adding fields or changing writers must preserve this merge contract. User-global renames cascade through denormalized transaction names across all of the user’s ledgers before the global row is updated.
- Deletes remove the projection row and may compact obsolete upsert history, but preserve the delete event so lagging clients converge. `source_change_id` links projection rows to their materializing event for diagnosis.

## Evidence

- `alembic/versions/0010_user_global_projections.py`
- `alembic/versions/0011_drop_legacy_ledger_snapshot_changes.py`
- `src/routers/sync/push.py`
- `src/sync_applier.py`
- `src/projection.py`
- `tests/test_user_global_sync.py`
- `tests/test_projection_consistency.py`
- `tests/test_sync_concurrency.py`
