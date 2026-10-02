#!/usr/bin/env python3
"""Build a conservative publication dataset; never mutates collected sources or remote DBs."""
import collections,copy,hashlib,json,math,pathlib,re,datetime
OUT=pathlib.Path('build/published')
def norm(text):return re.sub(r'[\s　・（）()【】「」]', '', text)
def distance(a,b):return math.hypot((a['lng']-b['lng'])*111320*math.cos(math.radians(a['lat'])),(a['lat']-b['lat'])*111320)
def facility_name(name):
 # Only group component records under explicitly identified residences.
 name=re.sub(r'[\s　]','',name)
 match=re.fullmatch(r'(.+家住宅)[（(]?(?:主屋|江戸蔵|明治蔵|蔵|阿弥陀堂|観音堂|薬医門|門|北塀|西塀|東塀|南塀|塀)[）)]?',name)
 return match[1] if match else name
NON_VISIT=re.compile(r'教室|レッスン|整骨|治療院|保育園|幼稚園|駐車場|観光協会|レンタカー')
COMMUTE=re.compile(r'スクール|通学|通勤|買い物|送迎|病院|老人|工業団地')
def organize(routes,raw_spots,as_of=None):
 as_of=as_of or datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().strftime("%Y%m%d")
 groups=collections.defaultdict(list)
 photo_overrides_path=pathlib.Path('data/editorial/photo-enrichment.json')
 photo_overrides=json.loads(photo_overrides_path.read_text()) if photo_overrides_path.exists() else {}
 for s in raw_spots:
  s={**s,**photo_overrides.get(s['id'],{})}
  groups[(s.get('publisher',''),s.get('source_url',''),norm(facility_name(s['name'])))].append(s)
 spots={};aliases={};merges=[]
 for members in groups.values():
  remaining=list(members)
  while remaining:
   first=remaining.pop(0);cluster=[first];near=[s for s in remaining if distance(first,s)<=100];cluster+=near;remaining=[s for s in remaining if s not in near]
   representative=min(cluster,key=lambda s:(not bool(s.get('photo')),s['name']!=facility_name(s['name']),len(s['name']),s['id']))
   result=copy.deepcopy(representative);result['name']=facility_name(result['name']);result['members']=[{'id':s['id'],'name':s['name'],'source':s['source_url'],'license':s.get('data_license','')} for s in cluster]
   spots[result['id']]=result
   for s in cluster:aliases[s['id']]=result['id']
   if len(cluster)>1:merges.append({'id':result['id'],'name':result['name'],'members':result['members']})
 decisions=[];published=[]
 for original in routes:
  r=copy.deepcopy(original);links={};anchors=[]
  for linked in r['spots']:
   sid=aliases[linked['id']];s=spots[sid]
   if NON_VISIT.search(s['name']):continue
   stop_record=r['stops'][linked['sequence']]
   meters=distance(s,{'lng':stop_record['coordinate'][0],'lat':stop_record['coordinate'][1]})
   if meters>600:continue
   link={**linked,'walk':math.ceil(meters/70),'id':sid,'name':s['name'],'nameEn':s.get('name_en',''),'description':s.get('description',''),'coordinate':[s['lng'],s['lat']],'photo':s.get('photo',''),'source':s['source_url'],'credit':s.get('photo_credit',''),'license':s.get('photo_license',''),'licenseUrl':s.get('photo_license_url',''),'photoSource':s.get('photo_source',''),'photoChanges':'Resized and converted to WebP' if s.get('photo') else '', 'officialAccess':s.get('official_access','')}
   if sid not in links or (link['walk'],link['sequence'])<(links[sid]['walk'],links[sid]['sequence']):links[sid]=link
   name=norm(s['name']);stop=norm(link['stop']);access=s.get('official_access','')
   exact=len(name)>=4 and (name in stop or len(stop)>=4 and stop in name)
   explicit=len(link['stop'])>=3 and link['stop'] in access and bool(re.search('バス|停留所|下車',access))
   if exact or explicit:anchors.append({'spotId':sid,'stop':link['stop'],'basis':'official-bus-access' if explicit else 'stop-place-name-match','source':s['source_url']})
  reason=''
  if r.get('validUntil') and r['validUntil'].replace('-','')<as_of:reason='expired-feed'
  elif r.get('validFrom') and r['validFrom'].replace('-','')>as_of:reason='future-feed'
  elif r.get('featured'):reason='official-scenic-selection'
  elif not r.get('tourismEligible',True):reason=r.get('tourismExclusionReason') or 'excluded-service'
  elif COMMUTE.search(r['name']):reason='生活目的を示す路線名・要個別確認'
  elif anchors:reason='destination-connected'
  elif links:reason='近傍候補のみ・観光目的未確認'
  else:reason='関連スポットなし・未選定'
  publish=reason in ['official-scenic-selection','destination-connected']
  decisions.append({'id':r['id'],'name':r['name'],'published':publish,'reason':reason,'anchors':anchors})
  if publish:
   r['spots']=sorted(links.values(),key=lambda s:(s['sequence'],s['id']));r['publicationBasis']=reason;r['publicationEvidence']=anchors
   group_key=(r.get('sourceId') or r['operator'])+'\0'+(r.get('featuredName') or r['name']);r['groupId']='route-group-'+hashlib.sha256(group_key.encode()).hexdigest()[:20]
   published.append(r)
 linked_ids={s['id'] for r in published for s in r['spots']};selected=[s for sid,s in spots.items() if sid in linked_ids]
 route_groups=collections.defaultdict(list)
 for r in published:route_groups[r['groupId']].append(r)
 group_records=[{'id':gid,'name':members[0].get('featuredName') or members[0]['name'],'operator':members[0]['operator'],'representativeId':min(members,key=lambda r:(-sum(bool(s['photo']) for s in r['spots']),-len(r['spots']),r['id']))['id'],'variantIds':[r['id'] for r in members]} for gid,members in route_groups.items()]
 report={'validatedOn':as_of,'scope':'local-only; production unchanged','policy':'official scenic selection OR stop/place name match OR official bus access; proximity alone is insufficient','inputRoutes':len(routes),'inputSpots':len(raw_spots),'publishedPatterns':len(published),'publishedRouteGroups':len(group_records),'publishedSpots':len(selected),'relations':sum(len(r['spots']) for r in published),'photoSpots':sum(bool(s.get('photo')) for s in selected),'withheldRoutes':len(routes)-len(published),'withheldSpots':len(raw_spots)-len(selected),'mergedFacilities':len(merges),'mergedRecords':sum(len(m['members'])-1 for m in merges),'routeReasons':dict(collections.Counter(d['reason'] for d in decisions)),'routes':decisions,'merges':merges,'withheldSpotIds':[s['id'] for s in raw_spots if aliases[s['id']] not in linked_ids],'notice':'地点と停留所の名称照合はアクセスの手がかりです。入口・歩行経路・営業状態は未確認です。公開待ち候補は原本として保持します。'}
 return published,selected,group_records,report

def main():
 routes=json.load(open('build/collected/catalog.json'));raw=json.load(open('data/tourism-spots.json'));routes,spots,groups,report=organize(routes,raw);report['inputDigests']={p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in ['build/collected/catalog.json','data/tourism-spots.json']+(['data/editorial/photo-enrichment.json'] if pathlib.Path('data/editorial/photo-enrichment.json').exists() else [])};OUT.mkdir(parents=True,exist_ok=True)
 for name,value in [('catalog',routes),('spots',spots),('route-groups',groups),('organization-report',report)]: (OUT/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2))
 ids={r['id'] for r in routes};geo=json.load(open('build/collected/routes.geojson'));geo['features']=[f for f in geo['features'] if f['properties']['id'] in ids]
 for feature in geo['features']:feature['properties']['groupId']=next(r['groupId'] for r in routes if r['id']==feature['properties']['id'])
 (OUT/'routes.geojson').write_text(json.dumps(geo,ensure_ascii=False,separators=(',',':')))
 points=[{'type':'Feature','geometry':{'type':'Point','coordinates':[s['lng'],s['lat']]},'properties':{'id':s['id'],'name':s['name'],'nameEn':s.get('name_en',''),'source':s['source_url']}} for s in spots]
 (OUT/'spot-points.geojson').write_text(json.dumps({'type':'FeatureCollection','license':'ODbL 1.0; individual source rights retained','attribution':'© OpenStreetMap contributors; municipal publishers','features':points},ensure_ascii=False,separators=(',',':')))
 photo_credits=[{'id':s['id'],'name':s['name'],'photo':s['photo'],'photo_credit':s['photo_credit'],'photo_source':s['photo_source'],'photo_license':s['photo_license'],'photo_license_url':s.get('photo_license_url',''),'changes':'Resized and converted to WebP'} for s in spots if s.get('photo')]
 credit_json=json.dumps(photo_credits,ensure_ascii=False,indent=2)
 for target in [OUT/'photo-credits.json']:
  target.parent.mkdir(parents=True,exist_ok=True);target.write_text(credit_json)
 print(json.dumps({k:v for k,v in report.items() if k not in ['routes','merges','withheldSpotIds']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
