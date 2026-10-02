#!/usr/bin/env python3
import json,pathlib,re,math
municipal=json.load(open('data/municipal-spots.json'));commons=json.load(open('data/spots.json'));by_name={}
def normalized(name):return re.sub(r'[\s　・（）()]','',name)
for spot in municipal:by_name.setdefault(normalized(spot['name']),[]).append(spot)
extra=[]
for spot in commons:
 matches=[s for s in by_name.get(normalized(spot['name']),[]) if abs(s['lat']-spot['lat'])<.002 and abs(s['lng']-spot['lng'])<.003]
 if matches:
  target=matches[0]
  if not target['photo']:
   for k in ['photo','photo_original','photo_source','photo_license','photo_license_url','photo_credit']:target[k]=spot.get(k,'')
 else:extra.append(spot)
combined=municipal+extra
osm=json.load(open('data/osm-spots.json')) if pathlib.Path('data/osm-spots.json').exists() else []
for spot in combined:by_name.setdefault(normalized(spot['name']),[]).append(spot)
osm_added=[]
for spot in osm:
 matches=[s for s in by_name.get(normalized(spot['name']),[]) if abs(s['lat']-spot['lat'])<.001 and abs(s['lng']-spot['lng'])<.0015]
 if matches:continue
 osm_added.append(spot);by_name.setdefault(normalized(spot['name']),[]).append(spot)
merged=combined+osm_added
override_path=pathlib.Path('data/spot-photo-overrides.json')
overrides=json.loads(override_path.read_text()) if override_path.exists() else {}
for spot in merged:spot.update(overrides.get(spot['id'],{}))
pathlib.Path('data/tourism-spots.json').write_text(json.dumps(merged,ensure_ascii=False,indent=2))
# Offer the full OSM extract separately, including geometry and source identifiers.
pathlib.Path('build/collected/osm-spots-source.json').write_text(json.dumps({'license':'ODbL 1.0','licenseUrl':'https://opendatacommons.org/licenses/odbl/1-0/','attribution':'© OpenStreetMap contributors','spots':osm},ensure_ascii=False))
print(len(municipal),'municipal spots;',len(extra),'Commons/Wikidata spots;',len(osm_added),'additional OSM spots')
