import {test,expect} from '@playwright/test'
import {routeCode} from '../src/components/route-labels'
import type {BusRoute} from '../src/data/catalog'
const id='sankobus__sankobus:87_87580_1_20260813'
test('公式の番号と内部IDを区別する',()=>{
 const base={id:'provider:87',name:'阿蘇山上線'} as BusRoute
 expect(routeCode(base)).toBe('')
 expect(routeCode({...base,name:'8：阿蘇駅前→阿蘇山上ターミナル'})).toBe('8')
 expect(routeCode({...base,routeShortName:'A12'})).toBe('A12')
 for(const code of ['YKB3T','YKB-HLT','A12/B34','東12','１２－３']){
  expect(routeCode({...base,routeShortName:code})).toBe(code)
  expect(routeCode({...base,name:code+'：案内'})).toBe(code)
 }
 expect(routeCode({...base,routeShortName:'南北循環バス'})).toBe('')
 expect(routeCode({...base,routeShortName:'Airport Shuttle'})).toBe('')
})
test('公開データの英字を含む路線記号を表示する',async({page})=>{
 for(const [suffix,code] of [['02','YKB3T'],['03','YKB-HLT']]){
  await page.goto('/routes/'+encodeURIComponent('yanbaru-expressbus__yanbaru-express-bus:'+suffix))
  await expect(page.locator('.route-sign strong')).toHaveText(code)
 }
})
test('路線番号・運行会社・表示区間と停留所への導線を表示する',async({page})=>{
 await page.goto('/routes/'+encodeURIComponent(id))
 await expect(page.locator('.map-loading')).toHaveCount(0,{timeout:30000})
 await expect(page.locator('.route-sign strong')).toHaveText('8')
 await expect(page.locator('.route-operator')).toContainText('運行会社')
 await expect(page.locator('.route-operator strong')).toHaveText('九州産交バス')
 await expect(page.locator('.journey-endpoints li').first()).toContainText('阿蘇駅前')
 await expect(page.locator('.journey-endpoints li').last()).toContainText('阿蘇山上ターミナル')
 await expect(page.locator('.operation-link')).toHaveText('運行会社の公式サイト')
 await expect(page.locator('.operation-link')).toHaveAttribute('href','https://www.sankobus.jp/')
 await expect(page.locator('.route-data')).not.toHaveAttribute('open','')
 await page.locator('.route-data summary').click()
 await expect(page.locator('.route-data')).toContainText('2026/12/29')
 await page.getByRole('button',{name:'全6停留所を見る'}).click()
 await expect(page.getByRole('button',{name:'バス停',exact:true})).toHaveAttribute('aria-pressed','true')
 await expect(page.locator('.stop-row')).toHaveCount(6)
 await page.setViewportSize({width:390,height:844})
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
 await page.locator('.sidebar').evaluate(el=>el.scrollTop=0)
 await page.screenshot({path:'/private/tmp/route-bus-overview-mobile.png'})
 await page.goto('/routes/'+encodeURIComponent(id)+'?lang=en')
 await expect(page.locator('.map-loading')).toHaveCount(0,{timeout:30000})
 await expect(page.locator('.route-sign strong')).toHaveText('8')
 await expect(page.locator('.route-operator')).toContainText('Operated by')
 await expect(page.locator('.journey-endpoints li').first()).toContainText('Aso Sta.')
 await expect(page.getByRole('button',{name:'See all 6 stops'})).toBeVisible()
})
