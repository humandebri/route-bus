#!/usr/bin/env python3
"""Exercise missing parents, orphan cleanup, reassigned stops, batches and a no-op diff."""
import json,pathlib,sqlite3,subprocess,tempfile
with tempfile.TemporaryDirectory(prefix='route-bus-migration-') as folder:
 folder=pathlib.Path(folder);db=sqlite3.connect(':memory:')
 for file in sorted(pathlib.Path('migrations').glob('*.sql')):db.executescript(file.read_text())
 db.executescript(pathlib.Path('build/published/initial-seed.sql').read_text())
 target=folder/'target.sql';target.write_text('\n'.join(db.iterdump()))
 # Missing route and its associations must be reinserted after its parents.
 route=db.execute('SELECT route_id FROM route_spots LIMIT 1').fetchone()[0]
 db.execute('DELETE FROM route_spots WHERE route_id=?',(route,));db.execute('DELETE FROM routes WHERE id=?',(route,))
 # A place update and a stop reassignment must survive budget boundaries.
 db.execute("UPDATE spots SET name='old name' WHERE rowid=(SELECT rowid FROM spots LIMIT 1)")
 db.execute("INSERT INTO stops VALUES ('obsolete-stop','obsolete',35,135)")
 db.execute("UPDATE route_spots SET stop_id='obsolete-stop' WHERE rowid=(SELECT rowid FROM route_spots LIMIT 1)")
 db.execute("INSERT INTO routes(id,name,document) VALUES ('obsolete-route','obsolete','{}')")
 db.execute("INSERT INTO spots(id,name,lat,lng,document) VALUES ('obsolete-spot','obsolete',35,135,'{}')")
 db.execute("INSERT INTO route_spots(route_id,spot_id,stop_id,sequence) VALUES ('obsolete-route','obsolete-spot','obsolete-stop',0)")
 export=folder/'actual.sql';export.write_text('\n'.join(db.iterdump()))
 out=folder/'plan'
 def plan(source):
  subprocess.run(['python3','scripts/plan-publication-migration.py',str(source),'--batch-budget','20','--output-dir',str(out)],check=True,capture_output=True,text=True)
  return json.loads((out/'plan.json').read_text())
 result=plan(export)
 assert result['verifiedInSQLite'] and len(result['batches'])>1
 assert all(batch['estimatedWrites']<=20 for batch in result['batches'])
 assert result['counts']['routes']['insert']==1 and result['counts']['routes']['delete']==1
 assert result['counts']['route_spots']['update']==1
 noop=plan(target)
 assert noop['estimatedWrites']==0 and noop['batches']==[]
 assert not list(out.glob('batch-*.sql')),'Old batches retained after no-op plan'
 print('Migration regression checks passed: parent insertion, obsolete references, changed stop, budget boundaries, no-op.')
