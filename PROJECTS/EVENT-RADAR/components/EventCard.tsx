import Link from 'next/link';
import {MapPin,ArrowUpRight,ShieldCheck} from 'lucide-react';
import type {EventItem} from '@/lib/types';
import {categoryLabel,cityLabel,dateParts,eventDate,priceLabel,themeFor} from '@/lib/presentation';
import EventArtwork from './EventArtwork';
export {eventDate,priceLabel} from '@/lib/presentation';
export default function EventCard({event:e,index=0}:{event:EventItem;index?:number}){
 const category=categoryLabel(e.categories[0]?.name||'');const date=dateParts(e.starts_on);
 return <article className="event-card" style={{'--card-delay':`${Math.min(index,8)*35}ms`} as React.CSSProperties}>
 <Link href={`/events/${e.occurrence_id}`} className="card-link" aria-label={`${e.title}, ${eventDate(e)}, ${cityLabel(e.city)}`}>
 <div className="card-visual"><EventArtwork theme={themeFor(e.categories[0]?.name||'')}/><div className="date-badge"><strong>{date.day}</strong><span>{date.month}</span></div><span className="price-badge">{priceLabel(e)}</span></div>
 <div className="card-content"><div className="card-top"><span className="category">{category}</span>{e.languages.includes('ru')&&<span className="language">На русском</span>}</div><div className="card-title-row"><h3>{e.title}</h3><ArrowUpRight size={21} aria-hidden="true"/></div><p className="event-date">{eventDate(e)}</p><p className="place"><MapPin size={15} aria-hidden="true"/><span>{cityLabel(e.city)}</span>{e.distance_km!=null&&<span className="distance">{e.distance_km.toLocaleString('ru-RU',{maximumFractionDigits:1})} км</span>}</p><p className="venue">{e.venue||'Место уточняется'}</p><div className="card-bottom"><span className="verified"><ShieldCheck size={14} aria-hidden="true"/>Источник подтверждён</span><span className="card-more">Подробнее <ArrowUpRight size={14} aria-hidden="true"/></span></div>{e.membership&&<p className="restriction">Могут действовать условия входа</p>}</div></Link></article>;
}
