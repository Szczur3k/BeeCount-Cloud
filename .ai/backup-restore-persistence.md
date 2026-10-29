---
id: beecount-backup-restore-persistence
scope: project
type: runbook
status: active
tags: [sqlite, wal, backup, restore, docker, persistence]
updated: 2026-09-19
---

# WAL-Safe Backup, Restore, And Persistence

- The standard container persists the whole `/data` tree through one bind mount. It contains the SQLite database, attachments, backup/restore artifacts, rclone configuration, and JWT secret. Container replacement or image upgrades are safe only when this mount is retained; Alembic runs before Uvicorn on every start.
- Production SQLite uses WAL, `busy_timeout=5000`, `synchronous=NORMAL`, and foreign keys. Never back up a live deployment by copying only `beecount.db`: committed content may still be in `-wal`, and a concurrent copy can be inconsistent.
- Use the built-in backup runner (`VACUUM INTO`) or `scripts/backup_sqlite.sh` (`sqlite3 .backup`) for a clean standalone database file. The built-in archive can include attachments and `.jwt_secret`, fans out per remote, and keeps schema while clearing selected operational table rows; PAT rows intentionally remain so MCP clients survive restore.
- Server-side restore is staging only. It downloads and extracts under `<DATA_DIR>/restore/<run_id>/` and never replaces live data. Actual recovery requires stopping the service, manually replacing/copying the selected database and files, then restarting so migrations run. Treat database, attachments, and JWT/PAT continuity as one recovery set.

## Evidence

- `README.md`
- `docker-compose.yml`
- `Dockerfile`
- `src/database.py`
- `scripts/backup_sqlite.sh`
- `src/services/backup/db_snapshot.py`
- `src/services/backup/runner.py`
- `src/services/backup/restore_runner.py`
- `tests/test_sqlite_wal.py`
- `tests/test_backup_restore.py`
