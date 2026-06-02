#!/usr/bin/env bash
set -euo pipefail

# Render stacked SVG comparisons for two TTF files.
#
# Usage:
#   scripts/font-compare.sh previous.ttf current.ttf
#   scripts/font-compare.sh previous.ttf current.ttf --left-label v1.7 --right-label current
#
# Output defaults to out/scripts/compare/<left>-vs-<right>.svg.
#
# Env: FNTBLD_IMAGE (override container image)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${FNTBLD_IMAGE:-ghcr.io/nicoverbruggen/fntbld-oci:latest}"

if ! command -v podman >/dev/null 2>&1; then
  echo "Missing required command: podman" >&2
  exit 1
fi

podman run --rm -i -v "$ROOT_DIR":/work -w /work "$IMAGE" \
  python3 /work/scripts/font_compare.py "$@"
