#!/usr/bin/env python3
"""Download Commons originals and thumbnails; preserve attribution in manifest."""
import json,pathlib,urllib.request,concurrent.futures,urllib.parse
root=pathlib.Path('build/photos');root.mkdir(parents=True,exist_ok=True);spots=json.load(open('data/spots.json'))
def download(spot):
 result=[]
 for variant,url in [('thumb',spot['photo']),('original',spot['photo_original'])]:
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'RouteBusMVP/0.1 (licensed Commons images)'})
   with urllib.request.urlopen(req,timeout=30) as response:
    mime=response.headers.get('Content-Type','image/jpeg').split(';')[0];ext={'image/jpeg':'jpg','image/png':'png','image/webp':'webp'}.get(mime)
    if not ext:raise ValueError('Unsupported image type '+mime)
    content=response.read(20_000_001)
    if len(content)>20_000_000:raise ValueError('Photo exceeds 20MB limit')
   path=root/f"{spot['id']}-{variant}.{ext}";path.write_bytes(content);result.append({'id':spot['id'],'variant':variant,'file':str(path),'key':'photos/'+path.name,'mime':mime,'source':spot['photo_source'],'credit':spot['photo_credit'],'license':spot['photo_license']})
  except Exception as e:result.append({'id':spot['id'],'variant':variant,'error':str(e)})
 return result
records=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for batch in pool.map(download,spots):records.extend(batch)
pathlib.Path('data/sources/photos-manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));byid={r['id']:r for r in records if r.get('variant')=='thumb' and 'error' not in r}
for spot in spots:
 if spot['id'] in byid:spot['photo_external']=spot['photo'];spot['photo']='/'+byid[spot['id']]['key']
pathlib.Path('data/spots.json').write_text(json.dumps(spots,ensure_ascii=False,indent=2));print('Downloaded',sum('error' not in r for r in records),'image files;',sum('error' in r for r in records),'errors')
