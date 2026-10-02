#!/usr/bin/env python3
"""Replace only reviewed extra feeds; keep original registry geometry intact."""
import json,pathlib,subprocess,sys
out=pathlib.Path('build/collected');catalog=json.load(open(out/'catalog.json'));geometry=json.load(open(out/'routes.geojson'));feeds=json.load(open('data/sources/extra-gtfs-collection.json'));report=[]
for feed in feeds:
 sid=feed['organization_id']+'__'+feed['feed_id']
 # Remove superseded or now expired extra feeds too.
 catalog=[r for r in catalog if r.get('sourceId')!=sid];geometry['features']=[f for f in geometry['features'] if not f['properties']['id'].startswith(sid+':')]
 if feed['status']!='downloaded':continue
 directory=out/sid;pref='福井県' if feed['feed_pref_id']==18 else '鳥取県';region='中部' if feed['feed_pref_id']==18 else '中国'
 result=subprocess.run([sys.executable,'scripts/import-gtfs.py',feed['archive'],'--source-id',sid,'--license',feed['feed_license'],'--region',region,'--prefecture',pref,'--output',str(directory)],capture_output=True,text=True)
 if result.returncode:report.append(dict(id=sid,status='error',error=result.stderr[-1000:]));continue
 docs=json.load(open(directory/'catalog.json'))
 for r in docs:r.update(dataUpdatedAt=feed['feed_info'].get('feed_version') or feed['last_updated_at'],validUntil=feed['calendar_end'],sourceUrl=feed['source_page'])
 catalog.extend(docs);geometry['features'].extend(json.load(open(directory/'routes.geojson'))['features']);report.append(dict(id=sid,status='built',routes=len(docs)));print(pref,feed['feed_name'],len(docs),'routes',flush=True)
(out/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False));(out/'routes.geojson').write_text(json.dumps(geometry,ensure_ascii=False));(out/'extra-build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(sum(r.get('routes',0) for r in report),'extra routes')
