# Pinto cloud checkpoint

2026-10-03. Status: CLOUD_DB_VERIFIED; WEBSITE_BLOCKED. NOT READY.

Production target project: miptbxuadwbrqdhxcyqu, Pinto, https://supabase.com/dashboard/project/miptbxuadwbrqdhxcyqu . Staging/recovery: vrcdafrfzvfsijyokdcz, Pinto-staging. PostgreSQL17.11, private radar schema, PostGIS. Current canonical Event Sheets pointer has NOT switched.

Source reconciliation: all9 original tables match source API cells;89raw events=>88events/occurrences+1explicit alias,74originalsources,218edges,135searchchecks.49VERIFIED_PRIMARY and3candidates retained.11verifiedlocationrows/6mappedpublicoccurrences. Original source statuses never promoted by migration.

Cloud backup: actual export42tables/2220rows. Independent cloud restore42/42table row sets exact. Export SHA25611ece0ac707893cf13c74946a4f20b3ba6bada9c627d74b7ca8997bf98cd3e0c. Restore uses OVERRIDING SYSTEM VALUE for identity columns and resets sequence; no synthetic test in production. Staging has one separately labeled synthetic ingestion acceptance record added after restore verification. No recurring backup job activated.

API: public Supabase HTTPS RPC radar_search/radar_facets verified with publishable key. Operator SQL/RPC tested through Supabase Work connector; staging ingest committed/readback/replay/rejected conflicting retry. No production service key or operator REST token has been configured. Do not claim operator website REST/MCP continuity is deployed.

Vercel connector: list_teams=[]; deploy_to_vercel returned Tool deploy_to_vercel not found. No Vercel deployment/project/public website URL created. User authorization is required before browser fallback from this insufficient connector.

Deployment handoff: import ReShuLeo/ReShuLeo branch event-radar/product-v1; root PROJECTS/EVENT-RADAR; project name pinto; npm ci; npm run build; Next.js; Node24. Set SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY in provider environment using secret-safe account UI. Keep SUPABASE_SERVICE_ROLE_KEY and RADAR_OPERATOR_TOKEN server-only and add only with authorized private configuration. Never commit keys. The public pages require only the publishable key; operator routes return503 until private credentials configured.

Validate cloud website List/Map/mobile/location permission/error states and Work shared reads before promoting or switching canonical pointer. Keep Sheets writable authority until cutover, then freeze to projection; reconcile any new source revision before import/delta. Telegram account collection remains disabled. No health/nutrition/private LPOS data migrated.
