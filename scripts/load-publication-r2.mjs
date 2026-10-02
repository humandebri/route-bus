import {getPlatformProxy} from 'wrangler'
import {readFileSync} from 'node:fs'
const read = path => JSON.parse(readFileSync(path,'utf8'))
const spots=read('build/published/spots.json')
const ids=new Set(spots.filter(s=>s.photo).map(s=>s.id))
const files=read('data/sources/webp-manifest.json').filter(f=>f.file&&ids.has(f.id))
for(const record of read('data/sources/published-commons-downloads.json')){
 if(record.status==='downloaded-license-reviewed'&&ids.has(record.spotId)){
  for(const file of Object.values(record.files))files.push({...file,mime:'image/webp'})
 }
}
const keys=new Set(files.map(f=>'/'+f.key))
for(const spot of spots.filter(s=>s.photo))if(!keys.has(spot.photo))throw new Error(`Missing reviewed image for ${spot.id}`)
const version=read('build/published/map-version.json')
const proxy=await getPlatformProxy({persist:{path:'.wrangler/organized-preview/v3'}})
try{
 await proxy.env.MAP_DATA.put(version.routeKey,readFileSync('build/published/routes.pmtiles'),{httpMetadata:{contentType:'application/vnd.pmtiles'}})
 for(const file of process.argv.includes('--tiles-only')?[]:files)await proxy.env.MAP_DATA.put(file.key,readFileSync(file.file),{httpMetadata:{contentType:file.mime}})
 console.log(`Local R2: ${version.routeKey}; ${process.argv.includes('--tiles-only')?0:files.length} image files`)
}finally{await proxy.dispose()}
