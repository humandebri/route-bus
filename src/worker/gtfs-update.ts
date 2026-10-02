import {WorkflowEntrypoint,type WorkflowEvent,type WorkflowStep} from 'cloudflare:workers'
export type FeedJob={id:string;url:string;license:string}
export type UpdateEnv={DB:D1Database;MAP_DATA:R2Bucket;GTFS_QUEUE:Queue<FeedJob>;GTFS_UPDATE:Workflow}
type Feed={organization_id:string;feed_id:string;feed_license:string;feed_is_discontinued:boolean;latest_feed_start_date:string;latest_feed_end_date:string}
export class GtfsUpdateWorkflow extends WorkflowEntrypoint<UpdateEnv>{
 async run(_event:WorkflowEvent<unknown>,step:WorkflowStep){
  const feeds=await step.do('fetch-public-registry',async()=>{
   const response=await fetch('https://api.gtfs-data.jp/v2/feeds')
   if(!response.ok)throw new Error(`GTFS registry HTTP ${response.status}`)
   const registry=await response.json() as {body:Feed[]};const today=new Date().toISOString().slice(0,10)
   return registry.body.filter(f=>!f.feed_is_discontinued&&/^CC\s*(BY\s*\d+(?:\.\d+)?(?:\s+JP)?|0(?:\s+\d+(?:\.\d+)?)?)$/i.test(f.feed_license)&&(!f.latest_feed_end_date||f.latest_feed_end_date>=today)&&(!f.latest_feed_start_date||f.latest_feed_start_date<=today)).map(f=>({id:`${f.organization_id}__${f.feed_id}`,url:`https://api.gtfs-data.jp/v2/organizations/${encodeURIComponent(f.organization_id)}/feeds/${encodeURIComponent(f.feed_id)}/files/feed.zip?rid=current`,license:f.feed_license}))
  })
  for(let start=0;start<feeds.length;start+=100){const batch=feeds.slice(start,start+100);await step.do(`queue-feeds-${start}`,()=>this.env.GTFS_QUEUE.sendBatch(batch.map(body=>({body}))))}
  return {queued:feeds.length}
 }
}
export async function archiveFeed(job:FeedJob,env:UpdateEnv){
 const url=new URL(job.url)
 if(url.origin!=='https://api.gtfs-data.jp'||!url.pathname.startsWith('/v2/organizations/')||!/^CC\s*(BY\s*\d+(?:\.\d+)?(?:\s+JP)?|0(?:\s+\d+(?:\.\d+)?)?)$/i.test(job.license)||! /^[a-zA-Z0-9_-]+$/.test(job.id))throw new Error('Invalid feed source')
 const prior=await env.DB.prepare('SELECT etag FROM gtfs_sources WHERE id=?').bind(job.id).first<{etag:string|null}>()
 const response=await fetch(url,{headers:prior?.etag?{'If-None-Match':prior.etag}:{}})
 if(response.status===304)return
 if(!response.ok||!response.body)throw new Error(`Feed HTTP ${response.status}`)
 const length=Number(response.headers.get('Content-Length')||0)
 if(length>50_000_000){await response.body.cancel();throw new Error('Archive exceeds 50MB limit')}
 let total=0
 const bounded=response.body.pipeThrough(new TransformStream<Uint8Array,Uint8Array>({transform(chunk,controller){total+=chunk.byteLength;if(total>50_000_000)throw new Error('Archive exceeds 50MB limit');controller.enqueue(chunk)}}))
 const importId=crypto.randomUUID();const key=`gtfs/sources/${job.id}/${importId}.zip`
 await env.MAP_DATA.put(key,bounded,{httpMetadata:{contentType:'application/zip'},customMetadata:{license:job.license,source:job.url}})
 await env.DB.batch([
  env.DB.prepare('INSERT INTO gtfs_sources(id,url,license,etag,updated_at) VALUES (?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET url=excluded.url,license=excluded.license,etag=excluded.etag,updated_at=excluded.updated_at').bind(job.id,job.url,job.license,response.headers.get('ETag'),new Date().toISOString()),
  env.DB.prepare('INSERT INTO gtfs_imports(id,source_id,status,original_key) VALUES (?,?,?,?)').bind(importId,job.id,'archived-awaiting-build',key)
 ])
}
