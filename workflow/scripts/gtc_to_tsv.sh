#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
    echo "Usage: $0 <project_name_or_path> <data_dir> <gtc_batch_name> <genome_fasta>" >&2
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

[[ $# -eq 4 ]] || usage

project_path="$1"
data_dir_name="$2"
gtc_batch="$3"
genome_fasta="$4"

base_dir="$(cd "$project_path" 2>/dev/null && pwd || true)"
if [[ -z "$base_dir" || ! -d "$base_dir" ]]; then
    echo "Error: project directory does not exist: $project_path" >&2
    exit 1
fi

cd "$base_dir"

log "Project root: $base_dir"
log "Batch name: $gtc_batch"

export BCFTOOLS_PLUGINS="$base_dir/bcftools/plugins"
bcftools_bin="$base_dir/bcftools/bcftools"

data_dir="$base_dir/$data_dir_name"
manifest_extracted="$data_dir/GSE262754_manifest_extracted"
egt="$manifest_extracted/InfiniumOmniExpress-24v1-3_A1_ClusterFile.egt"
bpm="$manifest_extracted/InfiniumOmniExpress-24v1-3_A1.bpm"
csv_man="$manifest_extracted/GPL32421_InfiniumOmniExpress-24v1-3_A1.csv"
ref="$base_dir/genome/$genome_fasta"

input_gtc_list="$base_dir/output/gtc.list.txt"
output_dir="$base_dir/output/gtc2vcf"
output_tsv="$output_dir/${gtc_batch}.tsv"

mkdir -p "$output_dir"

required_files=(
    "$egt"
    "$bpm"
    "$csv_man"
    "$ref"
    "$input_gtc_list"
)

for f in "${required_files[@]}"; do
    if [[ ! -f "$f" ]]; then
        echo "Error: required file not found: $f" >&2
        exit 1
    fi
done

if [[ ! -x "$bcftools_bin" ]]; then
    echo "Error: bcftools not found or not executable: $bcftools_bin" >&2
    exit 1
fi

if [[ ! -d "$BCFTOOLS_PLUGINS" ]]; then
    echo "Error: bcftools plugins directory not found: $BCFTOOLS_PLUGINS" >&2
    exit 1
fi

if [[ ! -s "$input_gtc_list" ]]; then
    echo "Error: input GTC list is empty: $input_gtc_list" >&2
    exit 1
fi

gtc_count="$(wc -l < "$input_gtc_list" | tr -d ' ')"
log "Found $gtc_count GTC files listed in $input_gtc_list"

log "Extracting sample list from gtc2vcf header..."
set +o pipefail
sample_list=$(
    "$bcftools_bin" +gtc2vcf \
        --no-version \
        -Ov \
        -b "$bpm" \
        -c "$csv_man" \
        -t IGC \
        -e "$egt" \
        -g "$input_gtc_list" \
        -f "$ref" \
    | grep -m1 '^#CHROM' \
    | cut -f 10-
)
set -o pipefail

if [[ -z "$sample_list" ]]; then
    echo "Error: no sample names found in VCF header." >&2
    exit 1
fi

log "Writing TSV header..."
printf 'ID\tCHROM\tPOS\t%s\n' "$sample_list" > "$output_tsv"

log "Running gtc2vcf and formatting output..."
"$bcftools_bin" +gtc2vcf \
    --no-version \
    -Ov \
    -b "$bpm" \
    -c "$csv_man" \
    -t IGC,BAF,LRR,NORMX,NORMY,GT \
    -e "$egt" \
    -g "$input_gtc_list" \
    -f "$ref" \
| "$bcftools_bin" query \
    -f '%ID\t%CHROM\t%POS[\t%IGC|%BAF|%LRR|%NORMX|%NORMY|%GT]\n' \
>> "$output_tsv"

if [[ ! -s "$output_tsv" ]]; then
    echo "Error: output TSV was not created or is empty: $output_tsv" >&2
    exit 1
fi

line_count="$(wc -l < "$output_tsv" | tr -d ' ')"
log "Wrote output TSV: $output_tsv"
log "Output line count: $line_count"
log "Step 4 completed successfully."