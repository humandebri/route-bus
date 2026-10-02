#!/bin/sh
set -eu
if [ "${TILE_FORCE_REBUILD:-0}" != 1 ] && python3 - <<'PYCODE'
import hashlib,pathlib,sys
p=pathlib.Path('build/published')
stamp=p/'routes.pmtiles.source-sha256'
sys.exit(0 if (p/'routes.pmtiles').exists() and stamp.exists() and stamp.read_text().strip()==hashlib.sha256((p/'routes.geojson').read_bytes()).hexdigest() else 1)
PYCODE
then
  echo 'Publication tile source unchanged; using existing PMTiles.'
  exit 0
fi
TILE_BUILDER=${TIPPECANOE_BIN:-tippecanoe}
if ! command -v "$TILE_BUILDER" >/dev/null 2>&1 && [ -x .tools/tippecanoe ]; then
  TILE_BUILDER=.tools/tippecanoe
fi
"$TILE_BUILDER" -o build/published/routes.pmtiles -l bus_routes -Z4 -z14 --drop-densest-as-needed --force build/published/routes.geojson
python3 - <<'PYCODE'
import hashlib,pathlib
p=pathlib.Path('build/published')
(p/'routes.pmtiles.source-sha256').write_text(hashlib.sha256((p/'routes.geojson').read_bytes()).hexdigest())
PYCODE
