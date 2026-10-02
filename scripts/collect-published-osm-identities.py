#!/usr/bin/env python3
"""Read OSM identity/photo tags for currently shortlisted POIs from a local licensed PBF."""
import json,pathlib,osmium,collections
selected={s['id'] for s in json.load(open('build/published/spots.json')) if s['id'].startswith('osm-')}
archive=pathlib.Path('data/raw/osm/japan-latest.osm.pbf');found={};counts=collections.Counter()
processor=osmium.FileProcessor(str(archive),entities=osmium.osm.NODE|osmium.osm.WAY).with_filter(osmium.filter.KeyFilter('wikidata','wikimedia_commons','wikipedia','image'))
for obj in processor:
 identity=f'osm-{"node" if obj.is_node() else "way"}-{obj.id}'
 if identity not in selected:continue
 tags=dict(obj.tags);found[identity]={k:tags[k] for k in ('wikidata','wikimedia_commons','wikipedia','image','name') if k in tags};counts.update(k for k in found[identity] if k!='name')
pathlib.Path('data/sources/published-osm-identities.json').write_text(json.dumps({'source':'https://download.geofabrik.de/asia/japan.html','license':'ODbL 1.0','records':found},ensure_ascii=False,indent=2))
print('Published OSM identities:',len(found),'tag counts:',dict(counts),flush=True)
