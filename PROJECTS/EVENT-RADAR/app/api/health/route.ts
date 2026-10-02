import {rpc} from '@/lib/rpc';
export async function GET(){try{await rpc('radar_search',{p_filters:{limit:1}});return Response.json({status:'OK',database:'postgresql',checked_at:new Date().toISOString()},{headers:{'Cache-Control':'no-store'}});}catch{return Response.json({status:'DEGRADED',database:'NOT_LOADED'},{status:503,headers:{'Cache-Control':'no-store'}});}}
