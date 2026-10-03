'use client';
import {useEffect,useRef,useState} from 'react';
import {Scan,MapPin} from 'lucide-react';
import type {EventItem} from '@/lib/types';
import {eventDate,cityLabel} from '@/lib/presentation';
import 'leaflet/dist/leaflet.css';
export default function EventMap({events,location,onBounds}:{events:EventItem[];location:{lat:number;lng:number}|null;onBounds:(bbox:string)=>void}){
 const host=useRef<HTMLDivElement>(null);const mapRef=useRef<import('leaflet').Map|null>(null);const layer=useRef<import('leaflet').LayerGroup|null>(null);const fitted=useRef(false);const located=useRef('');
 const [failed,setFailed]=useState(false);const [ready,setReady]=useState(false);
 useEffect(()=>{let cancelled=false;import('leaflet').then(L=>{if(cancelled||!host.current)return;const map=L.map(host.current,{zoomControl:false}).setView([46.1,9.05],7);L.control.zoom({position:'bottomright'}).addTo(map);mapRef.current=map;layer.current=L.layerGroup().addTo(map);L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',maxZoom:19}).addTo(map);map.invalidateSize();setReady(true);}).catch(()=>setFailed(true));return()=>{cancelled=true;mapRef.current?.remove();mapRef.current=null;layer.current=null;};},[]);
 useEffect(()=>{if(!ready)return;let cancelled=false;import('leaflet').then(L=>{if(cancelled)return;const map=mapRef.current,group=layer.current;if(!map||!group)return;group.clearLayers();const clusters=new Map<string,EventItem[]>();
 for(const e of events){if(e.latitude===null||e.longitude===null||e.geocoding_status!=='VERIFIED')continue;const key=e.latitude.toFixed(6)+','+e.longitude.toFixed(6);clusters.set(key,[...(clusters.get(key)||[]),e]);}
 const points:import('leaflet').LatLngTuple[]=[];
 for(const list of clusters.values()){const first=list[0];const point:import('leaflet').LatLngTuple=[first.latitude!,first.longitude!];points.push(point);const content=document.createElement('div');for(const e of list){const link=document.createElement('a');link.href='/events/'+e.occurrence_id;link.textContent=e.title;content.append(link);const date=document.createElement('p');date.textContent=eventDate(e)+' · '+cityLabel(e.city);content.append(date);}const icon=L.divIcon({className:'',html:'<div class="map-marker"><span>'+list.length+'</span></div>',iconSize:[34,34],iconAnchor:[17,34],popupAnchor:[0,-35]});L.marker(point,{icon,alt:cityLabel(first.city)+': '+list.length+' событий'}).bindPopup(content,{maxWidth:270}).addTo(group);}
 const locationKey=location?`${location.lat},${location.lng}`:'';if(location){L.circleMarker([location.lat,location.lng],{radius:7,color:'#fff',weight:3,fillColor:'#376ae5',fillOpacity:1}).bindPopup('Ваше местоположение').addTo(group);if(located.current!==locationKey)map.setView([location.lat,location.lng],11);}else if(!fitted.current&&points.length){map.fitBounds(L.latLngBounds(points),{padding:[45,65],maxZoom:11});fitted.current=true;}located.current=locationKey;
 });return()=>{cancelled=true;};},[events,location,ready]);
 return <div className="map-shell"><div ref={host} className="map-canvas" aria-label="Карта мероприятий"/>{failed&&<div className="map-message">Карта не загрузилась. События доступны в списке.</div>}<button className="bounds-button" disabled={!ready} onClick={()=>{const b=mapRef.current?.getBounds();if(b)onBounds([b.getWest(),b.getSouth(),b.getEast(),b.getNorth()].join(','));}}><Scan size={16}/>Искать в этой области</button><p className="map-caption"><MapPin size={11}/> Только проверенные координаты</p></div>;
}
