#!/usr/bin/env python3
"""Collect a reproducible first set of Japanese tourism POIs (not exhaustive)."""
import urllib.request,urllib.parse,json,pathlib,time
classes={'museum':'Q33506','shrine':'Q845945','temple':'Q44539','lake':'Q23397','waterfall':'Q34038','castle':'Q23413','national-park':'Q46169'}
all_records={};queries=[]
for category,item in classes.items():
 query=f'''SELECT DISTINCT ?item ?itemLabel ?coord ?image WHERE {{ ?item wdt:P17 wd:Q17; wdt:P31/wdt:P279* wd:{item}; wdt:P625 ?coord; wdt:P18 ?image. FILTER NOT EXISTS {{ ?item wdt:P576 ?dissolved }} SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ja,en". }} }} ORDER BY ?item LIMIT 45'''
 url='https://query.wikidata.org/sparql?'+urllib.parse.urlencode({'query':query,'format':'json'})
 req=urllib.request.Request(url,headers={'User-Agent':'RouteBusMVP/0.1 open-data tourism collection','Accept':'application/sparql-results+json'})
 try:
  records=json.load(urllib.request.urlopen(req,timeout=60))['results']['bindings']
  for record in records:record['category']={'type':'literal','value':category};all_records[record['item']['value']]=record
  print(category,len(records),flush=True);queries.append({'category':category,'query':query,'count':len(records)})
 except Exception as e:queries.append({'category':category,'query':query,'error':str(e)});print(category,str(e),flush=True)
 time.sleep(.3)
pathlib.Path('data/sources/wikidata-spots.json').write_text(json.dumps({'head':{'vars':['item','itemLabel','coord','image']},'results':{'bindings':list(all_records.values())}},ensure_ascii=False))
pathlib.Path('data/sources/wikidata-queries.json').write_text(json.dumps(queries,ensure_ascii=False,indent=2))
