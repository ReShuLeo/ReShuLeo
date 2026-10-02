# Event Radar product impact review — 2026-10-02

User's explicit amendment authorizes the new target. Second review accepts implementation preparation; cloud READY is withheld.

| Perspective | Failure / conflicting authority | Repair and second review |
|---|---|---|
| LLM systems | Work continues reading cached Sheets after cloud cutover | Live locator registry, exact project/API ID, unavailable => STATE NOT LOADED. Accept only after connected Work test. |
| Data architecture | Tour title, venue, ticket, occurrence become repeated events | Events + occurrences, explicit aliases, many-to-many participants/categories/languages. Preserve doubtful matches for review. Accepted. |
| Database reliability | Replay duplicates; changed import silently overwritten | Deterministic IDs, transaction/advisory lock, immutable legacy rows, drift rejection, readback. Local tests pass; cloud check pending. |
| Knowledge/RAG | Backup or public page presented as current canonical state | One canonical pointer, projection fingerprints, current direct RPC. No JSON fallback. Accepted. |
| Automation | Collector half-run falsely called complete | Runs/checks preserved; full-run lanes remain mandatory; no scheduler created. Accepted. |
| Platform | Temporary ChatGPT tools constrain core product | Vendor-neutral versioned HTTP API/RPC contract and thin Work client; future MCP wraps it. Next/Vercel/Supabase target retained. Accepted. |
| QA | Successful SQL execution mistaken for migration completion | Cell-level raw comparison, counts, FK/graph checks, status tests, idempotence, recovery, geo and API tests. Production/browser tests still blocked. |
| SRE | Written backup policy mistaken for existing scheduled backup | Actual dump/restore receipt for staging; cloud backup explicitly unprovisioned. Read-based health endpoint. Accepted with cloud gate. |
| OSINT | Source text conflated with verified facts | Raw/candidate/verification separate; imported evidence statuses unchanged. Conflicts retained. Accepted. |
| Event intelligence | City/date error hidden by fuzzy dedup or strong social ranking | Explicit-only automatic aliases; Druga candidate and city conflict retained, Urgant linked to official tour and ticket provider. Accepted. |
| Nutrition/Fitness data | Public product leaks personal meals/metrics | No nutrition, fitness, health or profile rows migrate. Existing workbook untouched. Accepted. |
| Security/privacy | Anonymous data API exposes Telegram text or audit; service key in browser | Private `radar` schema, deny-by-default RLS/grants, limited-field RPCs, separate privileged API, safe source URLs. Anonymous denial and HTML secret checks pass locally. Cloud advisors pending. |
| Product | Build speculative subscriptions/enterprise services first | Reserve user/favorites/alerts/subscription schema; activate no billing, auth UI or notifications. Working List/Map/search/date/radius product only. Accepted. |
| Google Workspace | Old Sheets remains independent writable truth | Retain old authority until gates pass; after cutover export/admin projection only. Accepted. |
| Configuration management | Core silently changes; private checkpoint committed in Git | Versioned accepted change proposal; code-only repository, private migration/backup artifacts separated. Accepted. |

## Normalization choices

`search_checks` retains per-lane attempts in addition to `search_runs`; `source_edges` preserves all original graph edges. `legacy_records` is an immutable migration receipt, not a parallel mutable event database. `entity_aliases` retains explicit duplicate legacy IDs. `locations` centralizes geometry; venue/occurrence reference it rather than maintaining independently editable coordinate copies. API event responses include latitude/longitude/address/city/country/timezone through those relationships.

Telegram entities preserve chat ID, message ID/time/original text, raw extraction candidate and resolved event path. They are empty and inaccessible publicly. No Telegram login, session, scraper or account credentials were requested or used.

No source completeness claim improves because storage changed. Event Radar's latest discovery run stays INCOMPLETE. Building a product does not imply zero missed events.
