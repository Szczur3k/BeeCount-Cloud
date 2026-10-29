# Project Knowledge Index

Use this document to select only knowledge relevant to the current task. Do not
load all knowledge files.

## Sync And Projections

Path: `sync-projection-contracts.md`

Read when:
- changing sync push/pull, migrations, projections, conflict resolution, partial updates, rename cascades, or deletes

Contains:
- post-0010 user-global versus ledger scope
- post-0011 projection authority, deterministic LWW, and partial-merge contracts

## Backup And Recovery

Path: `backup-restore-persistence.md`

Read when:
- changing Docker persistence, SQLite settings, backups, restore, retention, attachments, or JWT/PAT recovery

Contains:
- `/data` ownership and WAL-safe snapshot requirements
- isolated restore staging and manual live-data replacement boundaries

## MCP And Document RAG

Path: `mcp-and-docs-index-runtime.md`

Read when:
- changing MCP transport/auth/tools, startup lifecycle, Docker builds, document Q&A, embedding providers, or indexes

Contains:
- PAT-only Streamable HTTP MCP and in-process write-path reuse
- image-bundled index and runtime embedding-model coupling

## License And Contributions

Path: `licensing-and-contributions.md`

Read when:
- evaluating use, distribution, commercial deployment, attribution, modified-source obligations, or accepting contributions

Contains:
- noncommercial versus paid-commercial license boundaries
- contributor sublicense grant and authorship warranty

`KNOWLEDGE-PROPOSAL.md` is a review buffer, not authoritative knowledge.
