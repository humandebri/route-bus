import {useEffect,useState} from 'react'
import {ImageOff} from 'lucide-react'
export function Photo({src,alt,eager=false}:{src:string;alt:string;eager?:boolean}){
 const [failed,setFailed]=useState(false)
 useEffect(()=>setFailed(false),[src])
 return src&&!failed?<img src={src} srcSet={src.endsWith('-thumb.webp')?`${src} 640w, ${src.replace('-thumb.webp','-original.webp')} 1440w`:undefined} sizes="(max-width: 640px) calc(100vw - 44px), 390px" alt={alt} loading={eager?'eager':'lazy'} decoding="async" onError={()=>setFailed(true)}/>:<div className="photo-unavailable"><ImageOff size={22}/><span>{alt}</span></div>
}
