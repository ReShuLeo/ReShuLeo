import {spawn} from 'node:child_process';import fs from 'node:fs/promises';import assert from 'node:assert/strict';
const directory=process.argv[2];if(!directory)throw new Error('Private test snapshot required');let children=[];let checks=[];
function start(script,args,ready){const p=spawn(process.execPath,[script,...args],{stdio:['ignore','pipe','pipe'],env:{...process.env,NO_PROXY:'127.0.0.1,localhost',NEXT_TELEMETRY_DISABLED:'1'}});children.push(p);return new Promise((resolve,reject)=>{let logs='';const timer=setTimeout(()=>reject(new Error('Server startup timeout:'+logs.slice(-500))),20000);const handle=b=>{logs+=b.toString();if(logs.includes(ready)){clearTimeout(timer);resolve(p);}};p.stdout.on('data',handle);p.stderr.on('data',handle);p.on('exit',code=>{clearTimeout(timer);reject(new Error('Server exited:'+code+' '+logs.slice(-500)));});});}
function pass(s){checks.push(s);console.log('PASS',s)}
try{
 await start('scripts/staging_api.mjs',[directory],'adapter ready');
 await start('node_modules/next/dist/bin/next',['start','--hostname','127.0.0.1','--port','3001'],'Ready');
 const root='http://127.0.0.1:3001';const read=async path=>{const r=await fetch(root+path,{signal:AbortSignal.timeout(10000)});return {status:r.status,value:await r.json()};};
 const health=await read('/api/health');assert.equal(health.status,200);pass('website_api_database_health');
 const all=await read('/api/v1/events?limit=200');assert.equal(all.status,200);assert.equal(all.value.total,49);assert.ok(all.value.mapped>0);pass('same_postgresql_49_verified_public_events');
 const id=all.value.items.find(r=>r.legacy_id==='EV-URGANT-MIL-20261020').occurrence_id;
 const close=await read('/api/v1/events?lat=45.4465818&lng=9.1791645&radius_km=1&sort=distance');assert.equal(close.status,200);assert.ok(close.value.items.some(r=>r.occurrence_id===id));pass('geo_search_reads_verified_coordinates');
 const free=await read('/api/v1/events?free=true');assert.ok(free.value.items.some(r=>r.legacy_id==='EV-CRASHAI-LUG-20261007'));pass('free_event_filter');
 const invalid=await read('/api/v1/events?radius_km=300');assert.equal(invalid.status,400);pass('invalid_filter_rejected');
 assert.equal((await read('/api/v1/operator/events?status=CANDIDATE_UNVERIFIED')).status,401);pass('operator_auth_enforced');
 const envText=await fs.readFile('.env.local','utf8');const token=envText.match(/^RADAR_OPERATOR_TOKEN=(.+)$/m)[1];const response=await fetch(root+'/api/v1/operator/events?status=CANDIDATE_UNVERIFIED',{headers:{Authorization:'Bearer '+token}});const candidates=await response.json();assert.equal(response.status,200);assert.equal(candidates.total,3);pass('work_operator_reads_same_database_candidates');
 const page=await fetch(root+'/events/'+id);const html=await page.text();assert.equal(page.status,200);assert.ok(html.includes('Urgant Live'));assert.ok(html.includes('ticketone.it'));assert.ok(html.includes('urgant.live'));assert.ok(!html.includes(token));pass('detail_tickets_sources_no_secret_leak');
 const report={status:'PASS_LOCAL_STAGING_E2E',checks,public_records:49,mapped_records:all.value.mapped,website_database:'isolated PostgreSQL/PostGIS; no production cutover',browser_ui:'NOT_TESTED_BY_THIS_SCRIPT'};await fs.writeFile(directory+'/http-test-report.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}finally{for(const p of children)p.kill();}
