import {BackendError} from './rpc';
import {ZodError} from 'zod';
export function failure(error:unknown){
 if(error instanceof BackendError)return Response.json({error:error.code,message:error.message},{status:error.status,headers:{'Cache-Control':'no-store'}});
 if(error instanceof ZodError||error instanceof Error&&error.message==='Status filter requires operator access')return Response.json({error:'INVALID_FILTER',message:'Проверьте параметры поиска.'},{status:400});
 return Response.json({error:'REQUEST_FAILED',message:'Не удалось выполнить запрос.'},{status:500});
}
