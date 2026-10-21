#!/bin/sh
export CAMEVISION_SINGLE_ROOT="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
cd "$CAMEVISION_SINGLE_ROOT" || exit 1
if [ ! -f "$CAMEVISION_SINGLE_ROOT/tools/cv_single_setup.py" ]; then
	echo "CameVision-Single.sh must sit in the unzipped package folder (next to tools/)." >&2
	exit 1
fi
if [ -x "$CAMEVISION_SINGLE_ROOT/host/linux/python/bin/python3" ]; then
	exec "$CAMEVISION_SINGLE_ROOT/host/linux/python/bin/python3" "$CAMEVISION_SINGLE_ROOT/tools/cv_single_setup.py" --gui
fi
exec python3 "$CAMEVISION_SINGLE_ROOT/tools/cv_single_setup.py" --gui
