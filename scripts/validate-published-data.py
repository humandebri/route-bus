#!/usr/bin/env python3
"""Verify cleaned data against an isolated in-memory SQLite DB; no Cloudflare calls."""
import json,pathlib,sqlite3,importlib.util,copy,hashlib
spec=importlib.util.spec_from_file_location('organize','scripts/organize-data.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
root=pathlib.Path('build/published');routes=json.loads((root/'catalog.json').read_text());spots=json.loads((root/'spots.json').read_text());groups=json.loads((root/'route-groups.json').read_text());report=json.loads((root/'organization-report.json').read_text())
for path,digest in report['inputDigests'].items():assert hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()==digest,'Collected source changed after organization'
ids={s['id'] for s in spots};routeids={r['id'] for r in routes};linked={s['id'] for r in routes for s in r['spots']}
assert ids==linked,'Unrelated or missing published place'
assert len(ids)==len(spots) and len(routeids)==len(routes),'Duplicate IDs'
assert {v for g in groups for v in g['variantIds']}==routeids,'Lost direction or route variant'
assert {g['id'] for g in groups}=={r['groupId'] for r in routes}
for s in spots:
 if s.get('photo'):
  assert s['photo'].startswith('/photos/') and s['photo'].endswith('.webp')
  asset=pathlib.Path('build')/s['photo'].lstrip('/')
  assert asset.is_file(),f'Missing photo asset: {asset}'
  with asset.open('rb') as f:assert f.read(4)==b'RIFF' and f.read(8)[4:]==b'WEBP',f'Invalid WebP: {asset}'
  assert s.get('photo_credit') and s.get('photo_license') and s.get('photo_source'),f'Missing photo attribution: {s["id"]}'
for r in routes:
 assert r.get('featured') or r['publicationEvidence'],'Proximity alone admitted a route'
 assert len({s['id'] for s in r['spots']})==len(r['spots'])
 for s in r['spots']:
  assert 0<=s['sequence']<len(r['stops'])
  assert s['photo']==next(p['photo'] for p in spots if p['id']==s['id'])
  if s['photo']:assert s['photo'].endswith('.webp') and s['credit'] and s['license'] and s['photoSource']
# Ensure every source route has an auditable keep/withhold decision.
assert len(report['routes'])==report['inputRoutes']
assert sum(d['published'] for d in report['routes'])==len(routes)
db=sqlite3.connect(':memory:')
for p in sorted(pathlib.Path('migrations').glob('*.sql')):db.executescript(p.read_text())
db.executescript((root/'initial-seed.sql').read_text());assert not db.execute('PRAGMA foreign_key_check').fetchall()
plan=json.loads((root/'initial-write-plan.json').read_text())
for table,count in plan['rows'].items():assert db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]==count
seed=(root/'initial-seed.sql').read_text();assert 'DELETE FROM' not in seed and 'UPDATE routes SET active=0' not in seed and 'ON CONFLICT' not in seed
# Regression fixtures: residence parts merge, different facilities do not; return direction stays.
def spot(id,name,lng=130):return {'id':id,'name':name,'lat':33,'lng':lng,'publisher':'自治体','source_url':'https://example.test/tourism','photo':'','data_license':'CC BY 4.0'}
fixtures=[spot('a','吉岡家住宅（主屋）'),spot('b','吉岡家住宅江戸蔵'),spot('c','別の家住宅主屋')]
def route(id,name='観光線',stop='吉岡家住宅前',featured=False):return {'id':id,'name':name,'operator':'事業者','sourceId':'provider','featured':featured,'stops':[{'name':stop,'coordinate':[130,33]}],'spots':[{'id':'a','name':'吉岡家住宅（主屋）','sequence':0,'walk':1,'stop':stop}],'tourismEligible':True}
kept,places,gr,_=module.organize([route('outbound'),route('return'),route('unverified',stop='駅前'),route('school','通学線'),{**route('famous',featured=True),'spots':[]}],fixtures)
assert {r['id'] for r in kept}=={'outbound','return','famous'}
assert len(gr)==1 and set(gr[0]['variantIds'])=={'outbound','return','famous'}
assert len(places)==1 and places[0]['name']=='吉岡家住宅' and len(places[0]['members'])==2
# A same-named residence in another location must remain separate.
_,far_places,_,far_report=module.organize([route('one')],fixtures+[spot('far','吉岡家住宅主屋',lng=130.01)])
assert all(member['id']!='far' for merge in far_report['merges'] for member in merge['members'])
print(f'Validated {len(routes)} patterns / {len(groups)} route groups / {len(spots)} places; references, provenance and SQLite seed passed. No remote operations.')
# Date changes cannot silently publish expired snapshots, including featured GTFS.
import datetime,sys
current=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().strftime('%Y%m%d')
assert all((not r.get('validUntil') or r['validUntil'].replace('-','')>=current) and (not r.get('validFrom') or r['validFrom'].replace('-','')<=current) for r in routes),'Feed outside its validity period. Run data:prepare.'
fixtures=[route('current'),dict(route('expired',featured=True),validUntil='20260930'),dict(route('future',featured=True),validFrom='20261003')]
kept,_,_,audit=module.organize(fixtures,[spot('a','吉岡家住宅（主屋）')],as_of='20261002')
assert {r['id'] for r in kept}=={'current'}
assert audit['routeReasons']['expired-feed']==1 and audit['routeReasons']['future-feed']==1
if '--assets' in sys.argv:
 import shutil
 version=json.loads((root/'map-version.json').read_text())
 assert hashlib.sha256((root/'routes.geojson').read_bytes()).hexdigest()==(root/'routes.pmtiles.source-sha256').read_text().strip(),'Stale tile source'
 assert version['routes']==hashlib.sha256((root/'routes.pmtiles').read_bytes()).hexdigest()[:16],'Stale tile version'
 assert version['points']==hashlib.sha256((root/'spot-points.geojson').read_bytes()).hexdigest()[:16]
 assert version['routeKey']=='maps/gtfs-routes-'+version['routes']+'.pmtiles'
 for name in ['spot-points.geojson','spots.geojson','osm-spots.json','osm-route-associations.json','photo-credits.json','coverage.json','collection-summary.json']:
  assert (root/name).read_bytes()==(pathlib.Path('public/data')/name).read_bytes(),f'Stale browser asset: {name}'
 for name in ['photo-credits.json','coverage.json','collection-summary.json','map-version.json']:
  assert (root/name).read_bytes()==(pathlib.Path('src/data')/name).read_bytes(),f'Stale SSR asset: {name}'
 points=json.loads((root/'spot-points.geojson').read_text())
 assert {f['properties']['id'] for f in points['features']}==ids,'Pins and DB differ'
 summary=json.loads((root/'collection-summary.json').read_text())
 assert (summary['tourismRoutes'],summary['tourismSpots'],summary['relations'])==(len(routes),len(spots),sum(len(r['spots']) for r in routes))
 for r in routes:
  doc=json.loads(db.execute('SELECT document FROM routes WHERE id=?',(r['id'],)).fetchone()[0])
  assert doc['publicationBasis']==r['publicationBasis'] and doc['publicationEvidence']==r['publicationEvidence']
 print('Browser assets, SSR counts and versioned R2 tile match the publication.')
