#!/usr/bin/env python3
"""Read published GTFS English translations. Never generate names from kanji."""
import json,csv,io,zipfile,pathlib,collections
catalog=json.load(open('build/collected/catalog.json'));by_source=collections.defaultdict(list)
for r in catalog:
 if r.get('sourceId'):by_source[r['sourceId']].append(r)
count=0
feeds=json.load(open('data/sources/gtfs-collection.json'))['feeds']
if pathlib.Path('data/sources/extra-gtfs-collection.json').exists():feeds+=json.load(open('data/sources/extra-gtfs-collection.json'))
for feed in feeds:
 sid=feed['organization_id']+'__'+feed['feed_id']
 if feed['status']!='downloaded' or sid not in by_source:continue
 with zipfile.ZipFile(feed['archive']) as z:
  if 'translations.txt' not in z.namelist():continue
  def read(name):return list(csv.DictReader(io.TextIOWrapper(z.open(name),encoding='utf-8-sig'))) if name in z.namelist() else []
  stops={s['stop_id']:s['stop_name'] for s in read('stops.txt')};agencies={s.get('agency_id',''):s['agency_name'] for s in read('agency.txt')};stop_en={};agency_en={};route_en={};text_en={}
  for tr in read('translations.txt'):
   if not (tr.get('language') or tr.get('lang') or '').lower().startswith('en'):continue
   value=tr.get('translation','').strip()
   if not value:continue
   record=tr.get('record_id','');field=tr.get('field_name','');table=tr.get('table_name','')
   if tr.get('trans_id'):text_en[tr['trans_id']]=value
   if tr.get('field_value'):text_en[tr['field_value']]=value
   if table=='stops' and field=='stop_name' and record in stops:stop_en[stops[record]]=value
   if table=='agency' and field=='agency_name' and record in agencies:agency_en[agencies[record]]=value
   if table=='routes' and field in ['route_long_name','route_short_name']:
    if field=='route_long_name' or record not in route_en:route_en[record]=value
  for r in by_source[sid]:
   name=route_en.get(r['id'].split(':',1)[1]) or text_en.get(r['name'])
   if name:r['nameEn']=name;count+=1
   if agency_en.get(r['operator']) or text_en.get(r['operator']):r['operatorEn']=agency_en.get(r['operator']) or text_en[r['operator']]
   for key in ['origin','destination']:
    if stop_en.get(r[key]) or text_en.get(r[key]):r[key+'En']=stop_en.get(r[key]) or text_en[r[key]]
   for s in r['stops']:
    if stop_en.get(s['name']) or text_en.get(s['name']):s['nameEn']=stop_en.get(s['name']) or text_en[s['name']]
dictionary=json.load(open('src/i18n/en.json'))
for r in catalog:
 if r.get('featured'):
  r['featuredNameEn']=dictionary.get(r.get('featuredName',''),'')
  if r['id'].startswith('featured:'):r['nameEn']=r['featuredNameEn']
pathlib.Path('build/collected/catalog.json').write_text(json.dumps(catalog,ensure_ascii=False));print(count,'route names with published English translations')
