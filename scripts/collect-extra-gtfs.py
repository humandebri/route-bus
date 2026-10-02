#!/usr/bin/env python3
"""Collect reviewed primary prefectural sources, rejecting expired calendars."""
import urllib.request,urllib.parse,json,pathlib,datetime,re,html,hashlib,zipfile,io,csv,subprocess,sys
sources=[('fukui',18,'https://www.pref.fukui.lg.jp/doc/dx-suishin/opendata/gtfs_jp.html','CC BY 4.0','https://creativecommons.org/licenses/by/4.0/'),('tottori',31,'https://odp-pref-tottori.tori-info.co.jp/bus.html','CC BY 2.1 JP','https://odp-pref-tottori.tori-info.co.jp/agreement.html')]
root=pathlib.Path('data/raw/extra-gtfs');root.mkdir(parents=True,exist_ok=True);records=[];today=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d')
for org,code,page,license,terms in sources:
 text=urllib.request.urlopen(page,timeout=30).read().decode('utf-8')
 links=re.findall(r'<a\b[^>]*href=[\"\x27]([^\"\x27]+)[\"\x27][^>]*>(.*?)</a>',text,re.S|re.I)
 for href,label in links:
  url=urllib.parse.urljoin(page,html.unescape(href))
  if not '.zip' in url.lower():continue
  id=hashlib.sha256(url.encode()).hexdigest()[:12];archive=root/(org+'-'+id+'.zip');record=dict(organization_id='extra-'+org,feed_id=id,feed_pref_id=code,feed_name=re.sub('<[^>]+>','',html.unescape(label)),feed_license=license,license_url=terms,source_page=page,url=url,archive=str(archive),last_updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
  try:
   if not archive.exists():
    with urllib.request.urlopen(url,timeout=45) as response:data=response.read(50_000_001)
    if len(data)>50_000_000:raise ValueError('Archive exceeds 50MB')
    archive.write_bytes(data)
   z=zipfile.ZipFile(archive)
   def rows(name):
    if name not in z.namelist():return []
    if z.getinfo(name).file_size>200_000_000:raise ValueError('Expanded file too large')
    return list(csv.DictReader(io.TextIOWrapper(z.open(name),encoding='utf-8-sig')))
   if org=='tottori':record['feed_name']=' / '.join(a['agency_name'] for a in rows('agency.txt'))
   info=rows('feed_info.txt');record['feed_info']=info[0] if info else {}
   dates=[r.get('end_date','') for r in rows('calendar.txt')]+[r.get('date','') for r in rows('calendar_dates.txt') if r.get('exception_type')=='1'];end=record['feed_info'].get('feed_end_date') or max(dates,default='')
   record['calendar_end']=end
   if not end:record['status']='validity-unconfirmed'
   elif end<today:record['status']='expired'
   else:record['status']='downloaded'
   record['sha256']=hashlib.sha256(archive.read_bytes()).hexdigest()
  except Exception as e:record.update(status='error',error=str(e))
  records.append(record);print(org,record['feed_name'],record['status'],record.get('calendar_end',''),flush=True)
  pathlib.Path('data/sources/extra-gtfs-collection.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
