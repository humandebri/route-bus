#!/usr/bin/env python3
import json,pathlib,subprocess,concurrent.futures,sys
feeds=[f for f in json.load(open('data/sources/gtfs-collection.json'))['feeds'] if f['status']=='downloaded'];out=pathlib.Path('build/collected');out.mkdir(parents=True,exist_ok=True)
if pathlib.Path('data/sources/extra-gtfs-collection.json').exists():feeds += [f for f in json.load(open('data/sources/extra-gtfs-collection.json')) if f['status']=='downloaded']
prefectures=['北海道','青森県','岩手県','宮城県','秋田県','山形県','福島県','茨城県','栃木県','群馬県','埼玉県','千葉県','東京都','神奈川県','新潟県','富山県','石川県','福井県','山梨県','長野県','岐阜県','静岡県','愛知県','三重県','滋賀県','京都府','大阪府','兵庫県','奈良県','和歌山県','鳥取県','島根県','岡山県','広島県','山口県','徳島県','香川県','愛媛県','高知県','福岡県','佐賀県','長崎県','熊本県','大分県','宮崎県','鹿児島県','沖縄県']
def build(feed):
 id=feed['organization_id']+'__'+feed['feed_id'];directory=out/id;code=int(feed.get('feed_pref_id') or 99);pref=prefectures[code-1] if 1<=code<=47 else '広域'
 region='北海道' if code==1 else '東北' if code<=7 else '関東' if code<=14 else '中部' if code<=23 else '関西' if code<=30 else '中国' if code<=35 else '四国' if code<=39 else '九州' if code<=46 else '沖縄' if code==47 else '広域'
 command=[sys.executable,'scripts/import-gtfs.py',feed['archive'],'--source-id',id,'--license',feed['feed_license'],'--region',region,'--prefecture',pref,'--output',str(directory),'--spots','data/spots.json']
 result=subprocess.run(command,capture_output=True,text=True)
 return {'id':id,'status':'built' if result.returncode==0 else 'error','error':result.stderr[-1000:] if result.returncode else '', 'directory':str(directory),'source':feed}
results=[];catalog=[];features=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for i,r in enumerate(pool.map(build,feeds),1):
  results.append(r)
  if r['status']=='built':
   docs=json.load(open(pathlib.Path(r['directory'])/'catalog.json'))
   for d in docs:d['dataUpdatedAt']=r['source']['feed_info'].get('feed_version') or r['source']['last_updated_at'];d['validUntil']=(r['source'].get('calendar_end') or r['source']['feed_info'].get('feed_end_date') or r['source'].get('latest_feed_end_date'));d['validFrom']=(r['source']['feed_info'].get('feed_start_date') or r['source'].get('latest_feed_start_date'));d['sourceUrl']=r['source']['url']
   catalog.extend(docs);features.extend(json.load(open(pathlib.Path(r['directory'])/'routes.geojson'))['features'])
  if i%50==0:print(i,'/',len(feeds),'normalized',len(catalog),'routes',flush=True)
(out/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False));(out/'routes.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features},ensure_ascii=False));(out/'build-report.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
def sql(v):return "'"+str(v).replace("'","''")+"'"
statements=['BEGIN TRANSACTION;']
for d in catalog:statements.append(f"INSERT INTO routes(id,name,region,document,active) VALUES ({sql(d['id'])},{sql(d['name'])},{sql(d['region'])},{sql(json.dumps(d,ensure_ascii=False))},1) ON CONFLICT(id) DO UPDATE SET name=excluded.name,region=excluded.region,document=excluded.document,active=1;")
statements.append('COMMIT;');(out/'seed-routes.sql').write_text('\n'.join(statements));print('Complete',len(catalog),'bus routes;',len([r for r in results if r['status']=='error']),'feed errors')
