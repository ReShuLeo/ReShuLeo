// Isolated test adapter only. Not a second production database and not a deployment target.
// Production routes use the same Supabase RPC names over PostgREST.
import {PGlite} from '@electric-sql/pglite';import {postgis} from '@electric-sql/pglite-postgis';import {pgcrypto} from '@electric-sql/pglite/contrib/pgcrypto';import fs from 'node:fs/promises';import http from 'node:http';import {randomBytes} from 'node:crypto';
const directory=process.argv[2];if(!directory)throw new Error('Private staging snapshot directory required');
const pg=new PGlite({extensions:{postgis,pgcrypto}});await pg.exec('create role anon;create role authenticated;create role service_role;');for(const file of ['202610020001_radar.sql','202610020002_api.sql'])await pg.exec(await fs.readFile('supabase/migrations/'+file,'utf8'));await pg.exec(await fs.readFile(directory+'/import.sql','utf8'));try{await pg.exec(await fs.readFile(directory+'/geocoding.sql','utf8'));}catch(e){if(e.code!=='ENOENT')throw e;}
const key=randomBytes(32).toString('hex');const operatorKey=randomBytes(32).toString('hex');const workToken=randomBytes(32).toString('hex');
const server=http.createServer(async(req,res)=>{res.setHeader('Content-Type','application/json');try{
 if(![key,operatorKey].includes(req.headers.apikey)){res.writeHead(401);res.end('{}');return;}
 const chunks=[];for await(const c of req)chunks.push(c);const args=JSON.parse(Buffer.concat(chunks).toString()||'{}');let value;
 if(req.url==='/rest/v1/rpc/radar_search')value=(await pg.query('select public.radar_search($1) value',[args.p_filters||{}])).rows[0].value;
 else if(req.url==='/rest/v1/rpc/radar_facets')value=(await pg.query('select public.radar_facets() value')).rows[0].value;
 else if(req.url==='/rest/v1/rpc/radar_operator_search'&&req.headers.apikey===operatorKey)value=(await pg.query('select public.radar_operator_search($1) value',[args.p_filters||{}])).rows[0].value;
 else if(req.url==='/rest/v1/rpc/radar_ingest'&&req.headers.apikey===operatorKey)value=(await pg.query('select public.radar_ingest($1,$2,$3,$4,$5,$6) value',[args.p_operation,args.p_source,args.p_external_key,args.p_text,args.p_payload,args.p_collector])).rows[0].value;
 else{res.writeHead(403);res.end('{}');return;}res.end(JSON.stringify(value));
 }catch(e){res.writeHead(500);res.end(JSON.stringify({error:e.message}));}});
server.listen(54321,'0.0.0.0',async()=>{await fs.writeFile('.env.local',`SUPABASE_URL=http://127.0.0.1:54321\nSUPABASE_PUBLISHABLE_KEY=${key}\nSUPABASE_SERVICE_ROLE_KEY=${operatorKey}\nRADAR_OPERATOR_TOKEN=${workToken}\nRADAR_STAGING_DIRECTORY=${directory}\nNEXT_PUBLIC_STAGING_NOTICE=Проверочная версия. Облачная база ещё не подключена.\n`);console.log('Staging PostgreSQL RPC adapter ready; test keys written to ignored .env.local (not printed).');});
