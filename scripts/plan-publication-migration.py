#!/usr/bin/env python3
"""Build and verify a budgeted diff from an actual D1 SQL export; no remote writes."""
import argparse,hashlib,json,pathlib,sqlite3
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('export',type=pathlib.Path,help='SQL export of the actual destination DB')
parser.add_argument('--batch-budget',type=int,default=20000,help='conservative row-write budget per batch, including indexes')
parser.add_argument('--output-dir',type=pathlib.Path,default=pathlib.Path('build/migration'))
args=parser.parse_args()
if args.batch_budget<20:parser.error('batch budget must be at least 20')
old=sqlite3.connect(':memory:');old.executescript(args.export.read_text());old.execute('PRAGMA foreign_keys=ON')
new=sqlite3.connect(':memory:')
for file in sorted(pathlib.Path('migrations').glob('*.sql')):new.executescript(file.read_text())
seed=pathlib.Path('build/published/initial-seed.sql');new.executescript(seed.read_text())
tables={'spots':['id'],'routes':['id'],'stops':['id'],'route_spots':['route_id','spot_id']}
def quote(v):
 if v is None:return 'NULL'
 if isinstance(v,(int,float)):return str(v)
 return "'"+v.replace("'","''")+"'"
def snapshot(db,table):
 cols=[r[1] for r in db.execute(f'PRAGMA table_info({table})')]
 return cols,{tuple(row[cols.index(k)] for k in tables[table]):row for row in db.execute(f'SELECT * FROM {table}')}
def where(table,key):return ' AND '.join(f'{col}={quote(value)}' for col,value in zip(tables[table],key))
changes={};ops=[];counts={}
for table in tables:
 cols,before=snapshot(old,table);target_cols,after=snapshot(new,table)
 if cols!=target_cols:raise SystemExit(f'Schema mismatch for {table}. Review schema migration separately.')
 indexes=len(list(old.execute(f'PRAGMA index_list({table})')))
 removed=set(before)-set(after);added=set(after)-set(before);changed={k for k in before.keys()&after.keys() if before[k]!=after[k]}
 changes[table]=(cols,before,after,removed,added,changed,1+indexes)
 counts[table]={'delete':len(removed),'insert':len(added),'update':len(changed)}
# Changed associations are replaced before removing their old parent rows.
for table in ['route_spots','stops','routes','spots']:
 cols,before,after,removed,added,changed,cost=changes[table]
 for key in sorted(removed|(changed if table=='route_spots' else set())):ops.append((f'DELETE FROM {table} WHERE {where(table,key)};',cost))
for table in ['spots','routes','stops','route_spots']:
 cols,before,after,removed,added,changed,cost=changes[table]
 for key in sorted(added|(changed if table=='route_spots' else set())):
  ops.append((f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join(quote(v) for v in after[key])});",cost))
 if table!='route_spots':
  for key in sorted(changed):
   assignments=','.join(f'{col}={quote(value)}' for col,value in zip(cols,after[key]) if col not in tables[table])
   ops.append((f'UPDATE {table} SET {assignments} WHERE {where(table,key)};',2*cost))
# Verify each batch with FK checking, then compare the entire target state.
batches=[];chunk=[];writes=0
for sql,cost in ops:
 if chunk and writes+cost>args.batch_budget:batches.append((chunk,writes));chunk=[];writes=0
 chunk.append(sql);writes+=cost
if chunk:batches.append((chunk,writes))
out=args.output_dir
out.mkdir(parents=True,exist_ok=True)
for stale in out.glob('batch-*.sql'):stale.unlink()
records=[]
for i,(statements,estimate) in enumerate(batches,1):
 text='BEGIN TRANSACTION;\n'+'\n'.join(statements)+'\nCOMMIT;\n'
 old.executescript(text)
 assert not old.execute('PRAGMA foreign_key_check').fetchall(),f'Foreign key failure in batch {i}'
 path=out/f'batch-{i:03}.sql';path.write_text(text)
 records.append({'file':str(path),'statements':len(statements),'estimatedWrites':estimate,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
for table in tables:assert snapshot(old,table)==snapshot(new,table),f'Diff does not reproduce target: {table}'
manifest={'sourceExportSha256':hashlib.sha256(args.export.read_bytes()).hexdigest(),'targetSeedSha256':hashlib.sha256(seed.read_bytes()).hexdigest(),'counts':counts,'estimatedWrites':sum(w for _,w in batches),'batchBudget':args.batch_budget,'batches':records,'verifiedInSQLite':True,'remoteWritesPerformed':False,'notice':'Use a fresh export. Confirm account write allowance before each batch. Batch boundaries are not daily scheduling; final rollout must coordinate code, static assets, D1 and R2.'}
(out/'plan.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in manifest.items() if k!='batches'},ensure_ascii=False,indent=2));print('Batches:',len(batches))
