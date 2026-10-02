#!/usr/bin/env python3
"""Refresh precomputed stop/spot relations without rebuilding geometry."""
import json,pathlib,math,re
pathlib.Path('build/collected/candidate-exports').mkdir(parents=True,exist_ok=True)
catalog=[r for r in json.load(open('build/collected/catalog.json')) if not r['id'].startswith('featured:')];spots=json.load(open('data/tourism-spots.json'))
grid={}
for spot in spots:grid.setdefault((math.floor(spot['lat']*100),math.floor(spot['lng']*100)),[]).append(spot)
sources={f['organization_id']+'__'+f['feed_id']:f for f in json.load(open('data/sources/gtfs-collection.json'))['feeds']}
for route in catalog:
 feed_name=sources.get(route.get('sourceId'),{}).get('feed_name','')
 name=route['name']
 exclusion='高速・空港系統' if re.search(r'高速|空港|[Ee]xpress|エクスプレス|大阪号|東京号',feed_name+' '+name) else '通学・買い物など生活目的の系統' if re.search(r'スクール|通学|通勤|買い物|送迎',name) else ''
 if not exclusion and re.search(r'大阪|東京|京都|神戸',name) and route['stops']:
  first,last=route['stops'][0]['coordinate'],route['stops'][-1]['coordinate']
  if math.hypot((first[0]-last[0])*90000,(first[1]-last[1])*111320)>80000:exclusion='長距離都市間の系統'
 route['tourismEligible']=not bool(exclusion);route['tourismExclusionReason']=exclusion
 linked=[];candidates={}
 for stop in route['stops']:
  lng,lat=stop['coordinate'];y=math.floor(lat*100);x=math.floor(lng*100)
  for dy in [-1,0,1]:
   for dx in [-1,0,1]:
    for spot in grid.get((y+dy,x+dx),[]):candidates[spot['id']]=spot
 for spot in candidates.values():
  nearby=[(i,s) for i,s in enumerate(route['stops']) if abs(s['coordinate'][1]-spot['lat'])<0.007 and abs(s['coordinate'][0]-spot['lng'])<0.01]
  if not nearby:continue
  def dist(s):
   lng,lat=s['coordinate'];return math.hypot((lng-spot['lng'])*111320*math.cos(math.radians(lat)),(lat-spot['lat'])*111320)
  sequence,stop=min(nearby,key=lambda x:dist(x[1]));metres=dist(stop)
  if metres>600:continue
  linked.append({'id':spot['id'],'name':spot['name'],'nameEn':spot.get('name_en',''),'descriptionEn':spot.get('description_en',''),'category':spot.get('category','博物館・文化'),'description':spot.get('description',''),'stop':stop['name'],'walk':math.ceil(metres/70),'coordinate':[spot['lng'],spot['lat']],'photo':spot['photo'],'source':spot['source_url'],'credit':spot['photo_credit'],'license':spot['photo_license'],'photoSource':spot['photo_source'],'accessVerified':False,'coordinateKind':spot.get('coordinate_kind','代表地点・入口未確認'),'officialAccess':spot.get('official_access',''),'publisher':spot.get('publisher','Wikidata'),'dataLicense':spot.get('data_license',''),'sequence':sequence})
 route['spots']=sorted(linked,key=lambda s:s['sequence'])
featured=json.load(open('data/editorial/featured-routes.json'))
for entry in featured:
 matches=[r for r in catalog if entry['sourceId'] and r.get('sourceId')==entry['sourceId'] and (entry['matchName']==r['name'] or entry['matchName']=='__IDPREFIX720__' and r['id'].startswith('sankobus__sankobus:720_'))]
 if not matches:
  matches=[dict(id='featured:'+entry['id'],name=entry['name'],operator=entry['operator'],region=entry['region'],prefecture=entry['prefecture'],origin=entry['origin'],destination=entry['destination'],duration='公式時刻表を確認',color='#648169',tags=[],description='',official=entry['sourceUrl'],stops=[],spots=[],dataLicense='独自編集（公式情報を参照）',geometryQuality='線形データ未取得',sourceUrl=entry['sourceUrl'])];catalog.extend(matches)
 for route in matches:
  route.update(featuredName=entry['name'],featured=True,featuredReason=entry['reason'],featuredSource=entry['sourceUrl'],featuredCheckedAt=entry['checkedAt'],tourismEligible=True,tourismExclusionReason='')
  route['description']=entry['reason'];route['tags']=list(dict.fromkeys(route.get('tags',[])+['乗って楽しむ',entry['kind']]))
pathlib.Path('build/collected/catalog.json').write_text(json.dumps(catalog,ensure_ascii=False))
eligible={r['id']:r for r in catalog if (r['spots'] or r.get('featured')) and r.get('tourismEligible',True)};geometries=json.load(open('build/collected/routes.geojson'));geometries['features']=[f for f in geometries['features'] if f['properties']['id'] in eligible];pathlib.Path('build/collected/tourism-routes.geojson').write_text(json.dumps(geometries,ensure_ascii=False))
reverse={}
for r in eligible.values():
 for s in r['spots']:reverse.setdefault(s['id'],[]).append({'id':r['id'],'name':r['name']})
features=[{'type':'Feature','geometry':{'type':'Point','coordinates':[s['lng'],s['lat']]},'properties':{'id':s['id'],'name':s['name'],'nameEn':s.get('name_en',''),'descriptionEn':s.get('description_en',''),'lng':s['lng'],'lat':s['lat'],'photo':s['photo'],'credit':s['photo_credit'],'license':s['photo_license'],'photoSource':s['photo_source'],'source':s['source_url'],'category':s.get('category','博物館・文化'),'description':s.get('description',''),'publisher':s.get('publisher','Wikidata'),'dataLicense':s.get('data_license',''),'access':s.get('official_access',''),'coordinateKind':s.get('coordinate_kind','代表地点・入口未確認'),'routes':json.dumps(reverse.get(s['id'],[])[:12],ensure_ascii=False)}} for s in spots];pathlib.Path('build/collected/candidate-exports/spots.geojson').write_text(json.dumps({'type':'FeatureCollection','license':'ODbL 1.0 (combined database); individual source and photo rights retained','attribution':'© OpenStreetMap contributors; municipal publishers and individual photo credits retained','features':features},ensure_ascii=False))
print(len(spots),'licensed POIs;',len(eligible),'tourism routes;',sum(len(r['spots']) for r in eligible.values()),'published relations')

# Publish OSM-derived associations under ODbL, separately from source-specific datasets.
associations=[{'routeId':r['id'],'routeName':r['name'],'operator':r['operator'],'routeSource':r.get('sourceUrl') or r.get('official'),'routeDataLicense':r.get('dataLicense'),'spotId':s['id'],'stop':s['stop'],'coordinate':s['coordinate'],'walkMinutes':s['walk'],'sequence':s['sequence']} for r in eligible.values() for s in r['spots']]
pathlib.Path('build/collected/candidate-exports/osm-route-associations.json').write_text(json.dumps({'license':'ODbL 1.0','attribution':'© OpenStreetMap contributors; route source rights retained','associations':associations},ensure_ascii=False))

# The initial map index carries only point labels; full text and relations load on click.
point_features=[{**f,'properties':{k:v for k,v in f['properties'].items() if k in ['id','name','nameEn','source']}} for f in features]
pathlib.Path('build/collected/candidate-exports/spot-points.geojson').write_text(json.dumps({'type':'FeatureCollection','license':'ODbL 1.0','attribution':'© OpenStreetMap contributors; individual source rights retained','features':point_features},ensure_ascii=False,separators=(',',':')))
