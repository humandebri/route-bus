import { createFileRoute } from '@tanstack/react-router'
import {seoLinks} from '../i18n'
import { Explorer } from '../components/Explorer'
import { getCatalog } from '../server-functions'
export const Route=createFileRoute('/')({loader:()=>getCatalog(),head:({match})=>({links:seoLinks('/',match.search.lang==='en'?'en':'ja')}),component:()=> <Explorer routes={Route.useLoaderData()}/>})
