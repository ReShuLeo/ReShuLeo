import pg from 'pg';import fs from 'node:fs/promises';import {createHash} from 'node:crypto';
if(process.env.CONFIRM_TARGET!=='EVENT_RADAR_STAGING')throw new Error('Set CONFIRM_TARGET=EVENT_RADAR_STAGING after verifying the separate staging project');
if(!process.env.DATABASE_URL)throw new Error('DATABASE_URL required; use a secret manager');
const client=new pg.Client({connectionString:process.env.DATABASE_URL});await client.connect();
try{
 await client.query("create schema if not exists radar_admin;revoke all on schema radar_admin from public;create table if not exists radar_admin.migration_ledger(version text primary key,sha256 text not null,applied_at timestamptz not null default now())");
 const versions=(await client.query('select version,sha256 from radar_admin.migration_ledger')).rows;
 for(const file of (await fs.readdir('supabase/migrations')).filter(f=>f.endsWith('.sql')).sort()){
  const sql=await fs.readFile('supabase/migrations/'+file,'utf8');const hash=createHash('sha256').update(sql).digest('hex');const prior=versions.find(r=>r.version===file);
  if(prior){if(prior.sha256!==hash)throw new Error('Applied migration changed:'+file);continue;}
  await client.query('begin');try{await client.query(sql.replace(/^begin;$/gm,'').replace(/^commit;$/gm,''));await client.query('insert into radar_admin.migration_ledger(version,sha256) values($1,$2)',[file,hash]);await client.query('commit');}catch(e){await client.query('rollback');throw e;}console.log('APPLIED',file);
 }
}finally{await client.end();}
