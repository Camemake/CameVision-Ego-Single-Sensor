#!/bin/sh
export CAMEVISION_SINGLE_ROOT="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
cd "$CAMEVISION_SINGLE_ROOT" || exit 1
if [ ! -f "$CAMEVISION_SINGLE_ROOT/tools/cv_single_setup.py" ]; then
	echo "CameVision-Single.sh must sit in the unzipped package folder (next to tools/)." >&2
	exit 1
fi
exec "$CAMEVISION_SINGLE_ROOT/CameVision-Single" "$@"
