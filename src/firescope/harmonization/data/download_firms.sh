#!/usr/bin/env bash
# Usage:
#   ./download_firms.sh --dataset-type modis,viirs-noaa20,viirs-snpp \
#       --start-year 2018 --end-year 2025 --output-dir data/raw

set -uo pipefail

BASE_URL="https://firms.modaps.eosdis.nasa.gov/data/country/zips"

usage() {
  cat <<EOF
Usage: $0 --dataset-type LIST --start-year YYYY --end-year YYYY --output-dir DIR [--remove-zip]

  --dataset-type  Comma-separated: modis, viirs-snpp, viirs-noaa20 (alias: viirs-jpss1)
  --start-year    First year to download
  --end-year      Last year to download (inclusive)
  --output-dir    Directory for downloads and extracted files
  --remove-zip    Delete each zip after it is extracted
EOF
}

# Map user-facing dataset name to the prefix used in the file name.
# viirs-noaa20 -> viirs-jpss1 comes from the example link.
# The modis and viirs-snpp prefixes are assumed to follow the same pattern.
dataset_prefix() {
  case "$1" in
    modis)                    echo "modis" ;;
    viirs-snpp)               echo "viirs-snpp" ;;
    viirs-noaa20|viirs-jpss1) echo "viirs-jpss1" ;;
    *) return 1 ;;
  esac
}

DATASETS=""; START=""; END=""; OUT=""; REMOVE_ZIP=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dataset-type) DATASETS="${2:-}"; shift 2 ;;
    --start-year)   START="${2:-}";    shift 2 ;;
    --end-year)     END="${2:-}";      shift 2 ;;
    --output-dir)   OUT="${2:-}";      shift 2 ;;
    --remove-zip)   REMOVE_ZIP=1;      shift ;;
    -h|--help)      usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 1 ;;
  esac
done

if [[ -z "$DATASETS" || -z "$START" || -z "$END" || -z "$OUT" ]]; then
  echo "Missing required argument." >&2; usage >&2; exit 1
fi
if ! [[ "$START" =~ ^[0-9]{4}$ && "$END" =~ ^[0-9]{4}$ ]] || (( START > END )); then
  echo "Years must be 4 digits and start-year <= end-year." >&2; exit 1
fi
for tool in wget unzip; do
  command -v "$tool" >/dev/null || { echo "$tool is not installed." >&2; exit 1; }
done

ZIP_DIR="$OUT/zips"
mkdir -p "$ZIP_DIR"

failed=0
IFS=',' read -ra TYPES <<< "$DATASETS"

for type in "${TYPES[@]}"; do
  type="${type// /}"
  if ! prefix=$(dataset_prefix "$type"); then
    echo "Skipping unknown dataset type: $type" >&2
    failed=1
    continue
  fi

  for (( year=START; year<=END; year++ )); do
    name="${prefix}_${year}_all_countries"
    url="${BASE_URL}/${name}.zip"
    zip_path="${ZIP_DIR}/${name}.zip"
    extract_dir="${OUT}/${name}"

    if [[ -d "$extract_dir" ]] && [[ -n "$(ls -A "$extract_dir" 2>/dev/null)" ]]; then
      echo "[skip] $name already extracted"
      continue
    fi

    echo "[get ] $url"
    if ! wget -c -nv -O "$zip_path" "$url"; then
      echo "[fail] could not download $url" >&2
      rm -f "$zip_path"
      failed=1
      continue
    fi

    echo "[unzip] $zip_path -> $extract_dir"
    mkdir -p "$extract_dir"
    if ! unzip -q -o "$zip_path" -d "$extract_dir"; then
      echo "[fail] could not unzip $zip_path" >&2
      failed=1
      continue
    fi

    (( REMOVE_ZIP )) && rm -f "$zip_path"
  done
done

if (( failed )); then
  echo "Finished with errors." >&2
  exit 1
fi
echo "Done."
