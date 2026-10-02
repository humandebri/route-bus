import {getPlatformProxy} from 'wrangler'
import {readFileSync} from 'node:fs'
const manifest=JSON.parse(readFileSync('data/sources/webp-manifest.json','utf8'))
const overrides=JSON.parse(readFileSync('data/spot-photo-overrides.json','utf8'))
const proxy=await getPlatformProxy({persist:{path:'.wrangler/state/v3'}})
try{
 for(const file of manifest.filter(r=>r.file))await proxy.env.MAP_DATA.put(file.key,readFileSync(file.file),{httpMetadata:{contentType:'image/webp'}})
 for(const [id,photo] of Object.entries(overrides))await proxy.env.DB.prepare("UPDATE spots SET document=json_set(document,'$.photo',?,'$.photoOriginal',?) WHERE id=?").bind(photo.photo,photo.photo_original,id).run()
 console.log('Local R2 and D1 updated:',Object.keys(overrides).length)
}finally{await proxy.dispose()}
