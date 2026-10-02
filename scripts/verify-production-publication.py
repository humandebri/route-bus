#!/usr/bin/env python3
"""Read destination DB and R2 before deploying matching browser assets. No remote writes."""
import hashlib,json,pathlib,sqlite3,subprocess,urllib.request,concurrent.futures,os
root=pathlib.Path('build/published');export=root/'destination-export.sql'
subprocess.run(['node','node_modules/wrangler/bin/wrangler.js','d1','export','bus-map','--remote','--output',str(export)],check=True)
actual=sqlite3.connect(':memory:');actual.executescript(export.read_text())
expected=sqlite3.connect(':memory:')
for file in sorted(pathlib.Path('migrations').glob('*.sql')):expected.executescript(file.read_text())
expected.executescript((root/'initial-seed.sql').read_text())
for table in ['routes','spots','stops','route_spots']:
 if set(actual.execute(f'SELECT * FROM {table}'))!=set(expected.execute(f'SELECT * FROM {table}')):
  raise SystemExit(f'Destination {table} does not match publication. Complete and verify the reviewed migration before code deployment.')
version=json.loads((root/'map-version.json').read_text());target=root/'destination.pmtiles'
subprocess.run(['node','node_modules/wrangler/bin/wrangler.js','r2','object','get','bus-map-data/'+version['routeKey'],'--remote','--file',str(target)],check=True)
assert hashlib.sha256(target.read_bytes()).digest()==hashlib.sha256((root/'routes.pmtiles').read_bytes()).digest(),'Destination tile differs from publication'
origin=os.environ.get('VITE_SITE_URL','https://route-bus.dreamvault.workers.dev').rstrip('/')
paths={s['photo'] for s in json.loads((root/'spots.json').read_text()) if s.get('photo')}
paths|={path.replace('-thumb.webp','-original.webp') for path in list(paths)}
def verify_photo(path):
 with urllib.request.urlopen(urllib.request.Request(origin+path,method='HEAD'),timeout=30) as response:
  assert response.status==200 and response.headers.get_content_type()=='image/webp',f'Missing destination image: {path}'
  size=response.headers.get('Content-Length')
  if size:assert int(size)==(pathlib.Path('build')/path.lstrip('/')).stat().st_size,f'Destination image size differs: {path}'
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(verify_photo,sorted(paths)))
print('Destination D1, versioned R2 tile and',len(paths),'image files match publication.')
