#!/usr/bin/env python3
"""Manual identity-approved coordinates; no automatic nearest/name-only matching."""
import json,sys,hashlib
from pathlib import Path
from prepare_migration import lit,uid
source=json.loads(Path(sys.argv[1]).read_text());out=Path(sys.argv[2])
approved={
 460773978:{'names':['Auditorium di Milano'],'city':'Milano','country':'IT','timezone':'Europe/Rome','address':'Largo Gustav Mahler, 20136 Milano, Italia','official':'https://www.sinfonicadimilano.org/en/auditorium','note':'OSM reports side street Via Conchetta; retain official Largo Mahler address. Building identity and city agree.'},
 259338174:{'names':['LAC','Lugano, LAC'],'city':'Lugano','country':'CH','timezone':'Europe/Zurich','address':'Piazza Bernardino Luini 6, 6900 Lugano, Svizzera','official':'https://www.luganolac.ch/lac/home.html','note':'OSM name, official address number and city agree.'},
 63004115:{'names':['Theater Spirgarten'],'city':'Zürich','country':'CH','timezone':'Europe/Zurich','address':'Lindenplatz 5, 8048 Zürich, Svizzera','official':'https://www.spirgarten.ch/en/meeting-events/theater','note':'OSM Neues Theater Spirgarten and official venue name/city/street agree.'}
}
sql=['begin;','select pg_advisory_xact_lock(830261002);'];proof=[]
for r in source['results']:
 a=approved.get(r['osm_id'])
 if not a:continue
 if r['address'].get('city')!=a['city'] or r['address'].get('country_code','').upper()!=a['country']:raise ValueError('Identity mismatch')
 lat=float(r['lat']);lng=float(r['lon']);url='https://www.openstreetmap.org/'+r['osm_type']+'/'+str(r['osm_id']);evidence={'map_url':url,'retrieval_url':source['url'],'official_venue_url':a['official'],'value_type':'MAP_REPORTED','point_method':'OSM_POINT_OR_BUILDING_CENTROID','original_response':r,'identity_review':a['note']}
 conditions='v.name in ('+','.join(lit(n) for n in a['names'])+')'
 # Both venue and occurrence locations enriched; imported raw records remain immutable.
 sql.append('insert into radar.change_log(legacy_operation_id,entity_type,entity_id,action,before_value,after_value,provenance) select '+lit('GEO-OSM-'+str(r['osm_id']))+",'location',l.id::text,'VERIFIED_GEOCODING',to_jsonb(l),"+lit({'latitude':lat,'longitude':lng,'normalized_address':a['address']})+','+lit(evidence)+' from radar.locations l where l.latitude is null and (l.id in(select v.location_id from radar.venues v where '+conditions+') or l.id in(select o.location_id from radar.event_occurrences o join radar.venues v on v.id=o.venue_id where '+conditions+'));')
 sql.append('update radar.locations l set latitude='+str(lat)+',longitude='+str(lng)+',normalized_address='+lit(a['address'])+',geocoding_status=\'VERIFIED\',geocoding_source='+lit(url)+'||\';identity:\'||'+lit(a['official'])+',geocoded_at=now() where l.latitude is null and (l.id in(select v.location_id from radar.venues v where '+conditions+') or l.id in(select o.location_id from radar.event_occurrences o join radar.venues v on v.id=o.venue_id where '+conditions+'));')
 proof.append(evidence)
sql.append('commit;');out.write_text('\n'.join(sql)+'\n');out.with_suffix('.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n');print('approved_osm_entities',len(proof))
