#!/usr/bin/env python3
"""Replace only the isolated local preview. Never contacts production."""
import subprocess,pathlib,sys
root=pathlib.Path('build/published')
if not (root/'map-version.json').exists():raise SystemExit('Run pnpm data:prepare first.')
subprocess.run(['python3','scripts/validate-published-data.py','--assets'],check=True)
if '--photos-only' not in sys.argv:
 # Replacing the preview is repeatable. The initial seed remains empty-DB-only.
 seed=(root/'initial-seed.sql').read_text().replace('BEGIN TRANSACTION;','BEGIN TRANSACTION;\nDELETE FROM route_spots;\nDELETE FROM stops;\nDELETE FROM routes;\nDELETE FROM spots;')
 (root/'local-preview-seed.sql').write_text(seed)
 command=['node','node_modules/wrangler/bin/wrangler.js','d1','execute','bus-map','--local','--persist-to','.wrangler/organized-preview']
 for file in ['migrations/0001.sql','migrations/0002.sql',str(root/'local-preview-seed.sql')]:
  # Migrations are applied only when the preview schema is absent.
  if file.startswith('migrations/'):
   import json
   result=subprocess.run(command+['--command','PRAGMA table_info(spots)','--json'],capture_output=True,text=True)
   if result.returncode:raise SystemExit(result.stderr or result.stdout)
   columns=json.loads(result.stdout)[0]['results']
   if file.endswith('0001.sql') and columns:continue
   if file.endswith('0002.sql') and any(c['name']=='document' for c in columns):continue
  subprocess.run(command+['--file',file],check=True)
subprocess.run(['node','scripts/load-publication-r2.mjs'],check=True)
