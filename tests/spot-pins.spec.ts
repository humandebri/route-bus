import {test,expect,type Page} from '@playwright/test'
const route='sankobus__sankobus:87_87580_1_20260813'
// Wait for real marker movement and then 400 ms without further camera updates.
async function settledMarkers(page:Page,previous?:string){
 return page.evaluate(async previous=>{
  const snapshot=()=>JSON.stringify([...document.querySelectorAll<HTMLElement>('.spot-map-pin')].map(el=>[el.dataset.spotId,el.style.transform]))
  const deadline=performance.now()+10000
  let last=snapshot(),stableSince=performance.now(),moved=previous===undefined
  while(performance.now()<deadline){
   await new Promise<void>(resolve=>requestAnimationFrame(()=>resolve()))
   const current=snapshot()
   if(current!==last){last=current;stableSince=performance.now()}
   if(previous!==undefined&&current!==previous)moved=true
   if(moved&&performance.now()-stableSince>=400)return current
  }
  throw new Error('Map markers did not move and settle within 10 seconds')
 },previous)
}
test('観光地の連番をアイコンに替え、一覧と地図の選択を連動する',async({page})=>{
 await page.goto('/routes/'+encodeURIComponent(route))
 await expect(page.locator('.map-loading')).toHaveCount(0,{timeout:30000})
 await expect(page.locator('.spot-map-pin').first()).toBeVisible()
 const card=page.locator('.spot-card').first()
 const name=(await card.locator('h3').innerText()).trim()
 await expect(card.locator('.spot-kind-badge svg')).toHaveCount(1)
 await expect(card.locator('.spot-kind-badge')).toHaveText('')
 const spotId=await card.getAttribute('data-spot-id')
 const pin=page.locator(`.spot-map-pin[data-spot-id="${spotId}"]`)
 await expect(pin).toHaveCount(1)
 await expect(pin.locator('svg').first()).toBeVisible()
 await card.click()
 await expect(card).toHaveAttribute('aria-pressed','true')
 await expect(pin).toHaveAttribute('aria-pressed','true')
 await expect(pin.locator('.spot-pin-label')).toBeVisible()
 await expect(page.locator('.spot-popup h2')).toHaveText(name)
 await page.getByRole('button',{name:'観光地詳細を閉じる'}).click()
 await expect(pin).toHaveAttribute('aria-pressed','false')
 await page.setViewportSize({width:1440,height:900})
 await pin.focus();await expect(pin.locator('.spot-pin-label')).toBeVisible()
 await pin.press('Enter');await expect(page.locator('.spot-popup h2')).toHaveText(name)
 await page.screenshot({path:'/private/tmp/route-bus-icon-pins.png'})
})

test('観光地ピンは地図の座標に固定され、一覧のスクロールでずれない',async({page})=>{
 await page.setViewportSize({width:1440,height:900})
 await page.goto('/routes/'+encodeURIComponent(route))
 await expect(page.locator('.map-loading')).toHaveCount(0,{timeout:30000})
 const pins=page.locator('.spot-map-pin:visible')
 await expect(pins.first()).toBeVisible()
 await expect(pins.first()).toHaveCSS('position','absolute')
 await settledMarkers(page)
 // MapLibre's final pixel translation is the geographic anchor; the pin tip must match it.
 const anchorError=()=>page.locator('.spot-map-pin:visible').evaluateAll(elements=>elements.length?Math.max(...elements.map(el=>{
  const parent=el.parentElement!.getBoundingClientRect(),rect=el.getBoundingClientRect()
  const translations=[...((el as HTMLElement).style.transform.matchAll(/translate\(([-\d.]+)px,\s*([-\d.]+)px\)/g))]
  if(!translations.length)return Infinity
  const coordinate=translations[translations.length-1]
  return Math.max(Math.abs(rect.x+rect.width/2-parent.x-Number(coordinate[1])),Math.abs(rect.bottom-parent.y-Number(coordinate[2])))
 })):Infinity)
 await expect.poll(anchorError).toBeLessThan(1)
 await page.locator('.sidebar').evaluate(el=>{el.scrollTop=el.scrollHeight})
 await expect.poll(()=>page.locator('.sidebar').evaluate(el=>el.scrollTop)).toBeGreaterThan(0)
 await expect.poll(anchorError).toBeLessThan(1)
 await page.locator('.map-canvas').hover()
 const beforeZoom=await settledMarkers(page)
 await page.mouse.wheel(0,-400)
 await settledMarkers(page,beforeZoom)
 await expect.poll(anchorError).toBeLessThan(1)
 await page.setViewportSize({width:390,height:844})
 await settledMarkers(page)
 await expect.poll(anchorError).toBeLessThan(1)
 await page.locator('.sidebar').evaluate(el=>{el.scrollTop=0})
 await expect.poll(anchorError).toBeLessThan(1)
})
