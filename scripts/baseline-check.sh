#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${1:-"$ROOT_DIR/out/scripts/baseline"}"

SAMPLE_TEXT="${READERLY_BASELINE_TEXT:-abcdefghijklmnopqrstuvwxyz}"
PROBE_A="${READERLY_BASELINE_PROBE_A:-ne}"
PROBE_B="${READERLY_BASELINE_PROBE_B:-ce}"
PROBE_CHARS=(${READERLY_BASELINE_PROBE_CHARS:-n c e})
REFERENCE_PROBE="${READERLY_BASELINE_REFERENCE_PROBE:-n}"
MEASURE_TEXT="${READERLY_BASELINE_MEASURE_TEXT:-abcdefghijklmnopqrstuvwxyz}"
DESCENDER_CHARS=(${READERLY_BASELINE_DESCENDERS:-g j p q y})
SIZES=(${READERLY_BASELINE_SIZES:-12 18 24 32 48 64 90})
STYLE="${READERLY_BASELINE_STYLE:-Regular}"
MARGIN="${READERLY_BASELINE_MARGIN:-40}"
JSON_REPORT="$OUT_DIR/baseline-measurements.json"

TTF_FONT="$ROOT_DIR/out/ttf/Readerly-$STYLE.ttf"
KF_FONT="$ROOT_DIR/out/kf/KF_Readerly-$STYLE.ttf"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/readerly-baseline.XXXXXX")"
MEASUREMENTS_TSV="$TMP_DIR/measurements.tsv"

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
  echo "Run the build first." >&2
  exit 1
fi

if [[ ! -f "$KF_FONT" ]]; then
  echo "Missing KF font: $KF_FONT" >&2
  echo "Run the build first." >&2
  exit 1
fi

mkdir -p "$OUT_DIR"
: > "$MEASUREMENTS_TSV"

is_descender() {
  local char="$1"
  local descender

  for descender in "${DESCENDER_CHARS[@]}"; do
    if [[ "$char" == "$descender" ]]; then
      return 0
    fi
  done
  return 1
}

render() {
  local font="$1"
  local text="$2"
  local size="$3"
  local out="$4"

  hb-view "$font" "$text" \
    --font-size="$size" \
    --font-ppem="$size" \
    --margin="$MARGIN" \
    --foreground=000000 \
    --background=ffffff \
    --output-file="$out"
}

measure_bottom() {
  local png="$1"
  local geom h y

  geom="$(magick "$png" -negate -threshold 1% -format '%@' info:)"
  h="${geom#*x}"
  h="${h%%+*}"
  y="${geom##*+}"
  echo $((y + h))
}

make_family_row() {
  local label="$1"
  local font="$2"
  local size="$3"
  local out="$4"

  render "$font" "$label $size px  $SAMPLE_TEXT" "$size" "$out"
}

make_probe() {
  local label="$1"
  local font="$2"
  local text="$3"
  local size="$4"
  local out="$TMP_DIR/$label.png"

  render "$font" "$text" "$size" "$out"
  measure_bottom "$out"
}

make_size_check() {
  local size="$1"
  local out="$OUT_DIR/baseline-alphabet-${size}px.png"
  local ttf_row="$TMP_DIR/ttf-row-$size.png"
  local kf_row="$TMP_DIR/kf-row-$size.png"

  make_family_row "TTF" "$TTF_FONT" "$size" "$ttf_row"
  make_family_row "KF " "$KF_FONT" "$size" "$kf_row"

  local ttf_row_bottom kf_row_bottom
  local ttf_a_bottom ttf_b_bottom kf_a_bottom kf_b_bottom
  local ttf_reference_bottom kf_reference_bottom
  ttf_row_bottom="$(measure_bottom "$ttf_row")"
  kf_row_bottom="$(measure_bottom "$kf_row")"
  ttf_a_bottom="$(make_probe "ttf-a-$size" "$TTF_FONT" "$PROBE_A" "$size")"
  ttf_b_bottom="$(make_probe "ttf-b-$size" "$TTF_FONT" "$PROBE_B" "$size")"
  kf_a_bottom="$(make_probe "kf-a-$size" "$KF_FONT" "$PROBE_A" "$size")"
  kf_b_bottom="$(make_probe "kf-b-$size" "$KF_FONT" "$PROBE_B" "$size")"
  ttf_reference_bottom="$(make_probe "ttf-reference-$size" "$TTF_FONT" "$REFERENCE_PROBE" "$size")"
  kf_reference_bottom="$(make_probe "kf-reference-$size" "$KF_FONT" "$REFERENCE_PROBE" "$size")"

  magick "$ttf_row" "$kf_row" -background white -gravity west -append "$out"

  local width row_height
  width="$(magick identify -format '%w' "$out")"
  row_height="$(magick identify -format '%h' "$ttf_row")"
  magick "$out" \
    -stroke red \
    -strokewidth 1 \
    -draw "line 0,$ttf_reference_bottom $((width - 1)),$ttf_reference_bottom line 0,$((row_height + kf_reference_bottom)) $((width - 1)),$((row_height + kf_reference_bottom))" \
    "$out"

  echo "Wrote $out"
  echo "Font style: $STYLE"
  echo "Size: $size px"
  echo "Sample: $SAMPLE_TEXT"
  echo "Probe: $PROBE_A vs $PROBE_B"
  echo "Reference line: bottom of $REFERENCE_PROBE"
  echo "TTF row bottom: $ttf_row_bottom"
  echo "KF  row bottom: $kf_row_bottom"
  echo "TTF reference bottom: $ttf_reference_bottom"
  echo "KF  reference bottom: $kf_reference_bottom"
  echo "TTF $PROBE_A bottom: $ttf_a_bottom"
  echo "TTF $PROBE_B bottom: $ttf_b_bottom"
  echo "KF  $PROBE_A bottom: $kf_a_bottom"
  echo "KF  $PROBE_B bottom: $kf_b_bottom"

  for probe_char in "${PROBE_CHARS[@]}"; do
    ttf_char_bottom="$(make_probe "ttf-char-$probe_char-$size" "$TTF_FONT" "$probe_char" "$size")"
    kf_char_bottom="$(make_probe "kf-char-$probe_char-$size" "$KF_FONT" "$probe_char" "$size")"
    echo "TTF $probe_char bottom: $ttf_char_bottom"
    echo "KF  $probe_char bottom: $kf_char_bottom"
  done

  echo "Character measurements:"
  seen_chars=""
  while IFS= read -r char; do
    [[ -z "$char" || "$char" == " " ]] && continue
    if [[ "$seen_chars" == *"|$char|"* ]]; then
      continue
    fi
    seen_chars="$seen_chars|$char|"
    safe_name="$(printf '%s' "$char" | LC_ALL=C tr -c 'A-Za-z0-9_.-' '_')"
    ttf_char_bottom="$(make_probe "ttf-measure-$safe_name-$size" "$TTF_FONT" "$char" "$size")"
    kf_char_bottom="$(make_probe "kf-measure-$safe_name-$size" "$KF_FONT" "$char" "$size")"
    ttf_delta=$((ttf_char_bottom - ttf_reference_bottom))
    kf_delta=$((kf_char_bottom - kf_reference_bottom))
    char_class="normal"
    if is_descender "$char"; then
      char_class="descender"
    fi
    printf '  %s  TTF:%s  KF:%s\n' "$char" "$ttf_char_bottom" "$kf_char_bottom"
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$size" "$char" "$char_class" \
      "$ttf_char_bottom" "$kf_char_bottom" \
      "$ttf_reference_bottom" "$kf_reference_bottom" \
      "$ttf_delta/$kf_delta" >> "$MEASUREMENTS_TSV"
  done < <(printf '%s' "$MEASURE_TEXT" | perl -CS -MUnicode::Normalize -ne 'binmode STDOUT, ":utf8"; print "$_\n" for split //')
  echo

  generated_rows+=("$out")
}

generated_rows=()
for size in "${SIZES[@]}"; do
  make_size_check "$size"
done

if ((${#generated_rows[@]})); then
  magick "${generated_rows[@]}" -background white -gravity west -append "$OUT_DIR/baseline-alphabet-all-sizes.png"
  echo "Wrote $OUT_DIR/baseline-alphabet-all-sizes.png"
fi

STYLE="$STYLE" \
SAMPLE_TEXT="$SAMPLE_TEXT" \
REFERENCE_PROBE="$REFERENCE_PROBE" \
MEASURE_TEXT="$MEASURE_TEXT" \
SIZES="${SIZES[*]}" \
DESCENDERS="${DESCENDER_CHARS[*]}" \
perl -CS - "$MEASUREMENTS_TSV" "$JSON_REPORT" <<'PERL'
use strict;
use warnings;

my ($tsv, $json_path) = @ARGV;

sub json_string {
    my ($value) = @_;
    $value =~ s/\\/\\\\/g;
    $value =~ s/"/\\"/g;
    $value =~ s/\n/\\n/g;
    $value =~ s/\r/\\r/g;
    $value =~ s/\t/\\t/g;
    return qq{"$value"};
}

sub json_array_strings {
    return "[" . join(", ", map { json_string($_) } @_) . "]";
}

my @size_order = split /\s+/, $ENV{SIZES};
my %size_seen = map { $_ => 1 } @size_order;
my %by_size;
my %char_order;
my %char_seen;

open my $fh, "<:encoding(UTF-8)", $tsv or die "Cannot read $tsv: $!";
while (my $line = <$fh>) {
    chomp $line;
    next if $line eq "";
    my ($size, $char, $class, $ttf, $kf, $ttf_ref, $kf_ref, $deltas) = split /\t/, $line;
    my ($ttf_delta, $kf_delta) = split /\//, $deltas;

    push @size_order, $size unless $size_seen{$size}++;
    push @{ $char_order{$size} }, $char unless $char_seen{$size}{$char}++;

    $by_size{$size}{reference_bottom}{ttf} = 0 + $ttf_ref;
    $by_size{$size}{reference_bottom}{kf} = 0 + $kf_ref;
    $by_size{$size}{characters}{$char} = {
        class => $class,
        ttf => 0 + $ttf,
        kf => 0 + $kf,
        ttf_delta => 0 + $ttf_delta,
        kf_delta => 0 + $kf_delta,
    };

    push @{ $by_size{$size}{groups}{ttf}{$ttf_delta} }, $char;
    push @{ $by_size{$size}{groups}{kf}{$kf_delta} }, $char;
    push @{ $by_size{$size}{discrepancies}{ttf}{normal} }, $char
        if $class eq "normal" && $ttf_delta != 0;
    push @{ $by_size{$size}{discrepancies}{kf}{normal} }, $char
        if $class eq "normal" && $kf_delta != 0;
}
close $fh;

open my $out, ">:encoding(UTF-8)", $json_path or die "Cannot write $json_path: $!";
print $out "{\n";
print $out "  \"style\": " . json_string($ENV{STYLE}) . ",\n";
print $out "  \"sample_text\": " . json_string($ENV{SAMPLE_TEXT}) . ",\n";
print $out "  \"measure_text\": " . json_string($ENV{MEASURE_TEXT}) . ",\n";
print $out "  \"reference_probe\": " . json_string($ENV{REFERENCE_PROBE}) . ",\n";
print $out "  \"descenders\": " . json_array_strings(split /\s+/, $ENV{DESCENDERS}) . ",\n";
print $out "  \"sizes\": [" . join(", ", map { 0 + $_ } @size_order) . "],\n";
print $out "  \"results\": [\n";

for my $si (0 .. $#size_order) {
    my $size = $size_order[$si];
    my $data = $by_size{$size};
    print $out "    {\n";
    print $out "      \"size_px\": " . (0 + $size) . ",\n";
    print $out "      \"output_png\": " . json_string("baseline-alphabet-${size}px.png") . ",\n";
    print $out "      \"reference_bottom\": {\"ttf\": $data->{reference_bottom}{ttf}, \"kf\": $data->{reference_bottom}{kf}},\n";
    print $out "      \"characters\": {\n";
    my @chars = @{ $char_order{$size} || [] };
    for my $ci (0 .. $#chars) {
        my $char = $chars[$ci];
        my $m = $data->{characters}{$char};
        print $out "        " . json_string($char) . ": ";
        print $out "{\"class\": " . json_string($m->{class}) .
            ", \"ttf\": $m->{ttf}, \"kf\": $m->{kf}" .
            ", \"ttf_delta\": $m->{ttf_delta}, \"kf_delta\": $m->{kf_delta} }";
        print $out "," if $ci < $#chars;
        print $out "\n";
    }
    print $out "      },\n";

    print $out "      \"groups_by_delta\": {\n";
    for my $renderer_i (0, 1) {
        my $renderer = $renderer_i == 0 ? "ttf" : "kf";
        print $out "        " . json_string($renderer) . ": {\n";
        my @deltas = sort { $a <=> $b } keys %{ $data->{groups}{$renderer} || {} };
        for my $di (0 .. $#deltas) {
            my $delta = $deltas[$di];
            print $out "          " . json_string($delta) . ": " .
                json_array_strings(@{ $data->{groups}{$renderer}{$delta} });
            print $out "," if $di < $#deltas;
            print $out "\n";
        }
        print $out "        }";
        print $out "," if $renderer_i == 0;
        print $out "\n";
    }
    print $out "      },\n";

    print $out "      \"normal_discrepancies\": {\n";
    my @ttf_norm = @{ $data->{discrepancies}{ttf}{normal} || [] };
    my @kf_norm = @{ $data->{discrepancies}{kf}{normal} || [] };
    print $out "        \"ttf\": " . json_array_strings(@ttf_norm) . ",\n";
    print $out "        \"kf\": " . json_array_strings(@kf_norm) . "\n";
    print $out "      }\n";
    print $out "    }";
    print $out "," if $si < $#size_order;
    print $out "\n";
}

print $out "  ]\n";
print $out "}\n";
close $out;
PERL

echo "Wrote $JSON_REPORT"
