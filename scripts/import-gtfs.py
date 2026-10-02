#!/usr/bin/env python3
"""Offline GTFS importer. Produces metadata SQL and separate route geometry.
Usage: python3 scripts/import-gtfs.py source.zip --source-id example --license 'CC BY 4.0' --output build/example [--spots spots.json]
Spots JSON: array of {id,name,lat,lng,description,photo}; licensed photos only.
"""
import argparse, csv, io, json, math, pathlib, zipfile
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('archive'); p.add_argument('--source-id',required=True); p.add_argument('--license',required=True); p.add_argument('--output',required=True);p.add_argument('--spots');p.add_argument('--region',default='未分類');p.add_argument('--prefecture',default='未分類');p.add_argument('--radius',type=float,default=600)
a=p.parse_args(); out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True)
z=zipfile.ZipFile(a.archive)
def rows(name,required=True):
    if name not in z.namelist():
        if required: raise ValueError(f'Missing GTFS file: {name}')
        return []
    info=z.getinfo(name)
    if info.file_size>200_000_000: raise ValueError(f'File too large: {name}; split the feed')
    return list(csv.DictReader(io.TextIOWrapper(z.open(name),encoding='utf-8-sig',newline='')))
def key(value):return a.source_id+':'+value
def sql(value):return 'NULL' if value is None else "'"+str(value).replace("'","''")+"'"
def insert(table,values):return f"INSERT INTO {table} ({','.join(values)}) VALUES ({','.join(sql(v) for v in values.values())}) ON CONFLICT DO UPDATE SET {','.join(k+'=excluded.'+k for k in values)};"
def point(row):
    lat=float(row['stop_lat']);lng=float(row['stop_lon'])
    if not (-90<=lat<=90 and -180<=lng<=180):raise ValueError('Invalid coordinate')
    return [lng,lat]
def distance(x,y):
    lng1,lat1,lng2,lat2=map(math.radians,[*x,*y]); dlat=lat2-lat1;dlng=lng2-lng1
    return 6371000*2*math.asin(min(1,math.sqrt(math.sin(dlat/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dlng/2)**2)))
stops={s['stop_id']:s for s in rows('stops.txt')}; routes=rows('routes.txt');trips=rows('trips.txt');agencies=rows('agency.txt'); times=rows('stop_times.txt'); shapes=rows('shapes.txt',False)
by_trip={};by_shape={};by_route={}
for t in trips:by_route.setdefault(t['route_id'],[]).append(t)
for s in times:by_trip.setdefault(s['trip_id'],[]).append(s)
for s in shapes:by_shape.setdefault(s['shape_id'],[]).append(s)
spots=json.loads(pathlib.Path(a.spots).read_text()) if a.spots else []
documents=[]
statements=['PRAGMA foreign_keys = ON;','BEGIN TRANSACTION;'];features=[]
for agency in agencies:statements.append(insert('operators',{'id':key(agency.get('agency_id','default')),'name':agency['agency_name'],'official_url':agency.get('agency_url')}))
for sid,s in stops.items():
    lng,lat=point(s);statements.append(insert('stops',{'id':key(sid),'name':s['stop_name'],'lat':lat,'lng':lng}))
for s in spots:statements.append(insert('spots',{'id':s['id'],'name':s['name'],'lat':s['lat'],'lng':s['lng'],'description':s.get('description','')}))
for route in routes:
    if route.get('route_type','3') not in ['3','700','701','702','703','704','705','706','707','708','709','710','711','712','713','714','715','716']:continue
    candidates=[t for t in by_route.get(route['route_id'],[]) if t['trip_id'] in by_trip]
    if not candidates:continue
    # Representative pattern: most served stops; each direction remains a separate pattern.
    representative=max(candidates,key=lambda t:len(by_trip[t['trip_id']]))
    ordered=sorted(by_trip[representative['trip_id']],key=lambda s:int(s['stop_sequence']))
    ordered=[s for s in ordered if s['stop_id'] in stops]
    if len(ordered)<2:continue
    agency=next((x for x in agencies if x.get('agency_id','default')==route.get('agency_id','default')),agencies[0])
    rid=key(route['route_id']); geometry=sorted(by_shape.get(representative.get('shape_id'),[]),key=lambda s:int(s['shape_pt_sequence']))
    coordinates=[[float(s['shape_pt_lon']),float(s['shape_pt_lat'])] for s in geometry] if geometry else [point(stops[s['stop_id']]) for s in ordered]
    linked=[]
    for spot in spots:
        if not any(abs(point(stops[s['stop_id']])[1]-spot['lat'])<0.007 and abs(point(stops[s['stop_id']])[0]-spot['lng'])<0.01 for s in ordered):continue
        best=min(enumerate(ordered),key=lambda item:distance(point(stops[item[1]['stop_id']]),[spot['lng'],spot['lat']]))
        metres=distance(point(stops[best[1]['stop_id']]),[spot['lng'],spot['lat']])
        if metres>a.radius:continue
        walk=math.ceil(metres/70);stop=stops[best[1]['stop_id']]
        linked.append({'id':spot['id'],'name':spot['name'],'category':'観光地','description':spot.get('description',''),'stop':stop['stop_name'],'walk':walk,'coordinate':[spot['lng'],spot['lat']],'photo':spot.get('photo',''),'source':spot.get('source_url'),'credit':spot.get('photo_credit'),'license':spot.get('photo_license'),'photoSource':spot.get('photo_source'),'accessVerified':False,'sequence':best[0]})
        statements.append(insert('route_spots',{'route_id':rid,'spot_id':spot['id'],'stop_id':key(best[1]['stop_id']),'walk_minutes':walk,'sequence':best[0]}))
    name=route.get('route_long_name') or route.get('route_short_name') or rid
    doc={'id':rid,'name':name,'routeShortName':route.get('route_short_name',''),'routeOfficial':route.get('route_url',''),'operatorOfficial':agency.get('agency_url',''),'region':a.region,'prefecture':a.prefecture,'operator':agency['agency_name'],'origin':stops[ordered[0]['stop_id']]['stop_name'],'destination':stops[ordered[-1]['stop_id']]['stop_name'],'duration':'公式時刻表を確認','color':'#648169','tags':[],'description':'公開GTFSの実路線データ。観光地は代表便の停留所周辺600mから抽出しています。' ,'official':agency.get('agency_url',''),'dataLicense':a.license,'geometryQuality':'GTFS shapes' if geometry else '停留所を結ぶ概略線','sourceId':a.source_id,'stops':[{'name':stops[s['stop_id']]['stop_name'],'coordinate':point(stops[s['stop_id']])} for s in ordered],'spots':sorted(linked,key=lambda s:s['sequence'])}
    documents.append(doc)
    # Parent route must precede relationships for FK checks.
    statements.insert(next((i for i,s in enumerate(statements) if s.startswith('INSERT INTO route_spots')),len(statements)),insert('routes',{'id':rid,'operator_id':key(agency.get('agency_id','default')),'name':name,'document':json.dumps(doc,ensure_ascii=False),'active':1}))
    seen=set()
    for trip in candidates:
        ts=sorted(by_trip[trip['trip_id']],key=lambda s:int(s['stop_sequence']));signature=(trip.get('direction_id','0'),tuple(s['stop_id'] for s in ts))
        if signature in seen:continue
        seen.add(signature);pid=key(trip['trip_id'])
        statements.append(insert('route_patterns',{'id':pid,'route_id':rid,'direction_id':trip.get('direction_id','0'),'shape_key':trip.get('shape_id')}))
        for i,s in enumerate(ts):
            if s['stop_id'] in stops:statements.append(insert('route_stops',{'pattern_id':pid,'stop_id':key(s['stop_id']),'sequence':i}))
    features.append({'type':'Feature','properties':{'id':rid,'color':'#648169'},'geometry':{'type':'LineString','coordinates':coordinates}})
statements.append('COMMIT;')
(out/'metadata.sql').write_text('\n'.join(statements))
(out/'catalog.json').write_text(json.dumps(documents,ensure_ascii=False))
(out/'routes.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features},ensure_ascii=False))
(out/'manifest.json').write_text(json.dumps({'source_id':a.source_id,'license':a.license,'routes':len(features),'walking':'straight-line estimate; not pedestrian routing'},indent=2))
print(f'Exported {len(features)} routes to {out}. Review metadata and licensing before publishing.')
