#!/usr/bin/env python3
"""Resolve explicit OSM Wikidata image identities and Commons licenses, without SPARQL."""
import collections,html,json,math,pathlib,re,time,urllib.parse,urllib.request
identities=json.load(open('data/sources/published-osm-identities.json'))['records'];spots={s['id']:s for s in json.load(open('build/published/spots.json'))}
ids=sorted({v['wikidata'] for v in identities.values() if re.fullmatch(r'Q[0-9]+',v.get('wikidata',''))});out=pathlib.Path('data/sources');out.mkdir(parents=True,exist_ok=True)
def get(base,params):
 url=base+'?'+urllib.parse.urlencode(params)
 req=urllib.request.Request(url,headers={'User-Agent':'TabiBusMapResearch/1.0 (licensed scenic bus map; contact via https://route-bus.dreamvault.workers.dev/)' ,'Accept':'application/json'})
 with urllib.request.urlopen(req,timeout=25) as r:return json.load(r)
def batches(seq,n):
 for i in range(0,len(seq),n):yield seq[i:i+n]
entities={};errors=[]
for batch in batches(ids,45):
 try:entities.update(get('https://www.wikidata.org/w/api.php',{'action':'wbgetentities','ids':'|'.join(batch),'props':'claims','format':'json'})['entities']);print('entities',len(entities),flush=True)
 except Exception as e:errors.append({'stage':'wikidata','ids':batch,'error':str(e)});break
 time.sleep(.4)
by_title=collections.defaultdict(list)
for sid,tags in identities.items():
 if sid not in spots:continue
 entity=entities.get(tags.get('wikidata',''),{});claims=entity.get('claims',{})
 images=[x.get('mainsnak',{}).get('datavalue',{}).get('value') for x in claims.get('P18',[])]
 position=[x.get('mainsnak',{}).get('datavalue',{}).get('value') for x in claims.get('P625',[])]
 if position:
  geo=position[0];s=spots[sid];distance=math.hypot((geo['latitude']-s['lat'])*111320,(geo['longitude']-s['lng'])*111320*math.cos(math.radians(s['lat'])))
  if distance>1000:continue
 for name in images[:2]:
  if isinstance(name,str):by_title['File:'+name.replace('_',' ')].append(sid)
 commons=tags.get('wikimedia_commons','');image=tags.get('image','')
 if commons.startswith('File:'):by_title[commons.replace('_',' ')].append(sid)
 if image.startswith('File:'):by_title[image.replace('_',' ')].append(sid)
licenses=[];candidate={}
def plain(value):return html.unescape(re.sub('<[^>]+>','',value or '')).strip()
def accepted(short,licenseurl):
 value=short.lower().replace(' ','-').replace('_','-')
 if any(term in value for term in ['-nc','-nd','noncommercial','no-derivatives']):return False
 return bool(re.fullmatch(r'cc-by(?:-sa)?(?:-\d+(?:\.\d+)?)?(?:-[a-z]{2})?|cc0(?:-\d+(?:\.\d+)?)?|public-domain|pd-old(?:-\d+)?|pd-us(?:-\d+)?',value))
for batch in batches(list(by_title),20):
 try:
  pages=get('https://commons.wikimedia.org/w/api.php',{'action':'query','format':'json','prop':'imageinfo','iiprop':'url|extmetadata|mime','iiurlwidth':1440,'titles':'|'.join(batch)})['query']['pages']
  for page in pages.values():
   if not page.get('imageinfo'):continue
   info=page['imageinfo'][0];meta=info.get('extmetadata',{});lic=plain(meta.get('LicenseShortName',{}).get('value',''));licurl=meta.get('LicenseUrl',{}).get('value','')
   if not accepted(lic,licurl):continue
   if not info.get('mime','').startswith('image/') or info['mime']=='image/svg+xml':continue
   title=page['title'];credit=plain(meta.get('Artist',{}).get('value','')) or plain(meta.get('Credit',{}).get('value',''))
   if not credit or not info.get('thumburl'):continue
   for sid in by_title[title]:
    if sid in candidate:continue
    candidate[sid]={'spotId':sid,'title':title,'downloadUrl':info['thumburl'],'photoSource':info['descriptionurl'],'credit':credit,'license':lic,'licenseUrl':licurl,'wikidata':identities[sid].get('wikidata',''),'source':'https://commons.wikimedia.org/w/api.php','status':'license-reviewed-download-pending'}
  print('image metadata',len(candidate),flush=True)
 except Exception as e:errors.append({'stage':'commons','titles':batch,'error':str(e)});break
 time.sleep(.4)
(out/'published-commons-candidates.json').write_text(json.dumps({'source':'https://commons.wikimedia.org/w/api.php','candidates':list(candidate.values()),'errors':errors,'wikidataEntitiesResolved':len(entities),'titles':len(by_title)},ensure_ascii=False,indent=2))
print('Candidates',len(candidate),'errors',len(errors),flush=True)
