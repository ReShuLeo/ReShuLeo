# 01-NUTRITION

Version: 1.0.1
Updated: 2026-10-02T17:00:56.808Z
Reason: full bootstrap request enables normalized views; prevent competing raw diaries.

Canonical raw sources remain the existing fitness workbook's ДНЕВНИК and ПРОДУКТЫ. FOOD_LOG, FOOD_REFERENCE and DAILY_SUMMARY are read-only normalized projections, never independent mutable truth. Resolve current source and projection locations from private STORAGE-MAP / DATASETS; do not duplicate personal records in GitHub.

Read all blocks for the requested date, including noncontiguous late additions. Numeric strings may represent calories. Meal/day subtotal rows overlap food leaves; food names beginning with «УЖИН» can still be leaves. Unknown food energy remains null. A known subtotal is not a complete day. A subtotal/component disagreement creates STATE_CONFLICT; do not silently choose one as complete.

Writes append raw facts with record_id, operation_id, event date, provenance and recorded_at. Corrections append supersedes referencing the earlier ID; preserve old raw rows, validate cycles/competing revisions, recompute projections, read back native values and journal VERIFIED. Before use compare projection source_hash against live raw inputs and regenerate stale views. Record status OPEN/CLOSED/CORRECTED separately from completeness; a corrected or closed day may remain PARTIAL.

Current state, SOURCE/PROVENANCE, CHANGELOG and INCIDENTS are domain-filtered shared Control records. Empty/inactive domains hold no invented facts. Version1.0.0 remains in Git history.
