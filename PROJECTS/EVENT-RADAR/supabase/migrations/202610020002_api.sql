begin;
create function radar.search_impl(f jsonb, operator_mode boolean default false) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare answer jsonb; lat double precision; lng double precision; radius double precision; box jsonb;
begin
 lat := nullif(f->>'lat','')::double precision; lng := nullif(f->>'lng','')::double precision;
 radius := nullif(f->>'radius_km','')::double precision; box := f->'bbox';
 if (lat is null) <> (lng is null) or lat not between -90 and 90 or lng not between -180 and 180 then raise exception 'Invalid coordinates' using errcode='22023';end if;
 if radius is not null and (lat is null or radius<=0 or radius>250) then raise exception 'Invalid radius' using errcode='22023';end if;
 if f->>'sort'='distance' and lat is null then raise exception 'Distance requires location' using errcode='22023';end if;
 if box is not null and (jsonb_array_length(box)<>4 or (box->>0)::float8 not between -180 and 180 or (box->>2)::float8 not between -180 and 180 or (box->>1)::float8 not between -90 and 90 or (box->>3)::float8 not between -90 and 90 or (box->>0)::float8 >= (box->>2)::float8 or (box->>1)::float8 >= (box->>3)::float8) then raise exception 'Invalid map bounds' using errcode='22023';end if;
 with base as materialized (
 select o.id as occurrence_id,e.id as event_id,e.legacy_id,e.title,e.description,e.series,o.starts_on,o.ends_on,o.start_local,o.end_local,o.doors_local,o.timezone,o.starts_at,o.status,e.last_verified,o.first_discovered,o.guest_list,o.membership,o.availability,
 v.name venue,v.id venue_id,c.name city,c.country_code,l.normalized_address,l.original_address,l.latitude,l.longitude,l.geocoding_status,
 case when lat is not null and l.geocoding_status='VERIFIED' then extensions.st_distance(l.point,extensions.st_setsrid(extensions.st_makepoint(lng,lat),4326)::extensions.geography)/1000 end distance_km,
 l.point,
 coalesce((select jsonb_agg(jsonb_build_object('id',a.id,'name',a.name)) from radar.event_artists j join radar.artists a on a.id=j.artist_id where j.event_id=e.id),'[]'::jsonb) artists,
 coalesce((select jsonb_agg(jsonb_build_object('id',a.id,'name',a.name,'role',j.role)) from radar.event_organizers j join radar.organizers a on a.id=j.organizer_id where j.event_id=e.id),'[]'::jsonb) organizers,
 coalesce((select jsonb_agg(jsonb_build_object('id',a.id,'name',a.name,'slug',a.slug)) from radar.event_categories j join radar.categories a on a.id=j.category_id where j.event_id=e.id),'[]'::jsonb) categories,
 coalesce((select jsonb_agg(j.language_code) from radar.event_languages j where j.event_id=e.id),'[]'::jsonb) languages,
 coalesce((select jsonb_agg(jsonb_build_object('provider',t.provider,'url',t.url,'price_min',t.price_min,'price_max',t.price_max,'currency',t.currency,'availability',t.availability,'last_checked',t.last_checked)) from radar.ticket_offers t where t.occurrence_id=o.id),'[]'::jsonb) tickets,
 coalesce((select jsonb_agg(jsonb_build_object('name',s.name,'url',es.url,'verified_at',es.verified_at,'evidence_kind',es.evidence_kind)) from radar.event_sources es join radar.sources s on s.id=es.source_id where es.event_id=e.id and es.visibility='PUBLIC' and s.visibility='PUBLIC' and es.url ~ '^https?://'),'[]'::jsonb) sources
 from radar.event_occurrences o join radar.events e on e.id=o.event_id
 left join radar.venues v on v.id=o.venue_id left join radar.locations l on l.id=coalesce(o.location_id,v.location_id) left join radar.cities c on c.id=l.city_id
 where (operator_mode or (o.status='VERIFIED_PRIMARY' and e.verification_status='VERIFIED_PRIMARY'))
 and (not operator_mode or f->>'status' is null or o.status=f->>'status')
 and (f->>'occurrence_id' is null or o.id::text=f->>'occurrence_id')
 and (f->>'from' is null or coalesce(o.ends_on,o.starts_on)>=(f->>'from')::date)
 and (f->>'to' is null or o.starts_on<=(f->>'to')::date)
 and (f->>'discovered_since' is null or o.first_discovered>=(f->>'discovered_since')::timestamptz)
 and (f->>'city' is null or c.name=f->>'city')
 and (f->>'venue' is null or v.name=f->>'venue')
 and (f->>'artist' is null or exists(select 1 from radar.event_artists j join radar.artists a on a.id=j.artist_id where j.event_id=e.id and a.name=f->>'artist'))
 and (f->>'organizer' is null or exists(select 1 from radar.event_organizers j join radar.organizers a on a.id=j.organizer_id where j.event_id=e.id and a.name=f->>'organizer'))
 and (f->>'category' is null or exists(select 1 from radar.event_categories j join radar.categories a on a.id=j.category_id where j.event_id=e.id and a.slug=f->>'category'))
 and (f->>'language' is null or exists(select 1 from radar.event_languages j where j.event_id=e.id and j.language_code=f->>'language'))
 and (coalesce((f->>'free')::boolean,false)=false or exists(select 1 from radar.ticket_offers t where t.occurrence_id=o.id and t.price_min=0))
 and (f->>'price_max' is null or exists(select 1 from radar.ticket_offers t where t.occurrence_id=o.id and t.price_min<=(f->>'price_max')::numeric and (f->>'currency' is null or t.currency=f->>'currency')))
 and (nullif(f->>'q','') is null or e.title ilike '%'||(f->>'q')||'%' or to_tsvector('simple',e.title||' '||coalesce(e.description,'')) @@ plainto_tsquery('simple',f->>'q'))
 and (radius is null or (l.geocoding_status='VERIFIED' and extensions.st_dwithin(l.point,extensions.st_setsrid(extensions.st_makepoint(lng,lat),4326)::extensions.geography,radius*1000)))
 and (box is null or (l.geocoding_status='VERIFIED' and extensions.st_intersects(l.point::extensions.geometry,extensions.st_makeenvelope((box->>0)::float8,(box->>1)::float8,(box->>2)::float8,(box->>3)::float8,4326))))
 ), page as (
 select b.*, count(*) over() total from base b
 order by case when f->>'sort'='distance' then distance_km end nulls last,
 case when f->>'sort'='newest' then first_discovered end desc nulls last, starts_on nulls last,start_local nulls last,occurrence_id
 limit least(greatest(coalesce((f->>'limit')::integer,50),1),200) offset greatest(coalesce((f->>'offset')::integer,0),0)
 )
 select jsonb_build_object('items',coalesce((select jsonb_agg(to_jsonb(p)-'point'-'total') from page p),'[]'::jsonb),'total',(select count(*) from base),'mapped',(select count(*) from base where geocoding_status='VERIFIED'),'database','postgresql','generated_at',now()) into answer;
 return answer;
end $$;
revoke all on function radar.search_impl(jsonb,boolean) from public,anon,authenticated;
create function public.radar_search(p_filters jsonb default '{}') returns jsonb language sql stable security definer set search_path='' as $$ select radar.search_impl(p_filters,false) $$;
revoke all on function public.radar_search(jsonb) from public;
grant execute on function public.radar_search(jsonb) to anon,authenticated,service_role;
create function public.radar_operator_search(p_filters jsonb default '{}') returns jsonb language sql stable security definer set search_path='' as $$ select radar.search_impl(p_filters,true) $$;
revoke all on function public.radar_operator_search(jsonb) from public,anon,authenticated;
grant execute on function public.radar_operator_search(jsonb) to service_role;
create function public.radar_facets() returns jsonb language sql stable security definer set search_path='' as $$
 select jsonb_build_object(
 'cities',coalesce((select jsonb_agg(name order by name) from radar.cities c where exists(select 1 from radar.locations l join radar.event_occurrences o on o.location_id=l.id join radar.events e on e.id=o.event_id where l.city_id=c.id and o.status='VERIFIED_PRIMARY' and e.verification_status='VERIFIED_PRIMARY')),'[]'::jsonb),
 'categories',coalesce((select jsonb_agg(jsonb_build_object('name',name,'slug',slug) order by name) from radar.categories),'[]'::jsonb),
 'languages',coalesce((select jsonb_agg(jsonb_build_object('code',code,'name',name) order by name) from radar.languages),'[]'::jsonb),
 'artists',coalesce((select jsonb_agg(name order by name) from radar.artists a where exists(select 1 from radar.event_artists j join radar.events e on e.id=j.event_id where j.artist_id=a.id and e.verification_status='VERIFIED_PRIMARY')),'[]'::jsonb),
 'organizers',coalesce((select jsonb_agg(name order by name) from radar.organizers a where exists(select 1 from radar.event_organizers j join radar.events e on e.id=j.event_id where j.organizer_id=a.id and e.verification_status='VERIFIED_PRIMARY')),'[]'::jsonb),
 'venues',coalesce((select jsonb_agg(name order by name) from radar.venues v where exists(select 1 from radar.event_occurrences o where o.venue_id=v.id and o.status='VERIFIED_PRIMARY')),'[]'::jsonb)
 ) $$;
revoke all on function public.radar_facets() from public;
grant execute on function public.radar_facets() to anon,authenticated,service_role;
create function public.radar_ingest(p_operation uuid,p_source uuid,p_external_key text,p_text text,p_payload jsonb,p_collector text default 'manual') returns jsonb
language plpgsql security definer set search_path='' as $$
declare run_uuid uuid; raw_uuid uuid; payload_hash text; previous_hash text;
begin
 if length(p_external_key)>500 or octet_length(p_text)>1048576 or octet_length(p_payload::text)>1048576 then raise exception 'Input too large';end if;
 if not exists(select 1 from radar.sources where id=p_source) then raise exception 'Unknown source';end if;
 payload_hash:=encode(extensions.digest(convert_to(coalesce(p_text,'')||p_payload::text,'UTF8'),'sha256'),'hex');
 select id,metadata->>'hash' into run_uuid,previous_hash from radar.ingestion_runs where operation_id=p_operation;
 if run_uuid is not null then
  if previous_hash<>payload_hash then raise exception 'Idempotency conflict';end if;
  select id into raw_uuid from radar.raw_ingestion where run_id=run_uuid;
  return jsonb_build_object('run_id',run_uuid,'raw_id',raw_uuid,'status','REPLAYED');
 end if;
 insert into radar.ingestion_runs(operation_id,collector,status,metadata) values(p_operation,p_collector,'STARTED',jsonb_build_object('hash',payload_hash)) returning id into run_uuid;
 insert into radar.raw_ingestion(run_id,source_id,external_key,original_text,payload,content_hash) values(run_uuid,p_source,p_external_key,p_text,p_payload,payload_hash)
 on conflict(source_id,external_key,content_hash) do nothing returning id into raw_uuid;
 if raw_uuid is null then select id into raw_uuid from radar.raw_ingestion where source_id=p_source and external_key=p_external_key and content_hash=payload_hash;end if;
 insert into radar.change_log(operation_id,entity_type,entity_id,action,after_value,provenance) values(p_operation,'raw_ingestion',raw_uuid::text,'INGEST',jsonb_build_object('hash',payload_hash),jsonb_build_object('source_id',p_source,'collector',p_collector));
 update radar.ingestion_runs set status='SUCCEEDED',finished_at=now() where id=run_uuid;
 return jsonb_build_object('run_id',run_uuid,'raw_id',raw_uuid,'status','SUCCEEDED');
end $$;
revoke all on function public.radar_ingest(uuid,uuid,text,text,jsonb,text) from public,anon,authenticated;
grant execute on function public.radar_ingest(uuid,uuid,text,text,jsonb,text) to service_role;
-- No Telegram collector is activated by these migrations.
insert into radar.schema_versions values('202610020002',now());
commit;
