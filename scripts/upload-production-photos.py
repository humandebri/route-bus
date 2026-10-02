#!/usr/bin/env python3
"""Upload only checked WebP derivatives to the explicitly configured production bucket."""
import json,subprocess,concurrent.futures,pathlib,sys
if '--approved-photo-scope' not in sys.argv:raise SystemExit('Production upload is paused. Review the organized photo scope and obtain explicit approval before using --approved-photo-scope.')
selected_ids={s['id'] for s in json.load(open('build/published/spots.json')) if s.get('photo')}
manifest=json.load(open('data/sources/webp-manifest.json'));files=[r for r in manifest if r.get('file') and r['id'] in selected_ids];success=[];errors=[]
for record in json.load(open('data/sources/published-commons-downloads.json')):
 if record['status']=='downloaded-license-reviewed' and record['spotId'] in selected_ids:
  files.extend(record['files'].values())
keys={r['key'] for r in files}
for spot in json.load(open('build/published/spots.json')):
 if spot.get('photo') and spot['photo'].lstrip('/') not in keys:raise SystemExit('Missing reviewed photo file: '+spot['id'])
def upload(record):
 result=subprocess.run(['node','node_modules/wrangler/bin/wrangler.js','r2','object','put','bus-map-data/'+record['key'],'--file',record['file'],'--content-type','image/webp','--cache-control','public, max-age=86400','--remote'],capture_output=True,text=True)
 return record['key'],result.returncode,result.stderr[-500:]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for key,status,error in pool.map(upload,files):
  if status:errors.append({'key':key,'error':error})
  else:success.append(key)
  if (len(success)+len(errors))%20==0:print(f'Uploaded {len(success)}/{len(files)}, errors {len(errors)}',flush=True)
pathlib.Path('build/production-photos-upload.json').write_text(json.dumps({'success':success,'errors':errors},indent=2))
print('Uploaded',len(success),'WebP files;',len(errors),'failures',flush=True)
if errors:raise SystemExit(1)
