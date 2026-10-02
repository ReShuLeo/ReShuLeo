# Event Radar

Next.js + Supabase PostgreSQL + PostGIS. One database; public website and operator API are two interfaces. LPOS personal data is excluded.

Current delivery: implementation and isolated staging tests. Supabase and Vercel must be authorized before provisioning/deployment. Google Sheets remains canonical until the cutover checks in `docs/MIGRATION-RUNBOOK.md` pass. No built-in JSON event fallback exists.

## Run

`npm ci`, configure server environment from `.env.example`, then `npm run dev`. `npm run build` and `npm start` use the real Supabase HTTP RPCs. Supabase service credentials and operator token never enter browser code. `npm test` and `npm run typecheck` verify filter/URL guards and types.

`RADAR_STAGING_DIRECTORY` is an explicit development-only switch for an isolated PGlite PostgreSQL/PostGIS test adapter. It is not the production database, a live canonical pointer, or a hosted product. Its PostGIS distribution is experimental; real Supabase acceptance remains mandatory. Do not set this variable in production. Test snapshots, `.env.local`, data dumps and credentials are ignored and absent from the repository.

## API

- `GET /api/v1/events` — verified events; date range, search, city, radius, bounding box, category, language, free/price, artist, venue, organizer, sorting and pagination.
- `GET /api/v1/facets` — public filter choices.
- `GET /api/v1/operator/events` — authenticated candidate/unverified queries against the same database.
- `POST /api/v1/operator/ingest` — authenticated, idempotent raw evidence write with source/run/audit trail. No silent publication.
- `GET /api/health` — actual PostgreSQL read; unavailable is HTTP503.

Filters: `q`, `from`, `to`, `city`, `radius_km`, `lat`, `lng`, `bbox=west,south,east,north`, `category`, `language`, `free=true`, `price_max` with `currency`, `venue`, `artist`, `organizer`, `sort=date|distance|newest`, `limit`, `offset`, `discovered_since`. Operator additionally supports `status`.

Geolocation is requested on a user click, never automatically. Coordinates are transient query parameters; they are not stored in user preferences. Radius works only with verified venue coordinates. Unknown locations remain null and their events remain visible in the list. Bounding boxes crossing the antimeridian are rejected in this regional MVP.

Raw evidence, Telegram text, audit, conflicts and incidents are private. No Telegram account collector has been enabled. Supabase Auth/Storage and user tables are reserved for later features; registration, payments, notifications and subscriptions are not activated.

No searches, notifications or backups have been scheduled. Proposed schedules require the owner's authorization.
