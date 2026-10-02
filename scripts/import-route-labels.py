#!/usr/bin/env python3
"""Restore published GTFS route signs and official links from cached originals."""
import csv,io,json,pathlib,zipfile
path=pathlib.Path('build/collected/catalog.json');catalog=json.loads(path.read_text());labels={}
registry=json.load(open('data/sources/gtfs-collection.json'))['feeds']
extra=pathlib.Path('data/sources/extra-gtfs-collection.json')
if extra.exists():registry+=json.loads(extra.read_text())
for feed in registry:
 archive=pathlib.Path(feed.get('archive',''))
 if feed.get('status')!='downloaded' or not archive.is_file():continue
 try:
  with zipfile.ZipFile(archive) as z:
   def rows(name):return list(csv.DictReader(io.TextIOWrapper(z.open(name),encoding='utf-8-sig')))
   agencies=rows('agency.txt');sid=feed['organization_id']+'__'+feed['feed_id']
   for r in rows('routes.txt'):
    agency=next((a for a in agencies if a.get('agency_id','default')==r.get('agency_id','default')),agencies[0])
    labels[sid+':'+r['route_id']]={'routeShortName':r.get('route_short_name','').strip(),'routeOfficial':r.get('route_url','').strip(),'operatorOfficial':agency.get('agency_url','').strip()}
 except (KeyError,IndexError,UnicodeDecodeError,zipfile.BadZipFile) as error:
  print('Labels unavailable:',archive.name,type(error).__name__)
for route in catalog:
 if route['id'] in labels:route.update(labels[route['id']])
path.write_text(json.dumps(catalog,ensure_ascii=False))
print('GTFS labels and official links restored for',sum(r['id'] in labels for r in catalog),'patterns')
