#!/usr/bin/env python3
"""Import municipality-published tourism lists from BODIK CKAN. Image rights are separate."""
import json,pathlib,urllib.request,csv,io,re,hashlib,concurrent.futures,urllib.parse,datetime
registry=json.load(open('data/sources/municipal-tourism-registry.json'))['result']['results'];root=pathlib.Path('data/raw/municipal');root.mkdir(parents=True,exist_ok=True)
def get(row,*names):
 for name in names:
  for k,v in row.items():
   if k and re.sub(r'[\s_（）()]','',k)==re.sub(r'[\s_（）()]','',name) and v:return v.strip()
 return ''
def collect(dataset):
 record={'id':dataset['name'],'title':dataset['title'],'publisher':dataset['organization']['title'],'source':'https://data.bodik.jp/dataset/'+dataset['name'],'license':dataset.get('license_id'),'updated_at':dataset.get('metadata_modified')}
 if dataset.get('license_id') not in ['cc-by-40-intl','cc-by','cc-by-40','cc-zero','cc-by-21-jp','cc-by-21','CC-BY-4.0']:record['status']='license-review-required';return record,[]
 resources=[r for r in dataset['resources'] if str(r.get('format','')).upper()=='CSV' or urllib.parse.urlparse(r['url']).path.lower().endswith('.csv')]
 if not resources:record['status']='no-csv';return record,[]
 resource=max(resources,key=lambda r:r.get('last_modified') or r.get('created') or '');record['url']=resource['url'];spots=[]
 try:
  cached=root/(dataset['name']+'.csv')
  changed_at=resource.get('last_modified') or dataset.get('metadata_modified')
  updated=datetime.datetime.fromisoformat(changed_at.replace('Z','+00:00')).replace(tzinfo=datetime.timezone.utc).timestamp() if changed_at else float('inf')
  data=cached.read_bytes() if cached.exists() and cached.stat().st_mtime>=updated else urllib.request.urlopen(resource['url'],timeout=30).read(10_000_001)
  if len(data)>10_000_000:raise ValueError('CSV exceeds 10MB limit')
  (root/(dataset['name']+'.csv')).write_bytes(data)
  text=None
  for encoding in ['utf-8-sig','cp932','utf-16']:
   try:text=data.decode(encoding);break
   except UnicodeError:pass
  if text is None:raise ValueError('Unsupported CSV encoding')
  # Some municipal files have an explanatory line before the standard header.
  lines=text.splitlines();start=next((i for i,line in enumerate(lines[:10]) if '名称' in line and ('緯度' in line or 'latitude' in line.lower())),0)
  rows=list(csv.DictReader(io.StringIO('\n'.join(lines[start:]))));record['rows']=len(rows);excluded=0
  for i,row in enumerate(rows):
   name=get(row,'名称','施設名','観光施設名','文化財名称','文化財名','スポット名','施設名称','name');lat=get(row,'緯度','latitude','施設緯度');lng=get(row,'経度','longitude','施設経度')
   if not name or not lat or not lng:excluded+=1;continue
   try:lat=float(lat);lng=float(lng)
   except ValueError:excluded+=1;continue
   if not(20<=lat<=46 and 122<=lng<=154):excluded+=1;continue
   if re.search(r'(駐車場|トイレ|市役所|町役場|消防署|警察署|保育園|バス停)$',name):excluded+=1;continue
   official=get(row,'URL','ホームページURL','施設URL');access=get(row,'アクセス方法','アクセス','交通アクセス')
   image=get(row,'画像','画像URL');image_license=get(row,'画像_ライセンス','画像ライセンス');allowed_image=image.startswith('https://') and bool(re.search(r'CC\s*[- ]?BY|CC0|パブリック',image_license,re.I))
   id='municipal-'+hashlib.sha256((name+str(round(lat,5))+str(round(lng,5))).encode()).hexdigest()[:16]
   spots.append({'id':id,'name':name,'name_en':get(row,'名称_英語','名称（英語）','英語名称','施設名英語','name_en'),'description_en':get(row,'説明_英語','説明（英語）','description_en'),'lat':lat,'lng':lng,'description':get(row,'説明','説明文','概要'),'category':'自治体の観光スポット','official_url':official if official.startswith('https://') else record['source'],'source_url':record['source'],'publisher':record['publisher'],'data_license':('CC0' if record['license']=='cc-zero' else 'CC BY 2.1 JP' if record['license'] in ['cc-by-21-jp','cc-by-21'] else 'CC BY 4.0'),'updated_at':record['updated_at'],'official_access':access,'coordinate_kind':'自治体掲載地点・入口未確認','photo':image if allowed_image else '', 'photo_original':image if allowed_image else '', 'photo_source':record['source'] if allowed_image else '', 'photo_license':image_license if allowed_image else '', 'photo_license_url':'','photo_credit':record['publisher'] if allowed_image else '', 'photo_review_status':'explicit-license' if allowed_image else 'not-licensed-or-missing','review_status':'official-tourism-list; entrance-and-walking-unverified'})
  record['status']='collected';record['accepted']=len(spots);record['excluded']=excluded;record['sha256']=hashlib.sha256(data).hexdigest()
 except Exception as e:record['status']='error';record['error']=str(e)
 return record,spots
records=[];merged={}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
 for record,spots in executor.map(collect,registry):
  records.append(record)
  for spot in spots:merged[spot['id']]=spot
pathlib.Path('data/municipal-spots.json').write_text(json.dumps(list(merged.values()),ensure_ascii=False,indent=2));pathlib.Path('data/sources/municipal-collection.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
print('Municipal sources:',len(records),'spots:',len(merged),'explicitly licensed images:',sum(bool(s['photo']) for s in merged.values()),'status:',{s:sum(r['status']==s for r in records) for s in {r['status'] for r in records}})
