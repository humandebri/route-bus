#!/usr/bin/env python3
"""Estimate existing-DB cleanup from the local deployed snapshot; never executes SQL."""
import json,pathlib,hashlib
root=pathlib.Path('build/published');old_routes=json.load(open('build/collected/catalog.json'));old_spots=json.load(open('data/tourism-spots.json'));new_routes=json.loads((root/'catalog.json').read_text());new_spots=json.loads((root/'spots.json').read_text())
def relations(routes):return {(r['id'],s['id']) for r in routes if r.get('tourismEligible',True) for s in r['spots']}
def stops(routes):return {'derived-stop-'+hashlib.sha256(json.dumps(r['stops'][s['sequence']],ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:20] for r in routes if r.get('tourismEligible',True) for s in r['spots']}
rows={}
for name,old,new,indexes in [('routes',{r['id'] for r in old_routes},{r['id'] for r in new_routes},1),('spots',{s['id'] for s in old_spots},{s['id'] for s in new_spots},1),('stops',stops(old_routes),stops(new_routes),1),('route_spots',relations(old_routes),relations(new_routes),2)]:
 rows[name]={'delete':len(old-new),'insert':len(new-old),'indexesPerRow':indexes}
minimum=sum((v['delete']+v['insert'])*(1+v['indexesPerRow']) for v in rows.values())
plan={'scope':'offline estimate from initial deployed snapshot; verify actual DB diff before execution','operations':rows,'estimatedDeleteAndInsertWrites':minimum,'retainedRowUpdatesIncluded':False,'freeDailyLimit':100000,'fitsOneFreeDay':minimum<=100000,'remoteExecutionAllowed':False,'notice':'既存DBからの整理は新規投入より書き込みが多い。残すレコードの更新、移行、他サービスの当日使用量は別。日別の小さな差分計画なしで実行しない。'}
(root/'existing-db-cleanup-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2));print(json.dumps(plan,ensure_ascii=False,indent=2))
