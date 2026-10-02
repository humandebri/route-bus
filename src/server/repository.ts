import type {BusRoute} from '../data/catalog'
export function currentRouteSql(alias:string){
 return `((COALESCE(json_extract(${alias}.document,'$.validUntil'),'')='' OR REPLACE(json_extract(${alias}.document,'$.validUntil'),'-','')>=strftime('%Y%m%d','now','+9 hours')) AND (COALESCE(json_extract(${alias}.document,'$.validFrom'),'')='' OR REPLACE(json_extract(${alias}.document,'$.validFrom'),'-','')<=strftime('%Y%m%d','now','+9 hours')))`
}
export async function loadRoute(db:D1Database,id:string):Promise<BusRoute|null>{
 const row=await db.prepare(`SELECT document FROM routes WHERE id=? AND active=1 AND ${currentRouteSql("routes")} AND (EXISTS(SELECT 1 FROM route_spots WHERE route_id=routes.id) OR json_extract(document,'$.featured')=1)`).bind(id).first<{document:string}>();if(!row)return null
 const linked=await db.prepare('SELECT s.document,st.name AS stop,rs.walk_minutes,rs.access_confidence FROM route_spots rs JOIN spots s ON s.id=rs.spot_id JOIN stops st ON st.id=rs.stop_id WHERE rs.route_id=? ORDER BY rs.sequence,s.id').bind(id).all<{document:string;stop:string;walk_minutes:number;access_confidence:string}>()
 return {...JSON.parse(row.document),spots:linked.results.map(s=>({...JSON.parse(s.document),stop:s.stop,walk:s.walk_minutes,accessConfidence:s.access_confidence}))}
}
