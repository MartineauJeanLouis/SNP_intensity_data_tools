#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
    echo "Usage: $0 <project_name_or_path> <penncnv_dir>" >&2
    exit 1
}

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

cleanup_on_error() {
    local exit_code=$?
    echo "Error: PennCNV setup failed at line ${BASH_LINENO[0]}." >&2
    exit "$exit_code"
}
trap cleanup_on_error ERR

[[ $# -eq 2 ]] || usage

project_path="$1"
penncnv_dir_input="$2"

base_dir="$(cd "$project_path" 2>/dev/null && pwd || true)"
if [[ -z "$base_dir" || ! -d "$base_dir" ]]; then
    echo "Error: project directory does not exist: $project_path" >&2
    exit 1
fi

if [[ "$penncnv_dir_input" = /* ]]; then
    penncnv_dir="$penncnv_dir_input"
else
    penncnv_dir="$base_dir/$penncnv_dir_input"
fi

parent_dir="$(dirname "$penncnv_dir")"
mkdir -p "$parent_dir"

log "Project root: $base_dir"
log "PennCNV dir: $penncnv_dir"

if [[ ! -d "$penncnv_dir" ]]; then
    log "Cloning PennCNV..."
    git clone https://github.com/WGLab/PennCNV.git "$penncnv_dir"
else
    log "PennCNV already exists, skipping clone."
fi

if [[ ! -d "$penncnv_dir/kext" ]]; then
    echo "Error: PennCNV kext directory not found: $penncnv_dir/kext" >&2
    exit 1
fi

log "Compiling PennCNV kext..."
cd "$penncnv_dir/kext"
make

if [[ ! -f "$penncnv_dir/detect_cnv.pl" ]]; then
    echo "Error: detect_cnv.pl not found in $penncnv_dir" >&2
    exit 1
fi

log "PennCNV installation completed successfully."