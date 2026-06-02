#!/usr/bin/env bash
set -euo pipefail

# Thin wrapper that runs glyph_inspect.py inside the fntbld-oci container
# (where freetype-py + pillow live). All arguments are passed straight through.
#
# Examples:
#   scripts/glyph_patches/glyph_inspect.sh outline out/ttf/Readerly-Regular.ttf nud
#   scripts/glyph_patches/glyph_inspect.sh variants out/ttf/Readerly-Regular.ttf d \
#       --region br --variant "current:" --variant "fix:37=772,76" \
#       --out out/scripts/patchdev/d-fix.png
#
# Env: FNTBLD_IMAGE (override container image)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IMAGE="${FNTBLD_IMAGE:-ghcr.io/nicoverbruggen/fntbld-oci:latest}"

if ! command -v podman >/dev/null 2>&1; then
  echo "Missing required command: podman" >&2
  exit 1
fi

podman run --rm -i -v "$ROOT_DIR":/work -w /work "$IMAGE" \
  python3 /work/scripts/glyph_patches/glyph_inspect.py "$@"
