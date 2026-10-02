import {ArrowUpRight,BusFront,ChevronDown,Clock,MapPin} from 'lucide-react'
import {routeCode} from './route-labels'
import type {BusRoute} from '../data/catalog'
import {type Locale,t} from '../i18n'

export function RouteOverview({route,locale,onShowStops}:{route:BusRoute;locale:Locale;onShowStops:()=>void}){
 const en=locale==='en'
 const operator=en?(route.operatorEn||t(route.operator,locale)):route.operator
 const origin=en?(route.originEn||t(route.origin,locale)):route.origin
 const destination=en?(route.destinationEn||t(route.destination,locale)):route.destination
 const duration=route.duration&&route.duration!=='公式時刻表を確認'?t(route.duration,locale):''
 const guide=route.routeOfficial||route.official
 const date=route.validUntil?.replace(/^(\d{4})-?(\d{2})-?(\d{2})$/,'$1/$2/$3')
 const geometry=route.geometryQuality==='GTFS shapes'?(en?'GTFS route geometry':'GTFSの経路データ'):route.geometryQuality==='停留所を結ぶ概略線'?(en?'Approximate line connecting stops':'停留所を結ぶ概略線'):route.geometryQuality
 return <section className="route-overview" aria-label={en?'Route and operator information':'路線と運行会社の情報'}>
  <div className="route-operator"><span className="operator-symbol"><BusFront size={19}/></span><div><span className="fact-label">{en?'Operated by':'運行会社'}</span><strong>{operator}</strong></div></div>
  <div className="route-journey"><span className="fact-label">{en?'Displayed journey':'表示している区間'}</span><ol className="journey-endpoints"><li><span>{en?'From':'出発'}</span><strong>{origin}</strong></li><li><span>{en?'To':'到着'}</span><strong>{destination}</strong></li></ol>
   {route.stops.length>0?<><p className="journey-note">{en?'This is a representative trip. Stops and direction may vary by service.':'代表便の区間です。便や方向によって経由する停留所が異なります。'}</p><button className="view-stops" onClick={onShowStops}><MapPin size={15}/>{en?`See all ${route.stops.length} stops`:`全${route.stops.length}停留所を見る`}<ChevronDown size={15}/></button></>:<p className="journey-note">{en?'Check the official guide for stops and the route map.':'線形データ未取得。停留所と路線図は公式の案内をご確認ください。'}</p>}
   {duration&&<p className="journey-duration"><Clock size={14}/>{en?'Travel time':'所要時間'}：{duration}</p>}
  </div>
  {guide&&<div className="operation-guide"><a className="official operation-link" href={guide} target="_blank" rel="noreferrer"><span>{en?'Check the official website':route.routeOfficial||route.id.startsWith('featured:')?'公式の路線・運行案内':'運行会社の公式サイト'}</span><ArrowUpRight size={17}/></a>{route.routeOfficial&&route.operatorOfficial&&route.routeOfficial!==route.operatorOfficial&&<a className="operator-site" href={route.operatorOfficial} target="_blank" rel="noreferrer">{en?'Operator website':'運行会社の公式サイト'}<ArrowUpRight size={13}/></a>}<p>{en?'Check timetables, fares and operating days before travelling.':'時刻表・運賃・運行日を、乗車前にご確認ください。'}</p></div>}
  <details className="route-data"><summary>{en?'Route data and sources':'路線データと出典'}</summary><dl>{route.routeShortName&&!routeCode(route)&&route.routeShortName!==route.name&&<div><dt>{en?'Short name':'通称・略称'}</dt><dd>{route.routeShortName}</dd></div>}<div><dt>{en?'Source':'情報源'}</dt><dd>{route.id.startsWith('featured:')?(en?'Reviewed official information':'公式情報を参照した編集情報'):'GTFS'}</dd></div>{geometry&&<div><dt>{en?'Map geometry':'地図の線'}</dt><dd>{geometry}</dd></div>}{date&&<div><dt>{en?'Data valid until':'データ有効期限'}</dt><dd>{date}</dd></div>}{route.dataUpdatedAt&&<div><dt>{en?'Data version':'データ版'}</dt><dd>{route.dataUpdatedAt}</dd></div>}{route.dataLicense&&<div><dt>{en?'Data license':'利用条件'}</dt><dd>{route.dataLicense}</dd></div>}</dl>{route.sourceUrl&&<a href={route.sourceUrl} target="_blank" rel="noreferrer">{en?'Original route data':'路線データの原本'}<ArrowUpRight size={13}/></a>}<p>{en?'Walking times are straight-line estimates. Entrances and walking routes are unverified.':'徒歩時間は直線距離からの推定です。施設入口と実際の徒歩経路は未確認です。'}</p></details>
 </section>
}
