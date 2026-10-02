import {readFileSync} from 'node:fs'
import {test,expect} from '@playwright/test'
test('全国データの地図と実路線検索・詳細が動作する',async({page,request})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message))
 await page.setViewportSize({width:1440,height:900});await page.goto('/')
 await expect(page.locator('.intro h1')).toBeVisible()
 await expect(page.locator('.map-canvas canvas')).toBeVisible();await expect(page.locator('.map-loading')).toHaveCount(0,{timeout:30000});await page.waitForLoadState('networkidle')
 const version=JSON.parse(readFileSync('src/data/map-version.json','utf8'));const range=await request.get('/'+version.routeKey,{headers:{Range:'bytes=0-126'}});expect(range.status()).toBe(206);expect((await range.body()).length).toBe(127)
 await page.screenshot({path:'/private/tmp/bus-desktop.png'})
 await page.getByRole('button',{name:'写真あり',exact:true}).click();await expect(page.locator('.route-card').first()).toBeVisible();const targetName='赤碕線';
 await page.getByRole('textbox',{name:'路線・場所を検索'}).fill(targetName)
 await expect(page.locator('.route-card').first()).toBeVisible()
 await expect(page.locator('.route-card').first()).toContainText(targetName)
 await page.locator('.route-card').first().click()
 await expect(page).toHaveURL(/\/routes\//)
 const id=new URL(page.url()).pathname.split('/').pop();const detail=await request.get(`/api/routes/${id}`);expect(detail.status()).toBe(200);expect((await detail.json()).spots.length).toBeGreaterThan(0)
 const excluded=JSON.parse(readFileSync('build/collected/catalog.json','utf8')).find((r:{tourismEligible?:boolean})=>r.tourismEligible===false);expect((await request.get(`/api/routes/${encodeURIComponent(excluded.id)}`)).status()).toBe(404)
 await expect(page.getByRole('heading',{name:'バス停周辺の観光スポット'})).toBeVisible()
 await page.getByRole('button',{name:'バス停',exact:true}).click();await expect(page.locator('.stop-row').first()).toBeVisible()
 await page.getByRole('button',{name:'車窓',exact:true}).click();await expect(page.getByText('この路線の車窓スポットは、まだ調査中です。')).toBeVisible()
 await expect(page.locator('.map-loading')).toHaveCount(0,{timeout:30000});await page.waitForLoadState('networkidle');await page.screenshot({path:'/private/tmp/bus-route-desktop.png'})
 await page.reload();await expect(page.getByRole('heading',{name:'バス停周辺の観光スポット'})).toBeVisible()
 await page.setViewportSize({width:390,height:844});await expect(page.locator('.map-loading')).toHaveCount(0,{timeout:30000});await page.waitForLoadState('networkidle');await page.screenshot({path:'/private/tmp/bus-route-mobile.png'})
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true)
 await page.getByRole('button',{name:'路線を探す',exact:true}).click();await expect(page).toHaveURL('/');await expect(page.locator('.intro h1')).toBeVisible();await page.waitForLoadState('networkidle');await expect(page.locator('.map-loading')).toHaveCount(0,{timeout:30000})
 await page.getByRole('button',{name:'パネルを広げる'}).click();await expect(page.locator('.sidebar')).toHaveClass(/expanded/);await page.getByRole('button',{name:'パネルを縮める'}).click();await expect(page.locator('.sidebar')).not.toHaveClass(/expanded/);await page.getByRole('button',{name:'パネルを広げる'}).click();await expect(page.locator('.sidebar')).toHaveClass(/expanded/)
 await expect.poll(()=>page.locator('.map-canvas').evaluate(el=>Math.abs(el.clientHeight-(el.querySelector('canvas')?.clientHeight??0)))).toBeLessThan(2);await page.screenshot({path:'/private/tmp/bus-mobile.png'});expect(errors).toEqual([]);
 await page.getByRole('button',{name:'すべて',exact:true}).click();await page.getByRole('textbox',{name:'路線・場所を検索'}).fill('八木新宮');await expect(page.locator('.route-card')).toHaveCount(1);await expect(page.locator('.route-card').first()).toContainText('八木新宮');await page.locator('.route-card').first().click();await expect(page.locator('.journey-note')).toContainText('線形データ未取得');await page.goto('/sources');await expect(page.getByRole('heading',{name:'表示する路線の基準'})).toBeVisible();await expect(page.getByRole('heading',{name:'写真の作者とライセンス'})).toBeVisible()
})

test('近傍スポット未登録の選定路線と別名検索',async({page,request})=>{
 const route=await request.get('/api/routes/'+encodeURIComponent('nemurokotsu__nemurobus:納沙布線_B'));expect(route.status()).toBe(200);expect((await route.json()).featured).toBe(true)
 await page.goto('/');await expect(page.locator('.map-loading')).toHaveCount(0,{timeout:30000});await page.waitForLoadState('networkidle');await page.getByRole('textbox',{name:'路線・場所を検索'}).fill('九州横断');await expect(page.locator('.route-card')).toHaveCount(4);await expect(page.locator('.route-card h3').first()).toHaveText('九州横断バス')
 const unmapped=await request.get('/api/routes/'+encodeURIComponent('featured:shiretoko'));expect(unmapped.status()).toBe(200);expect((await unmapped.json()).stops).toEqual([])
})

test('英語SSR・検索・言語切替で路線を保持する',async({page,request})=>{
 const html=await request.get('/?lang=en');expect(html.status()).toBe(200);const body=await html.text();expect(body).toContain('<html lang="en"');expect(body).toContain('Where will a bus take you?')
 await page.goto('/?lang=en');await expect(page.locator('.map-loading')).toHaveCount(0,{timeout:30000});await page.waitForLoadState('networkidle');await expect(page.getByRole('heading',{name:'Your next day off. Where will a bus take you?'})).toBeVisible()
 await page.getByRole('textbox',{name:'Search routes and places'}).fill('Yagi–Shingu');await expect(page.locator('.route-card')).toHaveCount(1);await page.locator('.route-card').first().click();await expect(page).toHaveURL(/\/routes\/.+\?lang=en/);await expect(page.getByRole('heading',{name:'Yagi–Shingu Express Bus',exact:true})).toBeVisible();await page.getByRole('button',{name:'Bus stops',exact:true}).click();await expect(page.getByText('Stop and route geometry data are not available yet.',{exact:false})).toBeVisible()
 const path=new URL(page.url()).pathname;await page.getByRole('link',{name:'日本語',exact:true}).click();await expect(page).toHaveURL(new RegExp(path));await expect(page.locator('html')).toHaveAttribute('lang','ja');await expect(page.getByRole('heading',{name:'八木新宮特急バス',exact:true})).toBeVisible();await page.getByRole('link',{name:'English',exact:true}).click();await expect(page.locator('html')).toHaveAttribute('lang','en')
 await expect(page.locator('.map-loading')).toHaveCount(0,{timeout:30000});await page.waitForLoadState('networkidle');await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);await page.screenshot({path:'/private/tmp/bus-english-mobile.png'})
 await page.goto('/sources?lang=en');await expect(page.getByRole('heading',{name:'How we choose routes'})).toBeVisible();await expect(page.getByRole('heading',{name:'Photo authors & licenses'})).toBeVisible();await page.getByRole('link',{name:'← Back to the map'}).click();await expect(page).toHaveURL(/\?lang=en/)
})
