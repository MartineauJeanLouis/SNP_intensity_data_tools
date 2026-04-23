#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
    echo "Usage: $0 <project_name_or_path> <resources_dir>" >&2
    exit 1
}

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

cleanup_on_error() {
    local exit_code=$?
    echo "Error: setup failed at line ${BASH_LINENO[0]}." >&2
    exit "$exit_code"
}
trap cleanup_on_error ERR

[[ $# -eq 2 ]] || usage

project_path="$1"
resources_dir_input="$2"

mkdir -p "$project_path"
base_dir="$(cd "$project_path" && pwd)"
resources_dir="$(cd "$resources_dir_input" && pwd)"
jobs="${JOBS:-$(command -v nproc >/dev/null 2>&1 && nproc || echo 4)}"

log "Project root: $base_dir"
log "Resources directory: $resources_dir"

cd "$base_dir"

# ---------- htslib ----------
if [[ ! -d "$base_dir/htslib" ]]; then
    log "Cloning htslib..."
    git clone --recurse-submodules https://github.com/samtools/htslib.git
else
    log "htslib already exists, skipping clone."
fi

log "Building htslib..."
cd "$base_dir/htslib"
autoheader
autoreconf -i
./configure
make -j"$jobs"

# ---------- bcftools ----------
cd "$base_dir"
if [[ ! -d "$base_dir/bcftools" ]]; then
    log "Cloning bcftools..."
    git clone https://github.com/samtools/bcftools.git
else
    log "bcftools already exists, skipping clone."
fi

log "Preparing bcftools plugins..."
mkdir -p "$base_dir/bcftools/plugins"

plugin_base_url="https://raw.githubusercontent.com/freeseek/gtc2vcf/master"
plugin_files=(
    "idat2gtc.c"
    "gtc2vcf.c"
    "gtc2vcf.h"
    "affy2vcf.c"
    "BAFregress.c"
)

for f in "${plugin_files[@]}"; do
    wget -O "$base_dir/bcftools/plugins/$f" "$plugin_base_url/$f"
done

log "Building bcftools..."
cd "$base_dir/bcftools"
autoheader
autoconf
./configure --enable-perl-filters --with-htslib="$base_dir/htslib"
make -j"$jobs"

export BCFTOOLS_PLUGINS="$base_dir/bcftools/plugins"
log "BCFTOOLS_PLUGINS set to: $BCFTOOLS_PLUGINS"

# ---------- samtools ----------
cd "$base_dir"
if [[ ! -d "$base_dir/samtools" ]]; then
    log "Cloning samtools..."
    git clone https://github.com/samtools/samtools.git
else
    log "samtools already exists, skipping clone."
fi

log "Building samtools..."
cd "$base_dir/samtools"
autoheader
autoconf -Wno-syntax
./configure --with-htslib="$base_dir/htslib"
make -j"$jobs"

# ---------- iaap-cli ----------
cd "$base_dir"

iaap_tar_name="iaap-cli-linux-x64-1.1.0-sha.80d7e5b3d9c1fdfc2e99b472a90652fd3848bbc7.tar.gz"
iaap_tar_src="$resources_dir/$iaap_tar_name"
iaap_extract_dir='iaap-cli-linux-x64-1.1.0-sha.80d7e5b3d9c1fdfc2e99b472a90652fd3848bbc7'
iaap_target_dir="$base_dir/iaap-cli"
iaap_dll="$iaap_target_dir/ArrayAnalysis.NormToGenCall.Services.dll"

if [[ ! -f "$iaap_tar_src" ]]; then
    echo "Error: IAAP tarball not found in resources directory: $iaap_tar_src" >&2
    exit 1
fi

log "Copying IAAP tarball..."
cp "$iaap_tar_src" "$base_dir/"

log "Extracting IAAP CLI..."
mkdir -p "$iaap_target_dir"
tar xzf "$base_dir/$iaap_tar_name" \
    -C "$base_dir" \
    --strip-components=1 \
    "$iaap_extract_dir/iaap-cli"

if [[ ! -f "$iaap_dll" ]]; then
    echo "Error: Expected DLL not found after extraction: $iaap_dll" >&2
    exit 1
fi

log "Patching IAAP DLL..."
sed -i \
    -e ':a' \
    -e 'N' \
    -e '$!ba' \
    -e 's/\x28\x17\x01\x00\x0a\x13\x07\x12\x07\x72\xdd\x23\x00\x70\x28\x18\x01\x00\x0a/\x00\x00\x00\x00\x00\x00\x00\x00\x00\x7e\x92\x00\x00\x0a\x00\x00\x00\x00\x00/' \
    "$iaap_dll"

log "Removing copied IAAP tarball..."
rm -f "$base_dir/$iaap_tar_name"

log "Setup completed successfully."