#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
python3 -m brand_inbox analyze
python3 -m brand_inbox evaluate --strict
printf '\nOpen artifacts/run/report.html. This demo used offline rules.\n'
