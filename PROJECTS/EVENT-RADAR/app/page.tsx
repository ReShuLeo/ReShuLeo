import Radar from '@/components/Radar';
import {rpc} from '@/lib/rpc';
import {todayInRome} from '@/lib/presentation';
import type {Facets,SearchResult} from '@/lib/types';
export const dynamic='force-dynamic';
export default async function Page(){
 const today=todayInRome();
 const [events,facets]=await Promise.allSettled([rpc<SearchResult>('radar_search',{p_filters:{from:today,limit:50,sort:'date'}}),rpc<Facets>('radar_facets')]);
 return <Radar today={today} initialResult={events.status==='fulfilled'?events.value:null} initialFacets={facets.status==='fulfilled'?facets.value:null} stagingNotice={process.env.NEXT_PUBLIC_STAGING_NOTICE||''}/>;
}
