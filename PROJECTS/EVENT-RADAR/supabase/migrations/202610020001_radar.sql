-- Dedicated Event Radar database. No LPOS personal data belongs here.
begin;
create schema if not exists extensions;
create extension if not exists postgis with schema extensions;
create extension if not exists pgcrypto with schema extensions;
create schema if not exists radar;
revoke all on schema radar from public;
create table radar.schema_versions(version text primary key, applied_at timestamptz not null default now());
create table radar.countries(code char(2) primary key, name text not null);
create table radar.cities(id uuid primary key default gen_random_uuid(), name text not null, country_code char(2) references radar.countries, timezone text, normalization_status text not null default 'UNVERIFIED', unique(name,country_code));
create table radar.locations(
 id uuid primary key default gen_random_uuid(), city_id uuid references radar.cities,
 original_address text, normalized_address text, country_code char(2) references radar.countries,
 timezone text, latitude double precision, longitude double precision,
 point extensions.geography(Point,4326) generated always as
  (case when latitude is not null and longitude is not null then extensions.st_setsrid(extensions.st_makepoint(longitude,latitude),4326)::extensions.geography end) stored,
 geocoding_status text not null default 'UNKNOWN' check(geocoding_status in ('UNKNOWN','CANDIDATE','VERIFIED')),
 geocoding_source text, geocoded_at timestamptz,
 check(latitude between -90 and 90),check(longitude between -180 and 180),
 check((latitude is null)=(longitude is null)),check(geocoding_status <> 'VERIFIED' or (point is not null and geocoding_source is not null))
);
create index locations_point_gist on radar.locations using gist(point);
create table radar.artists(id uuid primary key default gen_random_uuid(),name text not null,official_url text,instagram_url text,telegram_url text,legacy_id text unique,verification_status text not null default 'UNVERIFIED_IMPORT',last_verified timestamptz,metadata jsonb not null default '{}');
create table radar.organizers(id uuid primary key default gen_random_uuid(),name text not null,official_url text,instagram_url text,telegram_url text,legacy_id text unique,verification_status text not null default 'UNVERIFIED_IMPORT',last_verified timestamptz,metadata jsonb not null default '{}');
create table radar.venues(id uuid primary key default gen_random_uuid(),name text not null,location_id uuid references radar.locations,official_url text,legacy_id text unique,verification_status text not null default 'UNVERIFIED_IMPORT',last_verified timestamptz,metadata jsonb not null default '{}');
create table radar.categories(id uuid primary key default gen_random_uuid(),slug text not null unique,name text not null);
create table radar.languages(code text primary key,name text not null);
create table radar.events(
 id uuid primary key default gen_random_uuid(),legacy_id text unique,title text not null,series text,
 description text,verification_status text not null default 'CANDIDATE_UNVERIFIED',
 first_discovered timestamptz,last_verified timestamptz,revision bigint not null default 1,
 created_at timestamptz not null default now(),updated_at timestamptz not null default now(),
 metadata jsonb not null default '{}'
);
create index events_search on radar.events using gin(to_tsvector('simple', title || ' ' || coalesce(description,'')));
create table radar.event_occurrences(
 id uuid primary key default gen_random_uuid(),event_id uuid not null references radar.events,
 legacy_id text unique,venue_id uuid references radar.venues,location_id uuid references radar.locations,
 starts_on date,ends_on date,doors_local time,start_local time,end_local time,timezone text,
 starts_at timestamptz,ends_at timestamptz,
 status text not null default 'CANDIDATE_UNVERIFIED',availability text,
 first_discovered timestamptz,last_verified timestamptz,
 social_potential text,guest_list text,membership text,
 check(ends_on is null or starts_on is null or ends_on >= starts_on)
);
create index occurrences_dates on radar.event_occurrences(starts_on,ends_on);
create index occurrences_discovery on radar.event_occurrences(first_discovered);
create table radar.event_languages(event_id uuid references radar.events,language_code text references radar.languages,primary key(event_id,language_code));
create table radar.event_artists(event_id uuid references radar.events,artist_id uuid references radar.artists,primary key(event_id,artist_id));
create table radar.event_organizers(event_id uuid references radar.events,organizer_id uuid references radar.organizers,role text not null default 'ORGANIZER',primary key(event_id,organizer_id,role));
create table radar.event_categories(event_id uuid references radar.events,category_id uuid references radar.categories,primary key(event_id,category_id));
create table radar.sources(
 id uuid primary key default gen_random_uuid(),legacy_id text unique,name text not null,kind text not null,url text,
 lane text,visibility text not null default 'PUBLIC' check(visibility in ('PUBLIC','OPERATOR_ONLY')),
 discovered_at timestamptz,last_checked timestamptz,access_status text,verification_status text,
 metadata jsonb not null default '{}'
);
create unique index sources_url_kind on radar.sources(url,kind) where url is not null;
create table radar.source_entities(
 id uuid primary key default gen_random_uuid(),legacy_node_id text not null unique,entity_type text not null,
 event_id uuid references radar.events,artist_id uuid references radar.artists,
 organizer_id uuid references radar.organizers,venue_id uuid references radar.venues,source_id uuid references radar.sources,
 label text,metadata jsonb not null default '{}',
 check(num_nonnulls(event_id,artist_id,organizer_id,venue_id,source_id)<=1)
);
create table radar.source_edges(id uuid primary key default gen_random_uuid(),legacy_id text unique,from_entity uuid not null references radar.source_entities,to_entity uuid not null references radar.source_entities,relation text not null,provenance text,discovered_at timestamptz,confidence text,metadata jsonb not null default '{}');
create table radar.event_sources(id uuid primary key default gen_random_uuid(),event_id uuid not null references radar.events,occurrence_id uuid references radar.event_occurrences,source_id uuid not null references radar.sources,url text,retrieved_at timestamptz,verified_at timestamptz,evidence_kind text not null default 'IMPORTED_LINK',field_provenance jsonb not null default '{}',visibility text not null default 'PUBLIC',unique(event_id,source_id,url));
create table radar.ticket_offers(id uuid primary key default gen_random_uuid(),occurrence_id uuid not null references radar.event_occurrences,source_id uuid references radar.sources,provider text,url text not null,price_min numeric(12,2),price_max numeric(12,2),currency char(3),availability text,last_checked timestamptz,affiliate_url text,check(price_min>=0),check(price_max>=0),check(price_max is null or price_min is null or price_max>=price_min),unique(occurrence_id,url));
create table radar.ingestion_runs(id uuid primary key default gen_random_uuid(),operation_id uuid unique,collector text not null,status text not null check(status in ('STARTED','SUCCEEDED','FAILED','PARTIAL')),started_at timestamptz not null default now(),finished_at timestamptz,error text,metadata jsonb not null default '{}');
create table radar.raw_ingestion(id uuid primary key default gen_random_uuid(),run_id uuid references radar.ingestion_runs,source_id uuid references radar.sources,external_key text not null,original_text text,payload jsonb not null,content_hash text not null,captured_at timestamptz not null default now(),visibility text not null default 'OPERATOR_ONLY',unique(source_id,external_key,content_hash));
create table radar.extracted_candidates(id uuid primary key default gen_random_uuid(),raw_id uuid not null references radar.raw_ingestion,extraction_version text not null,payload jsonb not null,status text not null default 'UNVERIFIED',resolved_event_id uuid references radar.events,resolved_occurrence_id uuid references radar.event_occurrences,created_at timestamptz not null default now(),unique(raw_id,extraction_version));
create table radar.verification_records(id uuid primary key default gen_random_uuid(),event_id uuid references radar.events,occurrence_id uuid references radar.event_occurrences,candidate_id uuid references radar.extracted_candidates,source_id uuid references radar.sources,field_name text not null,claim jsonb not null,method text not null,outcome text not null,verified_at timestamptz,evidence jsonb not null,verifier text);
create table radar.conflicts(id uuid primary key default gen_random_uuid(),legacy_id text unique,event_id uuid references radar.events,occurrence_id uuid references radar.event_occurrences,field_name text not null,left_claim jsonb not null,right_claim jsonb not null,status text not null default 'OPEN',detected_at timestamptz not null default now(),resolved_at timestamptz,resolution text,metadata jsonb not null default '{}');
create table radar.incidents(id uuid primary key default gen_random_uuid(),legacy_id text unique,event_id uuid references radar.events,type text not null,severity text not null,status text not null default 'OPEN',summary text not null,detected_at timestamptz,root_cause text,cause_confidence text,fix text,sibling_search text,regression text,evidence jsonb not null default '{}');
create table radar.search_runs(id uuid primary key default gen_random_uuid(),legacy_id text unique,started_at timestamptz,finished_at timestamptz,status text not null default 'INCOMPLETE',scope jsonb not null default '{}',metadata jsonb not null default '{}');
create table radar.search_checks(id uuid primary key default gen_random_uuid(),run_id uuid not null references radar.search_runs,source_id uuid references radar.sources,lane text not null,action text,checked_at timestamptz,outcome text,query_or_url text,evidence text,metadata jsonb not null default '{}');
create table radar.change_log(id bigint generated always as identity primary key,operation_id uuid,legacy_operation_id text,entity_type text not null,entity_id text,action text not null,before_value jsonb,after_value jsonb,provenance jsonb not null,recorded_at timestamptz not null default now());
create table radar.entity_aliases(legacy_id text primary key,event_id uuid not null references radar.events,occurrence_id uuid references radar.event_occurrences,reason text not null,evidence jsonb not null);
create table radar.entity_resolution_queue(id uuid primary key default gen_random_uuid(),candidate_id uuid references radar.extracted_candidates,possible_event_id uuid references radar.events,score numeric,method text not null,status text not null default 'REVIEW_REQUIRED',evidence jsonb not null);
create table radar.legacy_records(dataset text not null,row_number integer not null,legacy_id text,original jsonb not null,content_hash text not null,imported_at timestamptz not null default now(),primary key(dataset,row_number));
create table radar.migration_checkpoints(id text primary key,source_sha256 text not null,counts jsonb not null,status text not null,created_at timestamptz not null default now(),verified_at timestamptz,proof jsonb not null);
create table radar.telegram_chats(id uuid primary key default gen_random_uuid(),telegram_chat_id bigint not null unique,username text,title text,chat_type text,is_public boolean not null default false,authorized_at timestamptz);
create table radar.telegram_sources(id uuid primary key default gen_random_uuid(),chat_id uuid not null references radar.telegram_chats,source_id uuid not null unique references radar.sources,authorization_scope text not null,enabled boolean not null default false);
create table radar.telegram_messages(id uuid primary key default gen_random_uuid(),chat_id uuid not null references radar.telegram_chats,message_id bigint not null,message_timestamp timestamptz not null,original_text text not null,edited_at timestamptz,raw_id uuid references radar.raw_ingestion,public_url text,unique(chat_id,message_id, message_timestamp));
create table radar.telegram_sync_state(source_id uuid primary key references radar.telegram_sources,last_message_id bigint,last_sync_at timestamptz,status text not null default 'DISABLED',last_error text);
create table radar.users(id uuid primary key,email text,created_at timestamptz not null default now());
create table radar.user_preferences(user_id uuid primary key references radar.users,language text references radar.languages,city_id uuid references radar.cities,radius_km numeric check(radius_km>0 and radius_km<=250),preferences jsonb not null default '{}');
create table radar.favorites(user_id uuid references radar.users,event_id uuid references radar.events,created_at timestamptz not null default now(),primary key(user_id,event_id));
create table radar.subscriptions(id uuid primary key default gen_random_uuid(),user_id uuid not null references radar.users,provider text,external_id text unique,status text not null,valid_until timestamptz);
create table radar.alerts(id uuid primary key default gen_random_uuid(),user_id uuid not null references radar.users,channel text not null,filter jsonb not null,enabled boolean not null default false,last_sent_at timestamptz);
-- Private schema is deliberately NOT in the Supabase Data API exposed-schemas list.
-- RLS is deny-by-default. Public reads use narrowly scoped, explicit-field RPCs.
do $$ declare t record; begin
 for t in select tablename from pg_tables where schemaname='radar' loop
  execute format('alter table radar.%I enable row level security',t.tablename);
  execute format('revoke all on radar.%I from public,anon,authenticated',t.tablename);
 end loop;
end $$;
create function radar.prevent_audit_mutation() returns trigger language plpgsql set search_path='' as $$begin raise exception 'Append-only audit record';end$$;
create trigger change_log_append_only before update or delete on radar.change_log for each row execute function radar.prevent_audit_mutation();
create trigger legacy_append_only before update or delete on radar.legacy_records for each row execute function radar.prevent_audit_mutation();
insert into radar.schema_versions values('202610020001',now());
commit;
