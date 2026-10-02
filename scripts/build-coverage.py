#!/usr/bin/env python3
"""Evidence-based prefecture counts; never equate a nonzero count with completeness."""
import json,pathlib,re,collections,runpy,sys
names=['北海道','青森県','岩手県','宮城県','秋田県','山形県','福島県','茨城県','栃木県','群馬県','埼玉県','千葉県','東京都','神奈川県','新潟県','富山県','石川県','福井県','山梨県','長野県','岐阜県','静岡県','愛知県','三重県','滋賀県','京都府','大阪府','兵庫県','奈良県','和歌山県','鳥取県','島根県','岡山県','広島県','山口県','徳島県','香川県','愛媛県','高知県','福岡県','佐賀県','長崎県','熊本県','大分県','宮崎県','鹿児島県','沖縄県']
organized='--published' in sys.argv
spots=json.load(open('build/published/spots.json' if organized else 'data/tourism-spots.json'));routes=json.load(open('build/collected/catalog.json'))
published_ids={r['id'] for r in json.load(open('build/published/catalog.json'))} if organized else set()
english=['Hokkaido','Aomori','Iwate','Miyagi','Akita','Yamagata','Fukushima','Ibaraki','Tochigi','Gunma','Saitama','Chiba','Tokyo','Kanagawa','Niigata','Toyama','Ishikawa','Fukui','Yamanashi','Nagano','Gifu','Shizuoka','Aichi','Mie','Shiga','Kyoto','Osaka','Hyogo','Nara','Wakayama','Tottori','Shimane','Okayama','Hiroshima','Yamaguchi','Tokushima','Kagawa','Ehime','Kochi','Fukuoka','Saga','Nagasaki','Kumamoto','Oita','Miyazaki','Kagoshima','Okinawa']
rows={n:dict(prefecture=n,prefectureEn=english[i],prefectureCode=i+1,gtfsRoutes=0,publishedRoutes=0,municipalSpots=0,osmSpots=0,spots=0) for i,n in enumerate(names)}
unassigned=0
for s in spots:
 n=s.get('prefecture');code=s.get('prefecture_code');m=re.search(r'/dataset/(\d{2})\d{3,4}',s.get('source_url',''))
 if not n and not code and m:code=int(m[1])
 if not n and code and 1<=int(code)<=47:n=names[int(code)-1]
 if n not in rows:
  matched=[p for p in names if p in s.get('publisher','')]
  n=matched[0] if len(matched)==1 else None
 if n not in rows:unassigned+=1;continue
 row=rows[n];row['spots']+=1
 if s['id'].startswith('osm-'):row['osmSpots']+=1
 elif s['id'].startswith('municipal'):row['municipalSpots']+=1
for r in routes:
 for n in names:
  if n in r.get('prefecture',''):
   rows[n]['gtfsRoutes']+=int(not r['id'].startswith('featured:'))
   rows[n]['publishedRoutes']+=int(r['id'] in published_ids) if organized else int(bool(r.get('spots') or r.get('featured')) and r.get('tourismEligible',True))
report=dict(prefectures=list(rows.values()),unassignedSpots=unassigned,notice='件数は収集済みの範囲です。1件以上あっても都道府県の全路線・全観光地を網羅したことを意味しません。')
for path in ['build/published/coverage.json'] if organized else ['src/data/coverage.json','public/data/coverage.json']:pathlib.Path(path).write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('Coverage:',sum(r['publishedRoutes']>0 for r in rows.values()),'prefectures with published routes;',sum(r['spots']>0 for r in rows.values()),'with assigned places;',unassigned,'unassigned places')
