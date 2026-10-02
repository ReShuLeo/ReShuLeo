#!/usr/bin/env python3
"""Lossless, deterministic, replay-safe Sheets checkpoint -> PostgreSQL staging.
Never fetches private accounts; never publishes the input. Explicit alias evidence only.
"""
import argparse, json, uuid, hashlib, re, datetime
from pathlib import Path
from urllib.parse import urlparse
NS=uuid.UUID('3f8b005d-2346-4367-94c6-03075961b142')
def uid(kind,key):return str(uuid.uuid5(NS,kind+':'+str(key)))
def js(value):return json.dumps(value,ensure_ascii=False,separators=(',',':'))
def lit(value):
 if value is None or value=='':return 'NULL'
 if isinstance(value,(dict,list)):return "'"+js(value).replace("'","''")+"'::jsonb"
 if isinstance(value,bool):return 'true' if value else 'false'
 if isinstance(value,(int,float)):return str(value)
 return "'"+str(value).replace("'","''")+"'"
def digest(value):return hashlib.sha256(js(value).encode()).hexdigest()
def records(rows):return [dict(zip(rows[0],r)) for r in rows[1:] if any(v not in ('',None) for v in r)]
def optional_time(v):return v if v and re.fullmatch(r'\d{1,2}:\d{2}(:\d{2})?',str(v)) else None
def optional_date(v):
 if v and re.fullmatch(r'\d{4}-\d{2}-\d{2}',str(v)):datetime.date.fromisoformat(v);return v
 return None
def json_provenance(v):
 try:return json.loads(v) if isinstance(v,str) else v or {}
 except ValueError:return {'original_text':v}
def prepare(snapshot):
 tables=snapshot['tables'];data={t:records(r) for t,r in tables.items()};statements=['begin;','select pg_advisory_xact_lock(830261002);'];counts={t:len(v) for t,v in data.items()};issues=[]
 def insert(table,row,conflict='do nothing'):
  statements.append('insert into radar.'+table+'('+','.join(row)+') values('+','.join(lit(v) for v in row.values())+') on conflict '+conflict+';')
 # Reject drift on replay rather than silently ignore changed raw rows.
 for dataset,rows in tables.items():
  for rowno,row in enumerate(rows[1:],2):
   if not any(v not in ('',None) for v in row):continue
   r=dict(zip(rows[0],row));rh=digest(r)
   statements.append("do $$begin if exists(select 1 from radar.legacy_records where dataset="+lit(dataset)+" and row_number="+str(rowno)+" and content_hash<>"+lit(rh)+") then raise exception 'Checkpoint drift; do not overwrite';end if;end$$;")
   insert('legacy_records',{'dataset':dataset,'row_number':rowno,'legacy_id':row[0],'original':r,'content_hash':rh})
 country_names={'IT':'Italia','CH':'Svizzera'}
 for code,name in country_names.items():insert('countries',{'code':code,'name':name})
 city_info={c:('IT','Europe/Rome') for c in ['Milano','Como','Monza','Pero','Lecco','Rho']}
 city_info.update({c:('CH','Europe/Zurich') for c in ['Zürich','Lugano','Mendrisio','Chiasso','Massagno','Dübendorf','Horgen','Lugano-Viganello']})
 def location(key,city,address,timezone=None):
  country,tz=city_info.get(city,(None,timezone))
  if city:
   insert('cities',{'id':uid('city',city),'name':city,'country_code':country,'timezone':tz,'normalization_status':'KNOWN_CITY' if country else 'UNRESOLVED_IMPORTED'})
  lid=uid('location',key);insert('locations',{'id':lid,'city_id':uid('city',city) if city else None,'country_code':country,'timezone':timezone or tz,'original_address':address,'geocoding_status':'UNKNOWN'})
  return lid
 identities={'artist':{},'organizer':{},'venue':{},'source':{},'event':{}}
 name_maps={t:{} for t in ('artist','organizer','venue')}
 for table,kind in [('ARTISTS','artist'),('ORGANIZERS','organizer'),('VENUES','venue')]:
  for r in data[table]:
   legacy=r[kind+'_id'];identities[kind][legacy]=uid(kind,legacy);name_maps[kind].setdefault(r['name'],legacy)
   row={'id':uid(kind,legacy),'legacy_id':legacy,'name':r['name'],'official_url':r.get('official_url'),'last_verified':r.get('last_verified'),'verification_status':r.get('confidence') or 'UNVERIFIED_IMPORT','metadata':r}
   if kind=='venue':row['location_id']=location(legacy,r.get('city'),r.get('address'))
   else:row.update(instagram_url=r.get('instagram_url'),telegram_url=r.get('telegram_url'))
   insert(kind+'s',row)
 def named(kind,name,city=None,address=None,tz=None):
  if not name:return None
  key=name_maps[kind].get(name)
  if key:return identities[kind][key]
  key='EXTRACTED-'+uid(kind+'-name',name);identities[kind][key]=uid(kind,key);name_maps[kind][name]=key
  row={'id':uid(kind,key),'legacy_id':key,'name':name,'verification_status':'UNVERIFIED_IMPORT','metadata':{'created_from_legacy_event_field':True}}
  if kind=='venue':row['location_id']=location(key,city,address,tz)
  insert(kind+'s',row);return row['id']
 source_urls={}
 for r in data['SOURCES']:
  sid=uid('source',r['source_id']);identities['source'][r['source_id']]=sid
  if r.get('url'):source_urls.setdefault(r['url'],sid)
  insert('sources',{'id':sid,'legacy_id':r['source_id'],'name':r['name'],'kind':r['type'],'url':r.get('url'),'lane':r.get('lane'),'discovered_at':r.get('discovered_at'),'last_checked':r.get('last_checked'),'access_status':r.get('access_status'),'verification_status':r.get('confidence'),'metadata':r})
 def url_source(url):
  if url in source_urls:return source_urls[url]
  sid=uid('source-url',url);source_urls[url]=sid
  insert('sources',{'id':sid,'legacy_id':'LINK-'+sid,'name':urlparse(url).hostname or url,'kind':'IMPORTED_EVIDENCE_URL','url':url,'verification_status':'LINK_ONLY'})
  return sid
 aliases={r['event_id']:r['status'].split(':',1)[1] for r in data['EVENTS'] if r.get('status','').startswith('DUPLICATE_OF:')}
 canonical={r['event_id']:r for r in data['EVENTS'] if r['event_id'] not in aliases}
 for old,target in aliases.items():
  if target not in canonical:raise ValueError('Alias target missing:'+old)
 for r in data['EVENTS']:
  eid=r['event_id'];target=aliases.get(eid,eid);identities['event'][eid]=uid('event',target)
  if eid in aliases:continue
  status=r.get('status') or 'UNVERIFIED_IMPORT';prov=json_provenance(r.get('field_provenance'));date=optional_date(r.get('date'));end_date=optional_date(prov.get('end_date')) if isinstance(prov,dict) else None
  if end_date and date and end_date<date:issues.append({'event_id':eid,'issue':'INVALID_END_DATE'});end_date=None
  insert('events',{'id':uid('event',eid),'legacy_id':eid,'title':r['title'],'description':r.get('description'),'series':r.get('series'),'verification_status':status,'first_discovered':r.get('first_discovered'),'last_verified':r.get('last_verified'),'metadata':{'original_status':status,'confidence':r.get('confidence'),'field_provenance':prov,'audience':r.get('audience'),'delta_state':r.get('delta_state')}})
  venue=named('venue',r.get('venue'),r.get('city'),r.get('address'),r.get('timezone'))
  loc=location(eid,r.get('city'),r.get('address'),r.get('timezone'))
  start=optional_time(r.get('start'));end=optional_time(r.get('end'));tz=r.get('timezone')
  occurrence={'id':uid('occurrence',eid),'legacy_id':eid,'event_id':uid('event',eid),'venue_id':venue,'location_id':loc,'starts_on':date,'ends_on':end_date,'doors_local':optional_time(r.get('doors')),'start_local':start,'end_local':end,'timezone':tz,'status':status,'availability':r.get('availability'),'first_discovered':r.get('first_discovered'),'last_verified':r.get('last_verified'),'social_potential':str(r.get('social_potential') or ''),'guest_list':r.get('guest_list'),'membership':r.get('membership')}
  # Starts_at derives only from an actual known time AND timezone, no fake midnight.
  insert('event_occurrences',occurrence)
  if date and start and tz:statements.append('update radar.event_occurrences set starts_at=('+lit(date+' '+start)+'::timestamp at time zone '+lit(tz)+') where id='+lit(occurrence['id'])+' and starts_at is null;')
  for kind,field,join in [('artist','artist','event_artists'),('organizer','organizer','event_organizers'),('organizer','promoter','event_organizers')]:
   names=[v.strip() for v in (r.get(field) or '').split(';') if v.strip()]
   for name in names:
    entity=named(kind,name)
    row={'event_id':uid('event',eid),kind+'_id':entity}
    if kind=='organizer':row['role']=field.upper()
    insert(join,row)
  category=r.get('event_type') or 'OTHER';slug=re.sub(r'[^a-z0-9]+','-',category.lower()).strip('-') or 'other';cid=uid('category',slug)
  translations={'SHOW':'Шоу','CONCERT':'Концерт','BUSINESS_TECH':'Бизнес и технологии','THEATRE':'Театр','COMEDY':'Стендап','NETWORKING':'Networking','LECTURE':'Лекция','FESTIVAL':'Фестиваль','PARTY':'Вечеринка','AI/business/networking':'AI и бизнес'}
  insert('categories',{'id':cid,'slug':slug,'name':translations.get(category,category)})
  insert('event_categories',{'event_id':uid('event',eid),'category_id':cid})
  for language in re.split(r'[,;/+ ]+',r.get('language') or ''):
   if not language:continue
   language=language.lower();insert('languages',{'code':language,'name':{'ru':'Русский','uk':'Украинский','it':'Итальянский','en':'Английский','de':'Немецкий'}.get(language,language)})
   insert('event_languages',{'event_id':uid('event',eid),'language_code':language})
  urls=[]
  for key in ('official_url','ticket_url','instagram_url','telegram_url','verification_source'):
   value=r.get(key) or ''
   if value.startswith(('https://','http://')) and not any(ch.isspace() for ch in value):urls.append(value)
  for url in dict.fromkeys(urls):
   sid=url_source(url);insert('event_sources',{'id':uid('event-source',eid+url),'event_id':uid('event',eid),'occurrence_id':occurrence['id'],'source_id':sid,'url':url,'retrieved_at':r.get('last_verified'),'verified_at':r.get('last_verified') if status=='VERIFIED_PRIMARY' else None,'evidence_kind':'IMPORTED_VERIFICATION' if status=='VERIFIED_PRIMARY' else 'IMPORTED_LINK','field_provenance':prov})
  if r.get('ticket_url'):
   url=r['ticket_url'];sid=url_source(url)
   insert('ticket_offers',{'id':uid('ticket',eid+url),'occurrence_id':occurrence['id'],'source_id':sid,'provider':r.get('ticket_provider'),'url':url,'price_min':r.get('price_min'),'price_max':r.get('price_max'),'currency':r.get('currency'),'availability':r.get('availability'),'last_checked':r.get('last_verified')})
  if status=='VERIFIED_PRIMARY':insert('verification_records',{'id':uid('verification',eid),'event_id':uid('event',eid),'occurrence_id':occurrence['id'],'field_name':'legacy_record','claim':{'status':status},'method':'PRESERVED_EXISTING_VERIFICATION','outcome':status,'verified_at':r.get('last_verified'),'evidence':{'verification_source':r.get('verification_source'),'field_provenance':prov},'verifier':'legacy_import_no_new_verification'})
 for old,target in aliases.items():insert('entity_aliases',{'legacy_id':old,'event_id':uid('event',target),'occurrence_id':uid('occurrence',target),'reason':'EXPLICIT_LEGACY_DUPLICATE','evidence':{'original_status':'DUPLICATE_OF:'+target,'target':target}})
 # Every original graph node and edge survives; aliases retain their original node IDs.
 nodes={}
 for kind,mapping in identities.items():
  for key,entity_id in mapping.items():nodes[key]={'id':uid('node',key),'legacy_node_id':key,'entity_type':kind,kind+'_id':entity_id}
 for edge in data['EDGES']:
  for key in [edge['from_id'],edge['to_id']]:
   if key not in nodes:nodes[key]={'id':uid('node',key),'legacy_node_id':key,'entity_type':'unresolved','label':key,'metadata':{'unresolved_original_graph_node':True}};issues.append({'node':key,'issue':'UNRESOLVED_GRAPH_NODE'})
 for node in nodes.values():insert('source_entities',node)
 for r in data['EDGES']:
  insert('source_edges',{'id':uid('edge',r['edge_id']),'legacy_id':r['edge_id'],'from_entity':uid('node',r['from_id']),'to_entity':uid('node',r['to_id']),'relation':r['relation'],'provenance':r.get('provenance'),'discovered_at':r.get('discovered_at'),'confidence':r.get('confidence'),'metadata':r})
  event_id=identities['event'].get(r['from_id'])
  if event_id and r['relation'] in ['ARTIST','FEATURES','PERFORMER'] and r['to_id'] in identities['artist']:insert('event_artists',{'event_id':event_id,'artist_id':identities['artist'][r['to_id']]})
  if event_id and r['relation'] in ['ORGANIZER','PROMOTER','ORGANIZED_BY','CO_ORGANIZED_BY'] and r['to_id'] in identities['organizer']:insert('event_organizers',{'event_id':event_id,'organizer_id':identities['organizer'][r['to_id']],'role':'PROMOTER' if r['relation']=='PROMOTER' else 'ORGANIZER'})
 run_ids={r['run_id'] for r in data['SEARCH_LOG']}
 control=snapshot.get('related_lpos_records',{})
 run_records=records([control['RUNS']['header']]+control['RUNS']['rows']) if control.get('RUNS') else []
 for run in sorted(run_ids):
  linked=next((r for r in run_records if run in str(r.values())),{})
  insert('search_runs',{'id':uid('run',run),'legacy_id':run,'status':'INCOMPLETE','metadata':{'original_run_record':linked,'import_preserves_incomplete_no_coverage_promotion':True}})
 for i,r in enumerate(data['SEARCH_LOG']):insert('search_checks',{'id':uid('check',str(i)+js(r)),'run_id':uid('run',r['run_id']),'source_id':identities['source'].get(r.get('source_id')),'lane':r['lane'],'action':r.get('action'),'checked_at':r.get('checked_at'),'outcome':r.get('outcome'),'query_or_url':r.get('query_or_url'),'evidence':r.get('evidence'),'metadata':r})
 for table in ['CONFLICTS','INCIDENTS','OPERATIONS']:
  block=control.get(table); rows=records([block['header']]+block['rows']) if block else []
  for i,r in enumerate(rows):
   if table=='CONFLICTS':
    subject=r.get('subject','');key=next((k for k in canonical if k in subject),None)
    insert('conflicts',{'id':uid('conflict',r['conflict_id']),'legacy_id':r['conflict_id'],'event_id':uid('event',key) if key else None,'field_name':subject,'left_claim':{'value':r.get('left_value'),'source':r.get('left_source')},'right_claim':{'value':r.get('right_value'),'source':r.get('right_source')},'status':r['status'],'detected_at':r.get('detected_at'),'resolved_at':r.get('resolved_at'),'resolution':r.get('resolution'),'metadata':r})
   elif table=='INCIDENTS':insert('incidents',{'id':uid('incident',r['incident_id']),'legacy_id':r['incident_id'],'type':r['type'],'severity':r['severity'],'status':r['status'],'summary':r['summary'],'detected_at':r.get('detected_at'),'root_cause':r.get('root_cause'),'cause_confidence':r.get('cause_confidence'),'fix':r.get('fix'),'sibling_search':r.get('sibling_search'),'regression':r.get('regression'),'evidence':r})
   else:
    statements.append('insert into radar.change_log(legacy_operation_id,entity_type,entity_id,action,before_value,after_value,provenance,recorded_at) select '+','.join(lit(v) for v in [r['operation_id'],'legacy_operation',r.get('record_id'),r.get('action'),{'value':r.get('before_value')},{'value':r.get('after_value')},r,r.get('timestamp')])+' where not exists(select 1 from radar.change_log where legacy_operation_id='+lit(r['operation_id'])+');')
 checkpoint_id='SHEETS-'+snapshot['snapshot_sha256']
 insert('migration_checkpoints',{'id':checkpoint_id,'source_sha256':snapshot['snapshot_sha256'],'counts':counts,'status':'IMPORTED_AWAITING_VALIDATION','proof':{'source':'Google Sheets','actual_backup_id':snapshot['backup']['backup']['id'],'actual_restore_id':snapshot['backup']['restore']['id'],'original_rows_retained':True,'pointer_switched':False}})
 statements.append('commit;')
 return '\n'.join(statements)+'\n',{'source_records':counts,'canonical_events':len(canonical),'canonical_occurrences':len(canonical),'aliases':len(aliases),'issues':issues,'checkpoint_id':checkpoint_id,'snapshot_sha256':snapshot['snapshot_sha256'],'status':'PREPARED_NOT_CUTOVER'}
def main():
 p=argparse.ArgumentParser();p.add_argument('checkpoint');p.add_argument('--output',required=True);p.add_argument('--report',required=True);args=p.parse_args()
 snapshot=json.loads(Path(args.checkpoint).read_text());sql,report=prepare(snapshot)
 Path(args.output).parent.mkdir(parents=True,exist_ok=True);Path(args.output).write_text(sql);Path(args.report).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(js(report))
if __name__=='__main__':main()
