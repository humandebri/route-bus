import {loadRoute,currentRouteSql} from './server/repository'
import handler from '@tanstack/react-start/server-entry'
import {archiveFeed,type FeedJob,type UpdateEnv} from './worker/gtfs-update'
export {GtfsUpdateWorkflow} from './worker/gtfs-update'
type Env=UpdateEnv
export default {
 async fetch(request:Request,env:Env,ctx:ExecutionContext){
  const url=new URL(request.url)
  if(url.pathname.startsWith('/api/routes/')){
   const id=decodeURIComponent(url.pathname.split('/')[3]??'')
   const route=await loadRoute(env.DB,id)
   return Response.json(route??{error:'路線が見つかりません'}, {status:route?200:404,headers:{'Cache-Control':route?'public, max-age=300, s-maxage=3600':'no-store'}})
  }
  if(url.pathname.startsWith('/api/spots/')){
   const id=decodeURIComponent(url.pathname.split('/')[3]??'')
   const row=await env.DB.prepare('SELECT document FROM spots WHERE id=?').bind(id).first<{document:string}>()
   if(!row)return Response.json({error:'Spot not found'},{status:404,headers:{'Cache-Control':'no-store'}})
   const routes=await env.DB.prepare(`SELECT r.id,r.name,r.document,st.name AS stop,rs.walk_minutes FROM route_spots rs JOIN routes r ON r.id=rs.route_id JOIN stops st ON st.id=rs.stop_id WHERE rs.spot_id=? AND r.active=1 AND ${currentRouteSql('r')} ORDER BY rs.walk_minutes,r.id LIMIT 12`).bind(id).all<{id:string;name:string;document:string;stop:string;walk_minutes:number}>()
   return Response.json({...JSON.parse(row.document),stop:routes.results[0]?.stop||'',walk:routes.results[0]?.walk_minutes??0,routes:routes.results.map(r=>({id:r.id,name:r.name,nameEn:JSON.parse(r.document).nameEn}))},{headers:{'Cache-Control':'public, max-age=300, s-maxage=3600'}})
  }
  if(url.pathname.startsWith('/photos/')){
   const key=url.pathname.slice(1)
   if(!/^photos\/(Q[0-9]+|municipal-[a-f0-9]{16}|commons-[a-f0-9]{16})-(thumb|original)\.(jpg|png|webp)$/.test(key))return new Response('Not found',{status:404})
   const object=await env.MAP_DATA.get(key)
   if(!object)return new Response('Not found',{status:404})
   const headers=new Headers({'Cache-Control':'public, max-age=86400'});object.writeHttpMetadata(headers);headers.set('ETag',object.httpEtag)
   return new Response(object.body,{headers})
  }
  if(url.pathname.startsWith('/maps/')){
   const key=url.pathname.slice(1)
   if(!/^maps\/[a-zA-Z0-9._-]+\.pmtiles$/.test(key))return new Response('Not found',{status:404})
   const object=await env.MAP_DATA.get(key,{range:request.headers,onlyIf:request.headers})
   if(!object)return new Response('Not found',{status:404})
   const headers=new Headers({'Accept-Ranges':'bytes','Cache-Control':'public, max-age=3600'})
   object.writeHttpMetadata(headers); headers.set('ETag',object.httpEtag)
   if(!('body' in object))return new Response(null,{status:request.headers.has('If-Match')||request.headers.has('If-Unmodified-Since')?412:304,headers})
   const range=object.range as {offset?:number;length?:number}|undefined
   if(range?.offset!==undefined&&range.length!==undefined){headers.set('Content-Range',`bytes ${range.offset}-${range.offset+range.length-1}/${object.size}`);headers.set('Content-Length',String(range.length))}
   return new Response(object.body,{status:range?206:200,headers})
  }
  return handler.fetch(request)
 },
 async scheduled(_event:ScheduledController,env:Env){await env.GTFS_UPDATE.create()},
 async queue(batch:MessageBatch<FeedJob>,env:Env){for(const message of batch.messages){try{await archiveFeed(message.body,env);message.ack()}catch(error){console.error('GTFS archive failed',message.body.id,error);message.retry()}}}
}
