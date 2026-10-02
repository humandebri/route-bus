import type {Spot} from '../data/catalog'
type SymbolKind='place'|'museum'|'view'|'art'|'zoo'|'aquarium'|'park'
const symbols:Record<SymbolKind,{color:string;paths:string[]}>= {
 place:{color:'#9f532d',paths:['M15 12a3 3 0 1 0-6 0 3 3 0 0 0 6 0']},
 museum:{color:'#685582',paths:['M3 9h18L12 3 3 9Z','M5 10v9m5-9v9m4-9v9m5-9v9M3 21h18']},
 view:{color:'#35694e',paths:['m3 20 7-13 5 8 3-5 4 10H3Z','m7 12 3 3 2-3']},
 art:{color:'#685582',paths:['M12 3a9 9 0 1 0 0 18h1a2 2 0 0 0 0-4 2 2 0 0 1 0-4h3a5 5 0 0 0 5-5c0-3-4-5-9-5Z','M7 9h.01M10 6h.01M15 6h.01M18 9h.01']},
 zoo:{color:'#35694e',paths:['M8 14c-4 4-3 7 0 7 2 0 2-1 4-1s2 1 4 1c3 0 4-3 0-7-2-2-6-2-8 0Z','M8 7a2 3 0 1 0-4 0 2 3 0 0 0 4 0M14 5a2 3 0 1 0-4 0 2 3 0 0 0 4 0M20 7a2 3 0 1 0-4 0 2 3 0 0 0 4 0']},
 aquarium:{color:'#286e86',paths:['M18 12c-4-7-10-7-15 0 5 7 11 7 15 0Zm0 0 4-5v10l-4-5Z','M8 10h.01M12 6l-2-3M12 18l-2 3']},
 park:{color:'#685582',paths:['m12 3 3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1 3-6Z']}
}
export function spotKind(spot:Pick<Spot,'category'|'scenic'>):SymbolKind{
 if(spot.scenic||/展望|景勝/.test(spot.category))return 'view'
 if(/博物館/.test(spot.category))return 'museum'
 if(/美術館|ギャラリー/.test(spot.category))return 'art'
 if(/動物園/.test(spot.category))return 'zoo'
 if(/水族館/.test(spot.category))return 'aquarium'
 if(/テーマパーク/.test(spot.category))return 'park'
 return 'place'
}
export function spotColor(spot:Pick<Spot,'category'|'scenic'>){return symbols[spotKind(spot)].color}
export function SpotIcon({spot,size=18}:{spot:Pick<Spot,'category'|'scenic'>;size?:number}){
 return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{symbols[spotKind(spot)].paths.map((d,i)=><path d={d} key={i}/>)}</svg>
}
// Only constant symbol paths and colors enter this SVG, never place names or source text.
export function spotPinSvg(kind:SymbolKind='place'):string{
 const symbol=symbols[kind]
 return `<svg xmlns="http://www.w3.org/2000/svg" width="40" height="48" viewBox="0 0 40 48"><path d="M20 46C17 41 3 29 3 20a17 17 0 1 1 34 0c0 9-14 21-17 26Z" fill="${symbol.color}" stroke="white" stroke-width="2.5"/><svg x="9" y="9" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${symbol.paths.map(d=>`<path d="${d}"/>`).join('')}</svg></svg>`
}
