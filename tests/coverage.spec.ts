import {test,expect} from '@playwright/test'
import {readFileSync} from 'node:fs'
test('全国の収集状況と追加GTFSの根拠を表示する',async({page,request})=>{
 const coverage=await (await request.get('/data/coverage.json')).json()
 expect(coverage.prefectures).toHaveLength(47)
 expect(new Set(coverage.prefectures.map((r:{prefectureCode:number})=>r.prefectureCode)).size).toBe(47)
 for(const name of ['福井県','鳥取県'])expect(coverage.prefectures.find((r:{prefecture:string})=>r.prefecture===name).gtfsRoutes).toBeGreaterThan(0)
 const places=await (await request.get('/data/osm-spots.json')).json()
 expect(places.license).toBe('ODbL 1.0');expect(places.spots.length).toBeGreaterThan(0)
 const detail=await request.get(`/api/spots/${places.spots[0].id}`);expect(detail.status()).toBe(200);expect((await detail.json()).dataLicense).toBe('ODbL 1.0')
 expect((await request.get('/api/spots/not-a-real-spot')).status()).toBe(404)
 const points=await (await request.get('/data/spot-points.geojson')).json();expect(points.features[0].properties.description).toBeUndefined();const summary=await (await request.get('/data/collection-summary.json')).json();expect(points.features.length).toBe(summary.tourismSpots)
 const catalog=JSON.parse(readFileSync('build/published/catalog.json','utf8'))
 for(const route of catalog.filter((r:{sourceId?:string})=>r.sourceId?.startsWith('extra-')))expect(!route.validUntil||route.validUntil.replaceAll('-','')>=new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'}).replaceAll('-','')).toBe(true)
 await page.goto('/sources?lang=en');await expect(page.getByRole('heading',{name:'Coverage by prefecture'})).toBeVisible()
 const table=page.locator('section').filter({has:page.getByRole('heading',{name:'Coverage by prefecture'})}).locator('tbody tr');await expect(table).toHaveCount(47)
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
 await expect(page.getByRole('link',{name:'Combined places database',exact:true})).toHaveAttribute('href','/data/spots.geojson')
})
