#!/usr/bin/env python3
"""Resolve collected Wikidata coordinates and licensed Commons photo metadata."""
import json,pathlib,urllib.request,urllib.parse,re,html,time
source=json.load(open('data/sources/wikidata-spots.json'))['results']['bindings'];titles=['File:'+urllib.parse.unquote(s['image']['value'].split('/')[-1]) for s in source]
resolved={};errors=[]
def plain(s):return html.unescape(re.sub('<[^>]+>','',s or ''))
for offset in range(0,len(titles),25):
 params={'action':'query','format':'json','prop':'imageinfo','iiprop':'url|extmetadata','iiurlwidth':640,'titles':'|'.join(titles[offset:offset+25])}
 req=urllib.request.Request('https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(params),headers={'User-Agent':'RouteBusMVP/0.1 (open-data collection)'})
 try:
  data=json.load(urllib.request.urlopen(req,timeout=30))
  for page in data.get('query',{}).get('pages',{}).values():
   if page.get('imageinfo'):resolved[page['title']]=page['imageinfo'][0]
 except Exception as e:errors.append(str(e))
 time.sleep(.2)
spots=[]
for s,title in zip(source,titles):
 info=resolved.get(title)
 if not info:continue
 ext=info.get('extmetadata',{});license=ext.get('LicenseShortName',{}).get('value','')
 if not any(x in license.lower() for x in ['cc by','cc-by','cc0','public domain']):continue
 match=re.match(r'Point\(([-\d.]+) ([-\d.]+)\)',s['coord']['value'])
 if not match:continue
 spots.append({'id':s['item']['value'].split('/')[-1],'name':s['itemLabel']['value'],'lng':float(match[1]),'lat':float(match[2]),'description':'','source_url':s['item']['value'].replace('http:','https:'),'data_license':'CC0','photo':info.get('thumburl',info['url']),'photo_original':info['url'],'photo_source':info['descriptionurl'],'photo_license':plain(license),'photo_license_url':ext.get('LicenseUrl',{}).get('value',''),'photo_credit':plain(ext.get('Artist',{}).get('value','')),'review_status':'metadata-collected; walking-access-not-verified'})
pathlib.Path('data/spots.json').write_text(json.dumps(spots,ensure_ascii=False,indent=2));pathlib.Path('data/sources/commons-metadata.json').write_text(json.dumps(resolved,ensure_ascii=False));print('Licensed photo records:',len(spots),'errors:',errors)
