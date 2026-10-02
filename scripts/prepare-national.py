#!/usr/bin/env python3
"""Fetch and normalize MLIT 2022 national bus open data, preserving provenance."""
import urllib.request,pathlib,zipfile,io,json,hashlib,datetime
root=pathlib.Path('data');(root/'raw').mkdir(parents=True,exist_ok=True);out=pathlib.Path('build/national');out.mkdir(parents=True,exist_ok=True)
manifest={'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reference':'https://busmap.jp/about','sources':[]}
for dataset in ['N07','P11']:
 url=f'https://nlftp.mlit.go.jp/ksj/gml/data/{dataset}/{dataset}-22/{dataset}-22_SHP.zip';f=root/'raw'/f'{dataset}-22_SHP.zip'
 if not f.exists():urllib.request.urlretrieve(url,f)
 z=zipfile.ZipFile(f);features=[];prefectures=[]
 archives=[(None,z)] if dataset=='N07' else [(n,zipfile.ZipFile(io.BytesIO(z.read(n)))) for n in z.namelist() if n.endswith('.zip')]
 for name,archive in archives:
  geo=next(n for n in archive.namelist() if n.endswith('.geojson'))
  data=json.loads(archive.read(geo))
  if name:prefectures.append(name.split('_')[1])
  for i,feature in enumerate(data['features']):
   props=feature['properties']
   if dataset=='N07':normalized={'id':f'nlni-corridor-{len(features)}','operator':props['N07_001'],'note':props.get('N07_002') or '', 'year':2022,'kind':'operator-corridor'}
   else:normalized={'id':f'nlni-stop-{name.split("_")[1]}-{i}','name':props['P11_001'],'operator':props['P11_002'],'routes':' / '.join(str(v) for k,v in props.items() if k.startswith('P11_003') and v),'prefecture_code':name.split('_')[1],'year':2022}
   features.append({'type':'Feature','properties':normalized,'geometry':feature['geometry']})
 json.dump({'type':'FeatureCollection','features':features},(out/f'{dataset}.geojson').open('w'),ensure_ascii=False,separators=(',',':'))
 manifest['sources'].append({'id':dataset,'title':'国土数値情報（バスルート）' if dataset=='N07' else '国土数値情報（バス停留所）','url':url,'source_page':f'https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-{dataset}-2022.html','license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/','credit':'国土交通省 国土数値情報（2022年度）を加工して作成','sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'features':len(features),'prefectures':len(prefectures) if prefectures else 47,'warning':'2022年度のデータ。現行の運行を保証しません。N07は系統別でなく事業者単位の通行経路です。'})
 print(dataset,len(features),flush=True)
(root/'sources'/'national-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
