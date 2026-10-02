import {test,expect} from '@playwright/test'
import {readFileSync} from 'node:fs'
const read=(path:string)=>JSON.parse(readFileSync(path,'utf8'))
test('公開データの件数・ピン・期限・写真・R2タイルが一致する',async({request})=>{
 const catalog=read('build/published/catalog.json')
 const places=read('build/published/spots.json')
 const summary=await (await request.get('/data/collection-summary.json')).json()
 expect(summary.tourismRoutes).toBe(catalog.length)
 expect(summary.tourismSpots).toBe(places.length)
 const points=await (await request.get('/data/spot-points.geojson')).json()
 expect(points.features.map((f:any)=>f.properties.id).sort()).toEqual(places.map((p:any)=>p.id).sort())
 const today=new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'}).replaceAll('-','')
 const expired=read('build/collected/catalog.json').filter((r:any)=>r.validUntil&&r.validUntil.replaceAll('-','')<today)
 for(const route of expired.slice(0,3))expect((await request.get('/api/routes/'+encodeURIComponent(route.id))).status()).toBe(404)
 const photo=places.find((p:any)=>p.photo.startsWith('/photos/commons-'))
 expect(photo).toBeDefined()
 const detail=await (await request.get('/api/spots/'+encodeURIComponent(photo.id))).json()
 expect(detail.photo).toBe(photo.photo);expect(detail.credit).toBe(photo.photo_credit)
 for(const path of [detail.photo,detail.photo.replace('-thumb.webp','-original.webp')]){
  const image=await request.get(path);expect(image.status()).toBe(200);expect(image.headers()['content-type']).toBe('image/webp')
 }
 const version=read('src/data/map-version.json')
 const tile=await request.get('/'+version.routeKey,{headers:{Range:'bytes=0-126'}})
 expect(tile.status()).toBe(206);expect((await tile.body()).length).toBe(127)
 const published=new Set(catalog.map((r:any)=>r.id))
 const withheld=read('build/collected/catalog.json').find((r:any)=>!published.has(r.id)&&r.spots.length&&!r.validUntil?.startsWith('202609'))
 expect((await request.get('/api/routes/'+encodeURIComponent(withheld.id))).status()).toBe(404)
})
