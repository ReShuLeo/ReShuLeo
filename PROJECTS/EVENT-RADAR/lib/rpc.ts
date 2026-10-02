import 'server-only';
export class BackendError extends Error {constructor(public status:number,public code:string,message:string){super(message);}}
export async function rpc<T>(name:string,args:Record<string,unknown>={},operator=false):Promise<T>{
 const url=process.env.SUPABASE_URL;const key=operator?process.env.SUPABASE_SERVICE_ROLE_KEY:process.env.SUPABASE_PUBLISHABLE_KEY;
 if(!url||!key)throw new BackendError(503,'DATABASE_NOT_CONNECTED','База мероприятий ещё не подключена.');
 const base=new URL(url);if(base.protocol!=='https:'&&base.hostname!=='127.0.0.1'&&base.hostname!=='localhost')throw new BackendError(503,'INVALID_BACKEND','Проверьте подключение базы.');
 const headers:Record<string,string>={'Content-Type':'application/json',apikey:key};
 // JWT legacy keys need Authorization; sb_publishable_/sb_secret_ use apikey only.
 if(!key.startsWith('sb_'))headers.Authorization=`Bearer ${key}`;
 let response:Response;
 try{response=await fetch(new URL(`/rest/v1/rpc/${name}`,base),{method:'POST',headers,body:JSON.stringify(args),cache:'no-store',signal:AbortSignal.timeout(10000)});}catch{throw new BackendError(503,'DATABASE_UNAVAILABLE','База временно недоступна.');}
 if(!response.ok)throw new BackendError(503,'DATABASE_QUERY_FAILED','Не удалось прочитать данные мероприятий.');
 return response.json() as Promise<T>;
}
