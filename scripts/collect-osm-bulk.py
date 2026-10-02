#!/usr/bin/env python3
"""Extract named tourism nodes/ways from licensed Geofabrik Japan PBF offline.
Run .venv-data/bin/python scripts/collect-osm-bulk.py after downloading the PBF.
Relations from completed Overpass extracts are retained; neither source is exhaustive.
"""
import osmium,json,pathlib,datetime,collections,hashlib
from shapely.geometry import shape,Point
from shapely.strtree import STRtree
names=['北海道','青森県','岩手県','宮城県','秋田県','山形県','福島県','茨城県','栃木県','群馬県','埼玉県','千葉県','東京都','神奈川県','新潟県','富山県','石川県','福井県','山梨県','長野県','岐阜県','静岡県','愛知県','三重県','滋賀県','京都府','大阪府','兵庫県','奈良県','和歌山県','鳥取県','島根県','岡山県','広島県','山口県','徳島県','香川県','愛媛県','高知県','福岡県','佐賀県','長崎県','熊本県','大分県','宮崎県','鹿児島県','沖縄県']
categories={'attraction':'観光名所（OSM）','museum':'博物館（OSM）','viewpoint':'展望・景勝地（OSM）','zoo':'動物園（OSM）','aquarium':'水族館（OSM）','gallery':'美術館・ギャラリー（OSM）','theme_park':'テーマパーク（OSM）'}
archive=pathlib.Path('data/raw/osm/japan-latest.osm.pbf');boundary_file=pathlib.Path('data/raw/osm/prefectures.geojson');features=json.loads(boundary_file.read_text())['features'];geometries=[shape(f['geometry']) for f in features];tree=STRtree(geometries)
reader=osmium.io.Reader(str(archive));header=reader.header();snapshot=header.get('osmosis_replication_timestamp');reader.close()
prior=json.load(open('data/osm-spots.json'));spots={s['id']:s for s in prior if s.get('osm_type')=='relation'};counts=collections.Counter();invalid=0
processor=osmium.FileProcessor(str(archive),entities=osmium.osm.NODE|osmium.osm.WAY).with_locations('sparse_mem_array').with_filter(osmium.filter.TagFilter(*[('tourism',k) for k in categories]))
for o in processor:
 tags=dict(o.tags);title=tags.get('name:ja') or tags.get('name');kind=tags.get('tourism')
 if not title or kind not in categories or any(tags.get(k) in ['yes','true','1'] for k in ['disused','abandoned','demolished','removed']) or tags.get('access') in ['no','private']:continue
 if o.is_node():
  if not o.location.valid():invalid+=1;continue
  lat,lng=o.location.lat,o.location.lon;otype='node'
 else:
  points=[(n.location.lon,n.location.lat) for n in o.nodes if n.location.valid()]
  if not points or len(points)!=len(o.nodes):invalid+=1;continue
  lng=(min(p[0] for p in points)+max(p[0] for p in points))/2;lat=(min(p[1] for p in points)+max(p[1] for p in points))/2;otype='way'
 if not (20<=lat<=46 and 122<=lng<=154):continue
 point=Point(lng,lat);matches=tree.query(point,predicate='intersects');code=int(features[int(matches[0])]['properties']['shapeISO'].split('-')[1]) if len(matches)==1 else None
 id=f'osm-{otype}-{o.id}';source=f'https://www.openstreetmap.org/{otype}/{o.id}'
 spots[id]={'id':id,'name':title,'name_en':tags.get('name:en',''),'lat':lat,'lng':lng,'prefecture':names[code-1] if code else None,'prefecture_code':code,'description':tags.get('description:ja') or tags.get('description',''),'description_en':tags.get('description:en',''),'category':categories[kind],'official_url':tags.get('website') or tags.get('contact:website') or source,'source_url':source,'publisher':'OpenStreetMap contributors','data_license':'ODbL 1.0','coordinate_kind':'OSM掲載地点・入口未確認','official_access':'','photo':'','photo_original':'','photo_source':'','photo_license':'','photo_license_url':'','photo_credit':'','review_status':'community-tourism-tag; opening-and-entrance-unverified','osm_type':otype,'osm_id':o.id,'osm_tourism':kind,'osm_snapshot':snapshot,'osm_extract':'Geofabrik Japan PBF'};counts[code]+=1
 if len(spots)%1000==0:print(len(spots),'named tourism places extracted',flush=True)
pathlib.Path('data/osm-spots.json').write_text(json.dumps(list(spots.values()),ensure_ascii=False,indent=2))
hash=hashlib.sha256()
with archive.open('rb') as stream:
 for chunk in iter(lambda:stream.read(8*1024*1024),b''):hash.update(chunk)
report=dict(source='https://download.geofabrik.de/asia/japan.html',download='https://download.geofabrik.de/asia/japan-latest.osm.pbf',license='ODbL 1.0',archive=str(archive),sha256=hash.hexdigest(),bytes=archive.stat().st_size,snapshot=snapshot,collectedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),places=len(spots),invalidGeometry=invalid,prefectures=[dict(prefecture=n,prefectureCode=i+1,accepted=counts[i+1]) for i,n in enumerate(names)],unassigned=counts[None],scope='Named tourism nodes and ways nationwide; relations only from earlier regional extracts. Not complete tourism coverage.',boundarySource='https://www.geoboundaries.org/api/current/gbOpen/JPN/ADM1/',boundaryYear=2017)
pathlib.Path('data/sources/osm-bulk-collection.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('Complete:',len(spots),'OSM places;',sum(counts[i]>0 for i in range(1,48)),'prefectures;',invalid,'invalid geometries skipped',flush=True)
