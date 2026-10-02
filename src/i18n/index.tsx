import {useRouterState} from '@tanstack/react-router'
import dictionary from './en.json'
export type Locale='ja'|'en'
export function useLocale():Locale{return useRouterState({select:s=>(s.location.search as {lang?:string}).lang==='en'?'en':'ja'})}
export function t(text:string,locale:Locale):string{return locale==='en'?(dictionary as Record<string,string>)[text.trim()]??text:text}
export function localeUrl(path:string,locale:Locale){const url=new URL(path,'https://local.invalid');if(locale==='en')url.searchParams.set('lang','en');else url.searchParams.delete('lang');return url.pathname+url.search+url.hash}
export function LanguageSwitcher(){const locale=useLocale();const href=useRouterState({select:s=>s.location.href});return <nav className="language-switch" aria-label={locale==='en'?'Language':'言語'}><a href={localeUrl(href,'ja')} lang="ja" aria-current={locale==='ja'?'true':undefined}>日本語</a><span>/</span><a href={localeUrl(href,'en')} lang="en" aria-current={locale==='en'?'true':undefined}>English</a></nav>}
export function sourceTextNote(locale:Locale){return locale==='en'?'Official English names are used where available. Untranslated names and source text remain in Japanese.':''}
export function seoLinks(path:string,locale:Locale){const origin=import.meta.env.VITE_SITE_URL;if(!origin)return [];return [{rel:'canonical',href:new URL(localeUrl(path,locale),origin).href},...(['ja','en','x-default'] as const).map(hreflang=>({rel:'alternate',hrefLang:hreflang,href:new URL(localeUrl(path,hreflang==='en'?'en':'ja'),origin).href}))]}

export function placeName(text:string,locale:Locale){return text.split('・').map(part=>t(part,locale)).join(locale==='en'?' / ':'・')}
