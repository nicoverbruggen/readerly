#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-"$ROOT_DIR/out/scripts/rasterizer/raster-reference.png"}"

TEXT="${READERLY_SAMPLE_TEXT:-"AVATAR To Wa Yo Ta Te Tr ry. office affine final fi fl. āṇ ṇu ḍha"}"
SIZES=(${READERLY_SAMPLE_SIZES:-14 16 18 20 24 28 32 36 40 44 48})
STYLE="${READERLY_SAMPLE_STYLE:-Regular}"
MARGIN="${READERLY_SAMPLE_MARGIN:-14}"

TTF_FONT="$ROOT_DIR/out/ttf/Readerly-$STYLE.ttf"
KF_FONT="$ROOT_DIR/out/kf/KF_Readerly-$STYLE.ttf"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/readerly-raster.XXXXXX")"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

need hb-view
need magick

if [[ ! -f "$TTF_FONT" ]]; then
  echo "Missing TTF font: $TTF_FONT" >&2
  echo "Run ./build.py first." >&2
  exit 1
fi

if [[ ! -f "$KF_FONT" ]]; then
  echo "Missing KF font: $KF_FONT" >&2
  echo "Run ./build.py first." >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT")"

render_row() {
  local font="$1"
  local label="$2"
  local size="$3"
  local out="$4"

  hb-view "$font" "$label $size px  $TEXT" \
    --font-size="$size" \
    --font-ppem="$size" \
    --margin="$MARGIN" \
    --foreground=000000 \
    --background=ffffff \
    --output-file="$out"
}

rows=()
for size in "${SIZES[@]}"; do
  ttf_row="$TMP_DIR/${size}-ttf.png"
  kf_row="$TMP_DIR/${size}-kf.png"
  pair_row="$TMP_DIR/${size}-pair.png"

  render_row "$TTF_FONT" "TTF" "$size" "$ttf_row"
  render_row "$KF_FONT" "KF " "$size" "$kf_row"

  magick "$ttf_row" "$kf_row" -background white -gravity west -append "$pair_row"
  rows+=("$pair_row")
done

magick "${rows[@]}" -background white -gravity west -append "$OUT"

echo "Wrote $OUT"
echo "Font style: $STYLE"
echo "Sizes: ${SIZES[*]}"
