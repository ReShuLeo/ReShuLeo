# Backup and recovery

Version: 1.0.0

Bootstrap: copy each canonical native workbook into the LPOS BACKUPS folder, retaining provider IDs and timestamps. Read a representative food day, profile record and event from the copies; compare against canonical rows. For full-snapshot checks export or bounded-read all populated tabs and compare hashes. Record read-only restore verification; do not claim a destructive disaster-recovery drill.

Proposed, not active: daily operational snapshots with 7 daily / 4 weekly / 6 monthly retention; weekly checksum and monthly isolated restore. No deletion or schedule is active until approved. Recovery: stop writes, locate last verified backup, compare provenance and journal newer operations, create an isolated restore, validate integrity, then propose canonical pointer change with audit. Never silently read backup as current. Git history restores policy/code but not operational user records.
