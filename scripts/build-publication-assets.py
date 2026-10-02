#!/usr/bin/env python3
"""Stage browser assets for the same publication as D1 and R2. No remote calls."""
import hashlib,json,pathlib,shutil,subprocess
root=pathlib.Path('build/published')
def read(name):return json.loads((root/name).read_text())
def write(path,data):pathlib.Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2))
report=read('organization-report.json');routes=read('catalog.json');spots=read('spots.json')
# A stale tile build must never accompany a new catalog.
geo_digest=hashlib.sha256((root/'routes.geojson').read_bytes()).hexdigest()
assert (root/'routes.pmtiles.source-sha256').read_text().strip()==geo_digest,'Rebuild publication tiles first'
subprocess.run(['python3','scripts/build-coverage.py','--published'],check=True)
summary=json.loads(pathlib.Path('src/data/collection-summary.json').read_text())
summary.update(publicationDate=report['validatedOn'],tourismRoutes=len(routes),tourismSpots=len(spots),photoSpots=report['photoSpots'],relations=report['relations'],municipalSpots=sum(s['id'].startswith('municipal-') for s in spots),osmSpots=sum(s['id'].startswith('osm-') for s in spots),curatedWithoutGeometry=sum(not r['stops'] for r in routes),notice='公式の乗車・車窓選定、停留所と地点の名称照合、または公式バスアクセス情報に根拠がある路線を掲載します。距離が近いだけの候補は保留します。入口・徒歩経路・営業状態は未確認です。',publicationReasons=report['routeReasons'])
write(root/'collection-summary.json',summary)
license_info={'license':'ODbL 1.0','licenseUrl':'https://opendatacommons.org/licenses/odbl/1-0/','attribution':'© OpenStreetMap contributors; municipal publishers; individual source rights retained'}
write(root/'spots.geojson',{'type':'FeatureCollection',**license_info,'features':[{'type':'Feature','geometry':{'type':'Point','coordinates':[s['lng'],s['lat']]},'properties':s} for s in spots]})
write(root/'osm-spots.json',{**license_info,'spots':[s for s in spots if s['id'].startswith('osm-')]})
write(root/'osm-route-associations.json',{**license_info,'associations':[{'routeId':r['id'],'spotId':s['id'],'stop':s['stop'],'walkMinutes':s['walk']} for r in routes for s in r['spots']]})
version={key:hashlib.sha256((root/name).read_bytes()).hexdigest()[:16] for key,name in [('routes','routes.pmtiles'),('points','spot-points.geojson')]}
version['routeKey']='maps/gtfs-routes-'+version['routes']+'.pmtiles'
write(root/'map-version.json',version)
for name in ['spot-points.geojson','spots.geojson','osm-spots.json','osm-route-associations.json','photo-credits.json','coverage.json','collection-summary.json']:
 shutil.copyfile(root/name,pathlib.Path('public/data')/name)
for name in ['photo-credits.json','coverage.json','collection-summary.json','map-version.json']:
 shutil.copyfile(root/name,pathlib.Path('src/data')/name)
print('Staged',len(routes),'routes,',len(spots),'places;',version['routeKey'])
