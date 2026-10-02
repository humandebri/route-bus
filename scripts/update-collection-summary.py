#!/usr/bin/env python3
import json,pathlib,datetime,collections,hashlib
catalog=json.load(open('build/collected/catalog.json'));spots=json.load(open('data/tourism-spots.json'));sources=json.load(open('data/sources/municipal-collection.json'))
eligible=[r for r in catalog if (r['spots'] or r.get('featured')) and r.get('tourismEligible',True)]
p=pathlib.Path('src/data/collection-summary.json');report=json.loads(p.read_text());report.update(collectedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),tourismRoutes=len(eligible),tourismSpots=len(spots),municipalSpots=len(json.load(open('data/municipal-spots.json'))),municipalDatasets=sum(s['status']=='collected' for s in sources),municipalSources=sources,photoSpots=sum(bool(s['photo']) for s in spots),relations=sum(len(r['spots']) for r in eligible),featuredRoutes=json.load(open('data/editorial/featured-routes.json')),featuredPatterns=sum(bool(r.get('featured')) for r in catalog),curatedWithoutGeometry=sum(r['id'].startswith('featured:') for r in catalog))
report['normalizedRoutes']=sum(not r['id'].startswith('featured:') for r in catalog)
report['extraGtfsSources']=json.load(open('data/sources/extra-gtfs-collection.json')) if pathlib.Path('data/sources/extra-gtfs-collection.json').exists() else []
report['extraGtfsBuildErrors']=[r for r in json.load(open('build/collected/extra-build-report.json')) if r['status']=='error'] if pathlib.Path('build/collected/extra-build-report.json').exists() else []
report['osmBulkSource']=json.load(open('data/sources/osm-bulk-collection.json')) if pathlib.Path('data/sources/osm-bulk-collection.json').exists() else None
registry=json.load(open('data/sources/gtfs-collection.json'))['feeds']
report['downloadedFeeds']=sum(f['status']=='downloaded' for f in registry+report['extraGtfsSources'])
report['extraGtfsFeeds']=len(report['extraGtfsSources'])
report['osmSpots']=sum(s['id'].startswith('osm-') for s in spots)
report['osmSources']=json.load(open('data/sources/osm-collection.json')) if pathlib.Path('data/sources/osm-collection.json').exists() else []
report['routeExclusions']=dict(collections.Counter(r.get('tourismExclusionReason') or '観光地未登録・未選定' for r in catalog if r not in eligible))
for path in ['src/data/collection-summary.json','public/data/collection-summary.json']:pathlib.Path(path).write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(report['tourismRoutes'],'published routes;',len(report['featuredRoutes']),'reviewed route groups;',report['relations'],'relations')

version={key:hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()[:16] for key,path in [('routes','build/collected/tourism-routes.geojson'),('points','public/data/spot-points.geojson')]}
pathlib.Path('src/data/map-version.json').write_text(json.dumps(version))
