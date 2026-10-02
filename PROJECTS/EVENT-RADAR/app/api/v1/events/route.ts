import {parseFilters} from '@/lib/filters';import {rpc} from '@/lib/rpc';import {failure} from '@/lib/http';import type {SearchResult} from '@/lib/types';
export async function GET(req:Request){try{return Response.json(await rpc<SearchResult>('radar_search',{p_filters:parseFilters(new URL(req.url).searchParams)}),{headers:{'Cache-Control':'no-store'}});}catch(e){return failure(e);}}
