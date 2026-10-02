#!/usr/bin/env python3
import urllib.request,urllib.parse,json,pathlib
url='https://data.bodik.jp/api/3/action/package_search?'+urllib.parse.urlencode({'q':'title:観光 OR title:文化財 OR title:博物館 OR title:名所','rows':1000})
data=json.load(urllib.request.urlopen(url,timeout=30))
pathlib.Path('data/sources/municipal-tourism-registry.json').write_text(json.dumps(data,ensure_ascii=False));print('Municipal tourism datasets:',data['result']['count'])
