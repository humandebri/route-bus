import {createRootRoute,HeadContent,Scripts,Outlet} from '@tanstack/react-router'
import {useLocale,seoLinks} from '../i18n'
import css from '../styles.css?url'
export const Route=createRootRoute({
 validateSearch:(search:Record<string,unknown>):{lang?:'en'|'ja'}=>search.lang==='en'?{lang:'en'}:search.lang==='ja'?{lang:'ja'}:{},
 head:({match})=>{const english=match.search.lang==='en';return {meta:[{charSet:'utf-8'},{name:'viewport',content:'width=device-width, initial-scale=1'},{title:english?'Tabi Bus Map | Discover Japan by bus':'旅バスマップ｜路線から、旅を見つける'},{name:'description',content:english?'Discover scenic bus routes across Japan and the places you can visit along the way.':'全国の観光路線バスを地図から発見。このバスで行ける観光地と車窓の景色を探しましょう。'}],links:[{rel:'stylesheet',href:css}]};},
 component:Root,
})
function Root(){const locale=useLocale();return <html lang={locale}><head><HeadContent/></head><body><Outlet/><Scripts/></body></html>}
