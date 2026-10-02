#!/usr/bin/env python3
"""Create licensed WebP derivatives. Never replace credit or source metadata."""
import io,json,pathlib,urllib.request,hashlib,time
from PIL import Image,ImageOps
root=pathlib.Path('build/photos');root.mkdir(parents=True,exist_ok=True)
spots=json.load(open('data/tourism-spots.json'));overrides={};records=[]
for spot in spots:
 url=spot.get('photo','') or spot.get('photo_external','')
 if not url:continue
 try:
  if url.startswith('/photos/'):
   candidate=spot.get('photo_original','')
   originals=[p for p in root.glob(pathlib.Path(url).name.split('-thumb.')[0]+'-original.*') if p.suffix in ['.jpg','.png','.webp']]
   if originals:candidate='/photos/'+max(originals,key=lambda p:p.stat().st_size).name
   source=root/pathlib.Path(candidate).name if candidate.startswith('/photos/') and (root/pathlib.Path(candidate).name).exists() else root/pathlib.Path(url).name
   if not source.exists():continue
   content=source.read_bytes()
  elif url.startswith('https://'):
   time.sleep(.3)
   request=urllib.request.Request(url,headers={'User-Agent':'TabiBusMap/1.0 (licensed tourism photo derivatives)'})
   with urllib.request.urlopen(request,timeout=12) as response:content=response.read(20_000_001)
   if len(content)>20_000_000:raise ValueError('Image exceeds 20MB')
  else:continue
  image=ImageOps.exif_transpose(Image.open(io.BytesIO(content))).convert('RGB')
  asset=spot['id'] if spot['id'].startswith('Q') else 'municipal-'+hashlib.sha256(spot['id'].encode()).hexdigest()[:16]
  for variant,size,quality in [('thumb',640,78),('original',1440,83)]:
   output=image.copy();output.thumbnail((size,size));path=root/f'{asset}-{variant}.webp';output.save(path,'WEBP',quality=quality,method=6)
   records.append({'id':spot['id'],'variant':variant,'file':str(path),'key':'photos/'+path.name,'mime':'image/webp','width':output.width,'height':output.height,'bytes':path.stat().st_size,'inputBytes':len(content),'source':spot['photo_source'],'credit':spot['photo_credit'],'license':spot['photo_license']})
  overrides[spot['id']]={'photo':f'/photos/{asset}-thumb.webp','photo_original':f'/photos/{asset}-original.webp'}
 except Exception as error:
  records.append({'id':spot['id'],'error':str(error)})
  overrides[spot['id']]={'photo':'','photo_original':'','photo_external':url}
  if '429' in str(error):break
pathlib.Path('data/spot-photo-overrides.json').write_text(json.dumps(overrides,ensure_ascii=False,indent=2))
pathlib.Path('data/sources/webp-manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
print('Optimized spots:',sum(bool(r['photo']) for r in overrides.values()),'Failures:',sum('error' in r for r in records),flush=True)
