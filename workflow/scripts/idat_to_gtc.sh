#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
    echo "Usage: $0 <project_name_or_path> <data_dir>" >&2
    exit 1
}

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

cleanup_on_error() {
    local exit_code=$?
    echo "Error: script failed at line ${BASH_LINENO[0]}." >&2
    exit "$exit_code"
}
trap cleanup_on_error ERR

[[ $# -eq 2 ]] || usage

project_path="$1"
data_dir_name="$2"

base_dir="$(cd "$project_path" 2>/dev/null && pwd || true)"

if [[ -z "$base_dir" || ! -d "$base_dir" ]]; then
    echo "Error: project directory does not exist: $project_path" >&2
    exit 1
fi

cd "$base_dir"

log "Project root: $base_dir"

# ---------- Configurable resources ----------
data_dir="$base_dir/$data_dir_name"
output_dir="$base_dir/output"
gtc_dir="$output_dir/gtc_data"
manifest_extracted="$data_dir/GSE262754_manifest_extracted"

egt="$manifest_extracted/InfiniumOmniExpress-24v1-3_A1_ClusterFile.egt"
bpm="$manifest_extracted/InfiniumOmniExpress-24v1-3_A1.bpm"
csv_man="$manifest_extracted/GPL32421_InfiniumOmniExpress-24v1-3_A1.csv"

iaap="$base_dir/iaap-cli/iaap-cli"

threads="${THREADS:-40}"
batch_size="${BATCH_SIZE:-500000}"

mkdir -p "$gtc_dir"

# ---------- Input validation ----------
required_files=(
    "$egt"
    "$bpm"
    "$csv_man"
)

for f in "${required_files[@]}"; do
    if [[ ! -f "$f" ]]; then
        echo "Error: required file not found: $f" >&2
        exit 1
    fi
done

if [[ ! -x "$iaap" ]]; then
    echo "Error: iaap-cli not found or not executable: $iaap" >&2
    exit 1
fi

# ---------- Check input IDAT availability ----------
idat_count="$(find "$data_dir" -type f \( -name "*_Grn.idat" -o -name "*_Red.idat" \) | wc -l | tr -d ' ')"

if [[ "$idat_count" -eq 0 ]]; then
    echo "Error: no IDAT files found under $data_dir" >&2
    exit 1
fi

log "Found $idat_count IDAT files under $data_dir"
log "Output directory: $gtc_dir"
log "Using IAAP CLI: $iaap"
log "Threads: $threads"
log "Batch size: $batch_size"

# ---------- Setting System.Globalization.Invariant to true -------
export DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1

# ---------- Run Gencall ----------
log "Starting IAAP gencall..."
"$iaap" gencall "$bpm" "$egt" "$gtc_dir" \
    -f "$data_dir" \
    -g \
    -p \
    -t "$threads" \
    -b "$batch_size"

# ---------- Build GTC list ----------
gtc_list="$output_dir/gtc.list.txt"
find "$gtc_dir" -type f -name "*.gtc" | sort > "$gtc_list"

gtc_count="$(wc -l < "$gtc_list" | tr -d ' ')"

if [[ "$gtc_count" -eq 0 ]]; then
    echo "Error: no .gtc files were generated in $gtc_dir" >&2
    exit 1
fi

log "Generated $gtc_count GTC files"
log "Wrote GTC list: $gtc_list"
log "Step 3 completed successfully."
