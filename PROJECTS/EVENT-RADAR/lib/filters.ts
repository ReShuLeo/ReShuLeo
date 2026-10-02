import {z} from 'zod';
const number = (min:number,max:number)=>z.coerce.number().finite().min(min).max(max);
export const FilterSchema=z.object({
 q:z.string().max(200).optional(),from:z.iso.date().optional(),to:z.iso.date().optional(),
 city:z.string().max(200).optional(),category:z.string().max(120).optional(),language:z.string().max(30).optional(),
 venue:z.string().max(250).optional(),artist:z.string().max(250).optional(),organizer:z.string().max(250).optional(),
 lat:number(-90,90).optional(),lng:number(-180,180).optional(),radius_km:number(0.001,250).optional(),
 price_max:number(0,100000).optional(),currency:z.enum(['EUR','CHF','USD','GBP']).optional(),
 free:z.enum(['true','false']).transform(v=>v==='true').optional(),sort:z.enum(['date','distance','newest']).default('date'),
 limit:number(1,200).int().default(50),offset:number(0,100000).int().default(0),
 occurrence_id:z.uuid().optional(),discovered_since:z.iso.datetime({offset:true}).optional(),
 bbox:z.string().transform(s=>s.split(',').map(Number)).pipe(z.tuple([z.number().min(-180).max(180),z.number().min(-90).max(90),z.number().min(-180).max(180),z.number().min(-90).max(90)])).optional(),
 status:z.string().max(60).optional()
}).superRefine((f,ctx)=>{
 if((f.lat===undefined)!==(f.lng===undefined))ctx.addIssue({code:'custom',message:'Both coordinates required'});
 if((f.radius_km!==undefined||f.sort==='distance')&&f.lat===undefined)ctx.addIssue({code:'custom',message:'Location required'});
 if(f.from&&f.to&&f.from>f.to)ctx.addIssue({code:'custom',message:'Invalid date interval'});
 if(f.bbox&&(f.bbox[0]>=f.bbox[2]||f.bbox[1]>=f.bbox[3]))ctx.addIssue({code:'custom',message:'Invalid map bounds'});
 if(f.price_max!==undefined&&!f.currency)ctx.addIssue({code:'custom',message:'Choose a price currency'});
});
export function parseFilters(params:URLSearchParams,operator=false){
 const raw=Object.fromEntries([...params].filter(([,v])=>v!==''));
 if(!operator&&raw.status)throw new Error('Status filter requires operator access');
 return FilterSchema.parse(raw);
}
export function safeUrl(raw:string|undefined|null){try{const u=new URL(raw||'');return ['https:','http:'].includes(u.protocol)?u.href:null;}catch{return null;}}
