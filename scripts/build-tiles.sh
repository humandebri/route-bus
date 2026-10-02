#!/bin/sh
set -eu
TILE_BUILDER=${TIPPECANOE_BIN:-tippecanoe}
mkdir -p build/tiles
"$TILE_BUILDER" -o build/tiles/tourism-routes.pmtiles -l bus_routes -Z4 -z14 --drop-densest-as-needed --force build/collected/tourism-routes.geojson
