import {rpc} from '@/lib/rpc';import {failure} from '@/lib/http';
export async function GET(){try{return Response.json(await rpc('radar_facets'),{headers:{'Cache-Control':'no-store'}});}catch(e){return failure(e);}}
