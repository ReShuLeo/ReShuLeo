# 04-EVENT-RADAR

Version: 1.1.0
Change request: CCP-EVENT-PRODUCT-20261002; 2026-10-02T18:28:55.668Z; accepted by current explicit user architecture amendment.

Event Radar is a separate product in the LPOS ecosystem. TARGET: Supabase PostgreSQL/PostGIS with Next.js/Vercel website and versioned shared API. Work/operator, website and future bot/mobile use the same database. No nutrition/health/profile/private LPOS data migrates to this product.

CURRENT CANONICAL: retrieve live Control DATASETS and STORAGE-MAP. Until successful cloud migration and end-to-end validation, existing event workbook remains authoritative. Local staging PostgreSQL and migration/backup artifacts are NOT CANONICAL. Never replace a missing database read with embedded seed JSON or chat memory.

CUTOVER: verify cell-level legacy preservation, original89row receipt/88canonicalevents+oneexplicitduplicatealias, sources/artists/organizers/venues/218edges/135checks, unchanged imported statuses, conflicts/incidents, privileged write/readback, actual production backup+isolated restore, List/Map and shared website/Work reads. Record the exact project/API and version, then switch the sole pointer and freeze Sheets writes. Event incident/conflict authority moves with the domain; old shared Control entries become references, not competing editable records.

GEO: central locations hold PostGIS geography plus latitude/longitude/normalized address/city/country/timezone. Unknown coordinates stay null. Radius and bbox exclude unverified geometry only; discovery and list visibility do not exclude missing geocodes. Geolocation requires a user click/permission and is transient.

INGESTION: collectors/manual/web/ticket/artist/venue/social/Telegram evidence => private raw => candidates => verification/dedup => canonical events/occurrences. Preserve every source link and original text. Resolve explicit duplicates to canonical entity aliases; uncertain matches require review. Telegram account collection remains disabled pending authorization; raw messages and sessions are never public.

DISCOVERY: existing full runbook and independent A-J lanes remain mandatory. Native catalogue/social coverage is not satisfied by web snippets. Incomplete lanes mean INCOMPLETE; no no-new assertion. Historical regression/unchanged verified events are not repeated as news. Storage migration does not certify source coverage.

Work reads the exact live canonical project/API via authorized connector/MCP or the generic HTTP client after cutover. Local operator API tests are not proof of connected production Work continuity. Other LPOS domain stores remain unchanged.
