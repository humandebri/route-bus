#!/usr/bin/env python3
"""Sequential, cached prefectural tourism queries. OSM data is separately exported under ODbL."""
import urllib.request,urllib.parse,json,pathlib,datetime,time,hashlib,sys,os
names=['北海道','青森県','岩手県','宮城県','秋田県','山形県','福島県','茨城県','栃木県','群馬県','埼玉県','千葉県','東京都','神奈川県','新潟県','富山県','石川県','福井県','山梨県','長野県','岐阜県','静岡県','愛知県','三重県','滋賀県','京都府','大阪府','兵庫県','奈良県','和歌山県','鳥取県','島根県','岡山県','広島県','山口県','徳島県','香川県','愛媛県','高知県','福岡県','佐賀県','長崎県','熊本県','大分県','宮崎県','鹿児島県','沖縄県']
categories={'attraction':'観光名所（OSM）','museum':'博物館（OSM）','viewpoint':'展望・景勝地（OSM）','zoo':'動物園（OSM）','aquarium':'水族館（OSM）','gallery':'美術館・ギャラリー（OSM）','theme_park':'テーマパーク（OSM）'}
# Respect a cooldown after 429 across invocations; do not rotate endpoints.
previous=pathlib.Path('data/sources/osm-collection.json')
if '--cached-only' not in sys.argv and previous.exists() and any(r.get('error','').startswith('HTTP Error 429') for r in json.loads(previous.read_text())) and time.time()-previous.stat().st_mtime<300:
 raise SystemExit('Provider cooldown active: wait at least five minutes before resuming.')
endpoint='https://overpass-api.de/api/interpreter';root=pathlib.Path('data/raw/osm');root.mkdir(parents=True,exist_ok=True);records=[];spots={}
boundary_path=pathlib.Path('data/raw/osm/prefectures.geojson')
if not boundary_path.exists() and '--cached-only' not in sys.argv:
 metadata=json.load(urllib.request.urlopen('https://www.geoboundaries.org/api/current/gbOpen/JPN/ADM1/',timeout=30))
 if metadata.get('boundaryLicense')!='Open Data Commons Open Database License 1.0' or str(metadata.get('admUnitCount'))!='47':raise ValueError('Boundary metadata requires review')
 boundary_path.write_bytes(urllib.request.urlopen(metadata['simplifiedGeometryGeoJSON'],timeout=60).read(10_000_000))
 pathlib.Path('data/sources/prefecture-boundaries.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
boundaries={f['properties']['shapeISO']:f['geometry'] for f in json.loads(boundary_path.read_text())['features']} if boundary_path.exists() else {}
def polygons(g):return [g['coordinates']] if g['type']=='Polygon' else g['coordinates']
def in_ring(lng,lat,ring):
 inside=False
 for a,b in zip(ring,ring[1:]):
  if (a[1]>lat)!=(b[1]>lat) and lng<(b[0]-a[0])*(lat-a[1])/(b[1]-a[1])+a[0]:inside=not inside
 return inside
def within(lng,lat,g):return any(in_ring(lng,lat,p[0]) and not any(in_ring(lng,lat,hole) for hole in p[1:]) for p in polygons(g))
# Process cached regions before network requests, so partial failures never discard them.
order=sorted(enumerate(names,1),key=lambda pair:(not (root/f'JP-{pair[0]:02}.json').exists(),0 if pair[0]==31 else pair[0]))
for code,name in order:
 boundary=boundaries.get(f'JP-{code:02}')
 if boundary:
  points=[p for poly in polygons(boundary) for ring in poly for p in ring];bbox=f"{min(p[1] for p in points)},{min(p[0] for p in points)},{max(p[1] for p in points)},{max(p[0] for p in points)}"
  query=f'[out:json][timeout:25];nwr["tourism"]["name"]({bbox});out center tags;'
 else:
  query=f'[out:json][timeout:25];area["ISO3166-2"="JP-{code:02}"]["admin_level"="4"]->.a;('+''.join(f'nwr["tourism"="{kind}"]["name"](area.a);' for kind in categories)+');out center tags;'
 cache=root/f'JP-{code:02}.json';record={'prefecture':name,'prefectureCode':code,'source':endpoint,'query':query,'license':'ODbL 1.0'}
 if '--cached-only' in sys.argv and not cache.exists():
  record['status']='not-collected';records.append(record);continue
 try:
  if cache.exists():data=json.loads(cache.read_text())
  else:
   req=urllib.request.Request(endpoint+'?'+urllib.parse.urlencode({'data':query}),headers={'User-Agent':'BusJourneyJapan/0.1 tourism research; sequential cached requests'})
   with urllib.request.urlopen(req,timeout=40) as response:raw=response.read(25_000_001)
   if len(raw)>25_000_000:raise ValueError('Response exceeds 25MB limit')
   data=json.loads(raw)
   data['bus_journey_query']=query;data['bus_journey_bbox']=bool(boundary)
   if data.get('remark'):raise ValueError(data['remark'])
   cache.write_text(json.dumps(data,ensure_ascii=False));time.sleep(10)
  accepted=0
  for element in data.get('elements',[]):
   tags=element.get('tags',{});point=element.get('center',element);kind=tags.get('tourism');title=tags.get('name:ja') or tags.get('name')
   if kind not in categories or not title or any(tags.get(k) in ['yes','true','1'] for k in ['disused','abandoned','demolished','removed']) or tags.get('access') in ['no','private']:continue
   lat,lng=point.get('lat'),point.get('lon')
   if lat is None or lng is None or not(20<=lat<=46 and 122<=lng<=154):continue
   if data.get('bus_journey_bbox') and boundary and not within(lng,lat,boundary):continue
   id=f"osm-{element['type']}-{element['id']}";source=f"https://www.openstreetmap.org/{element['type']}/{element['id']}"
   spots[id]={'id':id,'name':title,'name_en':tags.get('name:en',''),'lat':lat,'lng':lng,'prefecture':name,'prefecture_code':code,'description':tags.get('description:ja') or tags.get('description',''),'description_en':tags.get('description:en',''),'category':categories[kind],'official_url':tags.get('website') or tags.get('contact:website') or source,'source_url':source,'publisher':'OpenStreetMap contributors','data_license':'ODbL 1.0','coordinate_kind':'OSM掲載地点・入口未確認','official_access':'','photo':'','photo_original':'','photo_source':'','photo_license':'','photo_license_url':'','photo_credit':'','review_status':'community-tourism-tag; opening-and-entrance-unverified','osm_type':element['type'],'osm_id':element['id'],'osm_tourism':kind,'osm_snapshot':data.get('osm3s',{}).get('timestamp_osm_base')};accepted+=1
  record['query']=data.get('bus_journey_query') or 'Legacy prefectural area query; archive retained'
  if data.get('bus_journey_bbox'):record['boundarySource']='https://www.geoboundaries.org/api/current/gbOpen/JPN/ADM1/';record['boundaryYear']=2017
  record.update(status='collected',accepted=accepted,snapshot=data.get('osm3s',{}).get('timestamp_osm_base'),sha256=hashlib.sha256(cache.read_bytes()).hexdigest())
 except Exception as error:
  record.update(status='error',error=str(error));time.sleep(10);print(name,'ERROR',str(error),flush=True)
  # Do not evade provider rate limits. Keep completed regions and stop on HTTP 429.
  if getattr(error,'code',None)==429:records.append(record);break
 records.append(record);print(code,name,record.get('accepted',0),'spots;',len(spots),'total',flush=True)
 pathlib.Path('data/osm-spots.json').write_text(json.dumps(list(spots.values()),ensure_ascii=False,indent=2));pathlib.Path('data/sources/osm-collection.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
pathlib.Path('data/osm-spots.json').write_text(json.dumps(list(spots.values()),ensure_ascii=False,indent=2));pathlib.Path('data/sources/osm-collection.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
