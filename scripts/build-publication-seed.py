#!/usr/bin/env python3
"""Generate an initial seed for a NEW EMPTY DB only. No remote calls; no blanket updates/deletes."""
import hashlib,json,pathlib
ROOT=pathlib.Path('build/published');catalog=json.loads((ROOT/'catalog.json').read_text());spots=json.loads((ROOT/'spots.json').read_text())
report=json.loads((ROOT/'organization-report.json').read_text())
for path,digest in report['inputDigests'].items():
 if hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()!=digest:raise SystemExit('Source changed. Run pnpm data:organize again before generating a seed.')
def sql(value):return 'NULL' if value is None else "'"+str(value).replace("'","''")+"'"
def insert(table,row):return f"INSERT INTO {table} ({','.join(row)}) VALUES ({','.join(sql(v) for v in row.values())});"
route_fields=['id','name','routeShortName','routeOfficial','operatorOfficial','nameEn','operator','operatorEn','origin','originEn','destination','destinationEn','region','prefecture','duration','color','tags','description','official','stops','featured','featuredName','featuredNameEn','featuredReason','featuredSource','featuredCheckedAt','dataLicense','geometryQuality','sourceId','sourceUrl','validUntil','validFrom','dataUpdatedAt','groupId','publicationBasis','publicationEvidence']
lines=['-- INITIAL SEED ONLY: empty database required. Existing DB cleanup needs a separate diff and write budget.','BEGIN TRANSACTION;'];stop_ids=set();associations=0
for s in spots:
 document={'id':s['id'],'name':s['name'],'nameEn':s.get('name_en',''),'descriptionEn':s.get('description_en',''),'coordinate':[s['lng'],s['lat']],'category':s.get('category') or '観光地','description':s.get('description',''),'photo':s.get('photo',''),'source':s['source_url'],'credit':s.get('photo_credit',''),'license':s.get('photo_license',''),'licenseUrl':s.get('photo_license_url',''),'photoSource':s.get('photo_source',''),'photoChanges':'Resized and converted to WebP' if s.get('photo') else '', 'accessVerified':False,'coordinateKind':s.get('coordinate_kind','代表地点・入口未確認'),'officialAccess':s.get('official_access',''),'publisher':s.get('publisher',''),'dataLicense':s.get('data_license','')}
 lines.append(insert('spots',{'id':s['id'],'name':s['name'],'lat':s['lat'],'lng':s['lng'],'description':s.get('description',''),'official_url':s.get('official_url',s['source_url']),'document':json.dumps(document,ensure_ascii=False,separators=(',',':'))}))
for r in catalog:
 doc={k:r[k] for k in route_fields if k in r};doc.update(spots=[],spotCount=len(r['spots']),photoCount=sum(bool(s.get('photo')) for s in r['spots']))
 lines.append(insert('routes',{'id':r['id'],'name':r['name'],'region':r['region'],'active':1,'document':json.dumps(doc,ensure_ascii=False,separators=(',',':'))}))
 for s in r['spots']:
  stop=r['stops'][s['sequence']];stop_id='derived-stop-'+hashlib.sha256(json.dumps(stop,ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:20]
  if stop_id not in stop_ids:
   lines.append(insert('stops',{'id':stop_id,'name':stop['name'],'lat':stop['coordinate'][1],'lng':stop['coordinate'][0]}));stop_ids.add(stop_id)
  official=s.get('officialAccess','');confidence='official-stop-mentioned' if stop['name'] and stop['name'] in official else 'proximity-only'
  lines.append(insert('route_spots',{'route_id':r['id'],'spot_id':s['id'],'stop_id':stop_id,'walk_minutes':s['walk'],'sequence':s['sequence'],'access_confidence':confidence}));associations+=1
lines.append('COMMIT;');(ROOT/'initial-seed.sql').write_text('\n'.join(lines))
# Current schema has one TEXT PK index on spots/routes/stops and two indexes on route_spots.
plan={'purpose':'new empty database only; not an update plan','rows':{'spots':len(spots),'routes':len(catalog),'stops':len(stop_ids),'route_spots':associations},'estimatedInsertWritesIncludingIndexes':2*(len(spots)+len(catalog)+len(stop_ids))+3*associations,'schemaAndOtherAccountWritesIncluded':False,'remoteExecutionAllowed':False,'notice':'推定値は既存スキーマへの新規投入のみ。既存データ削除、移行、他サービスの当日使用量を含まない。無料枠の残量を確認しないまま実行しない。'}
(ROOT/'initial-write-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2));print(json.dumps(plan,ensure_ascii=False,indent=2))
