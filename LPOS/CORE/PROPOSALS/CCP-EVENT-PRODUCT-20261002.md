# CCP-EVENT-PRODUCT-20261002

Status: ACCEPTED BY CURRENT EXPLICIT USER REQUEST; 2026-10-02T18:28:55.668Z
Core:1.0.0 ->1.1.0. Event Domain Core:1.0.0 ->1.1.0. Storage Map:1.0.2 ->1.1.0.

Problem: Event Radar's Sheets operational store cannot be the target architecture for a multi-user cloud product with spatial queries and multiple interfaces.
Evidence: current user amendment specifies Supabase/PostgreSQL/PostGIS, Next.js/Vercel, shared API, Telegram provenance and preservation of existing records. Live current state has89eventrows,74sources,218edges; existing9tablebackup+restore equals the new checkpoint.
Change: accept the target product architecture, keep personal LPOS separate, support provider-appropriate transactions and require a measured cutover. Do not change the current canonical pointer yet.
Affected domains: Event Radar, global placement/protocol; no new nutrition/health migration.
Migration impact: preserve all original rows/cells/provenance; normalize event/occurrence/entities; one explicit duplicate becomes an alias. Retain statuses and conflicts. Old event Control incidents become references after destination verification, not before.
Regression:25 PostgreSQL/PostGIS staging checks,8 HTTP/API checks,4 filter/security tests and Next production build pass. Real Supabase/Vercel, connected Work API and browser acceptance remain pending. Source discovery remains INCOMPLETE.
Rollback: untouched existing Sheets stays canonical now; after cutover reconcile post-cutover writes before any reversal. No destructive schema rollback is authorized.
Second review: professional impact review is in product docs/ARCHITECTURE-REVIEW.md. No account collector/schedules/billing have been activated.
