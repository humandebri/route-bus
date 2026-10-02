#!/usr/bin/env python3
"""Collect GTFS repository public feeds with explicit redistributable licenses.
Keeps expired feeds as source evidence, but excludes them from active catalog.
"""
import urllib.request,pathlib,json,hashlib,zipfile,csv,io,datetime,concurrent.futures,time,re,sys
root=pathlib.Path('data');(root/'raw'/'gtfs').mkdir(parents=True,exist_ok=True)
previous_path=root/'sources'/'gtfs-collection.json'
previous={(f['organization_id'],f['feed_id']):f for f in json.loads(previous_path.read_text())['feeds']} if previous_path.exists() else {}
registry='https://api.gtfs-data.jp/v2/feeds';data=json.load(urllib.request.urlopen(registry,timeout=30))['body']
(root/'sources'/'gtfs-feeds.json').write_text(json.dumps({'source':registry,'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'body':data},ensure_ascii=False))
today=datetime.date.today().strftime('%Y%m%d')
def collect(feed):
 record={k:feed.get(k) for k in ['organization_id','organization_name','feed_id','feed_name','feed_pref_id','feed_license','feed_license_url','last_updated_at','latest_feed_start_date','latest_feed_end_date','organization_web_url']}
 record['url']=f"https://api.gtfs-data.jp/v2/organizations/{feed['organization_id']}/feeds/{feed['feed_id']}/files/feed.zip?rid=current"
 if feed.get('feed_is_discontinued'):record['status']='discontinued';return record
 license=str(feed.get('feed_license','')).lower()
 if not re.fullmatch(r'cc\s*(?:by\s*\d+(?:\.\d+)?(?:\s+jp)?|0(?:\s+\d+(?:\.\d+)?)?)',license):record['status']='license-review-required';return record
 if feed.get('latest_feed_end_date','') and feed['latest_feed_end_date'].replace('-','')<today:record['status']='expired-not-downloaded';return record
 file=root/'raw'/'gtfs'/f"{feed['organization_id']}__{feed['feed_id']}.zip"
 try:
  cached=previous.get((feed['organization_id'],feed['feed_id']),{})
  if '--refresh' in sys.argv or not file.exists() or cached.get('last_updated_at')!=feed.get('last_updated_at'):
   req=urllib.request.Request(record['url'],headers={'User-Agent':'RouteBusMVP/0.1 public GTFS collection'})
   with urllib.request.urlopen(req,timeout=40) as response:
    size=response.headers.get('Content-Length')
    if size and int(size)>50_000_000:raise ValueError('Archive exceeds 50MB collection limit')
    content=response.read(50_000_001)
    if len(content)>50_000_000:raise ValueError('Archive exceeds 50MB collection limit')
   bad=zipfile.ZipFile(io.BytesIO(content)).testzip()
   if bad:raise ValueError('Corrupt archive member: '+bad)
   file.write_bytes(content)
  archive=zipfile.ZipFile(file)
  def rows(name):
   if name not in archive.namelist():return []
   return list(csv.DictReader(io.TextIOWrapper(archive.open(name),encoding='utf-8-sig')))
  info=rows('feed_info.txt');record['feed_info']=info[0] if info else {}
  end=(record['feed_info'].get('feed_end_date') or feed.get('latest_feed_end_date') or '').replace('-','');start=(record['feed_info'].get('feed_start_date') or feed.get('latest_feed_start_date') or '').replace('-','')
  record['status']='expired' if end and end<today else 'future' if start and start>today else 'downloaded'
  record['archive']=str(file);record['sha256']=hashlib.sha256(file.read_bytes()).hexdigest();record['routes']=len(rows('routes.txt'));record['stops']=len(rows('stops.txt'));record['has_shapes']='shapes.txt' in archive.namelist()
 except Exception as e:record['status']='error';record['error']=str(e)
 return record
records=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
 for n,record in enumerate(executor.map(collect,data),1):
  records.append(record)
  if n%25==0:print(f'{n}/{len(data)} reviewed; {sum(r["status"]=="downloaded" for r in records)} current feeds saved',flush=True)
  (root/'sources'/'gtfs-collection.json').write_text(json.dumps({'source':registry,'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'feeds':records},ensure_ascii=False,indent=2))
print('Complete:',{s:sum(r['status']==s for r in records) for s in sorted({r['status'] for r in records})})
