import type {BusRoute} from '../data/catalog'
import type {Locale} from '../i18n'
// Use a published short name or an explicit code before a colon, never the GTFS ID.
const codePattern=/^(?:[A-Za-z東西南北]{0,4}[0-9０-９]+[A-Za-z]{0,4}|[A-Za-z]{1,4})(?:[-－/／](?:[A-Za-z東西南北]{0,4}[0-9０-９]+[A-Za-z]{0,4}|[A-Za-z]{1,4}))*$/
export function routeCode(route:BusRoute):string{
 const short=route.routeShortName?.trim()??''
 if(codePattern.test(short))return short
 const prefix=route.name.match(/^([^：:]+)[：:]\s*/)?.[1]??''
 return codePattern.test(prefix)?prefix:''
}
export function routeTitle(route:BusRoute,locale:Locale,translate:(text:string)=>string):string{
 const name=locale==='en'?(translate(route.featuredName||'')||route.nameEn||route.name):(route.featuredName||route.name)
 const code=routeCode(route)
 const prefix=name.match(/^([^：:]+)[：:]\s*/)
 return code&&prefix?.[1]===code?name.slice(prefix[0].length):name
}
