export type Named = {id: string; name: string; slug?: string; role?: string};
export type EventItem = {
 occurrence_id: string;event_id: string;legacy_id: string;title: string;description: string|null;series: string|null;
 starts_on: string|null;ends_on: string|null;start_local: string|null;end_local: string|null;doors_local: string|null;timezone: string|null;
 city: string|null;country_code: string|null;venue: string|null;venue_id: string|null;normalized_address: string|null;original_address: string|null;
 latitude: number|null;longitude: number|null;geocoding_status: string;distance_km: number|null;
 status:string;last_verified:string|null;first_discovered:string|null;availability:string|null;guest_list:string|null;membership:string|null;
 artists:Named[];organizers:Named[];categories:Named[];languages:string[];
 tickets:{provider:string|null;url:string;price_min:number|null;price_max:number|null;currency:string|null;last_checked:string|null}[];
 sources:{name:string;url:string;verified_at:string|null;evidence_kind:string}[];
};
export type SearchResult = {items:EventItem[];total:number;mapped:number;database:string;generated_at:string};
export type Facets = {cities:string[];categories:{slug:string;name:string}[];languages:{code:string;name:string}[];artists:string[];venues:string[];organizers:string[]};
