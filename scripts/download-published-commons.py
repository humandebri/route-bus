#!/usr/bin/env python3
"""Download licensed Commons candidates as local WebP; skip failed/blocked files."""
import concurrent.futures,hashlib,io,json,pathlib,time,urllib.request
from PIL import Image,ImageOps
root=pathlib.Path('build/photos');root.mkdir(parents=True,exist_ok=True)
input=json.load(open('data/sources/published-commons-candidates.json'))['candidates'];records=[]
def one(item):
 sid=item['spotId'];prefix='commons-'+hashlib.sha256((sid+item['title']).encode()).hexdigest()[:16]
 try:
  cached=all((root/f'{prefix}-{variant}.webp').is_file() for variant in ('thumb','original'))
  if not cached:
   req=urllib.request.Request(item['downloadUrl'],headers={'User-Agent':'TabiBusMapResearch/1.0 (licensed tourism photos; https://route-bus.dreamvault.workers.dev/)'})
   with urllib.request.urlopen(req,timeout=25) as r:
    if not r.headers.get('Content-Type','').startswith('image/'):raise ValueError('Non-image response')
    data=r.read(20_000_001)
   if len(data)>20_000_000:raise ValueError('Image exceeds 20 MB')
   image=ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert('RGB')
  output={}
  for variant,size,quality in [('thumb',640,78),('original',1440,83)]:
   path=root/f'{prefix}-{variant}.webp'
   if not cached:
    resized=image.copy();resized.thumbnail((size,size));resized.save(path,'WEBP',quality=quality,method=6)
   with Image.open(path) as saved:
    if saved.format!='WEBP':raise ValueError('Cached file is not WebP')
    output[variant]={'key':'photos/'+path.name,'file':str(path),'bytes':path.stat().st_size,'width':saved.width,'height':saved.height}
  return {'spotId':sid,'name':item['title'],'photo':'/'+output['thumb']['key'],'photo_original':'/'+output['original']['key'],'photo_source':item['photoSource'],'photo_credit':item['credit'],'photo_license':item['license'],'photo_license_url':item['licenseUrl'],'wikidata':item['wikidata'],'source':item['source'],'status':'downloaded-license-reviewed','files':output}
 except Exception as e:return {'spotId':sid,'name':item['title'],'error':str(e),'status':'unavailable'}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for record in pool.map(one,input):
  records.append(record)
  if len(records)%25==0:print('Attempted',len(records),'downloaded',sum(r['status']=='downloaded-license-reviewed' for r in records),flush=True)
success=[r for r in records if r['status']=='downloaded-license-reviewed']
pathlib.Path('data/editorial/photo-enrichment.json').write_text(json.dumps({r['spotId']:{k:r[k] for k in ['photo','photo_original','photo_source','photo_credit','photo_license','photo_license_url']} for r in success},ensure_ascii=False,indent=2))
pathlib.Path('data/sources/published-commons-downloads.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
print('Downloaded',len(success),'of',len(records),'licensed images',flush=True)
