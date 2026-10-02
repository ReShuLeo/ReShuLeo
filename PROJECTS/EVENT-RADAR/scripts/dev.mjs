import {spawn} from 'node:child_process';import {createRequire} from 'node:module';import {existsSync} from 'node:fs';
const require=createRequire(import.meta.url);require('@next/env').loadEnvConfig(process.cwd(),true);
// Accept the supervised preview flags without changing the production Next.js stack.
const args=process.argv.slice(2).filter(v=>v!=='--strictPort').map(v=>v==='--host'?'--hostname':v);
if(!args.includes('--hostname'))args.push('--hostname','0.0.0.0');
let staging;
const stagingDirectory=process.env.RADAR_STAGING_DIRECTORY;
if(stagingDirectory){
 if(process.env.NODE_ENV==='production')throw new Error('Staging adapter prohibited in production');
 if(!existsSync(stagingDirectory+'/import.sql'))throw new Error('Missing explicit staging snapshot');
 staging=spawn(process.execPath,['scripts/staging_api.mjs',stagingDirectory],{stdio:['ignore','pipe','inherit']});
 await new Promise((resolve,reject)=>{staging.stdout.on('data',chunk=>{process.stdout.write(chunk);if(chunk.toString().includes('adapter ready'))resolve();});staging.on('exit',code=>reject(new Error('Staging adapter exited: '+code)));});
 require('@next/env').loadEnvConfig(process.cwd(),true,console,true);
}
const server=spawn(process.execPath,['node_modules/next/dist/bin/next','dev',...args],{stdio:'inherit',env:{...process.env,NEXT_TELEMETRY_DISABLED:'1'}});
function close(){server.kill();staging?.kill();}process.on('SIGTERM',close);process.on('SIGINT',close);server.on('exit',code=>{staging?.kill();process.exit(code||0);});
