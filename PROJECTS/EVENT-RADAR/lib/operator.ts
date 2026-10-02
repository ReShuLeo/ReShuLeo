import 'server-only';
import {timingSafeEqual} from 'node:crypto';
import {BackendError} from './rpc';
export function requireOperator(req:Request){
 const configured=process.env.RADAR_OPERATOR_TOKEN;const incoming=req.headers.get('authorization')?.replace(/^Bearer /,'');
 if(!configured)throw new BackendError(503,'OPERATOR_NOT_CONFIGURED','Operator access unavailable');
 if(!incoming||Buffer.byteLength(incoming)!==Buffer.byteLength(configured)||!timingSafeEqual(Buffer.from(incoming),Buffer.from(configured)))throw new BackendError(401,'UNAUTHORIZED','Operator authorization required');
}
