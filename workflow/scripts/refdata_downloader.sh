#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
    echo "Usage: $0 <project_name_or_path> <data_dir> <resources_dir> <genome_fasta> <genome_url>" >&2
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

[[ $# -eq 5 ]] || usage

project_path="$1"
data_dir_name="$2"
resources_dir_input="$3"
genome_fasta="$4"
genome_url="$5"

mkdir -p "$project_path"
base_dir="$(cd "$project_path" && pwd)"
resources_dir="$(cd "$resources_dir_input" && pwd)"
downloads_dir="$(dirname "$base_dir")/downloads"
data_dir="$base_dir/$data_dir_name"

mkdir -p "$data_dir"
cd "$data_dir"

log "Project root: $base_dir"
log "Data directory: $data_dir"
log "Resources directory: $resources_dir"
log "Shared downloads directory: $downloads_dir"
log "Genome FASTA: $genome_fasta"
log "Genome URL: $genome_url"

# ---------- Required filenames ----------
geo_raw_tar="GSE262754_RAW.tar"
geo_manifest_tar="GSE262754_InfiniumOmniExpress-24v1-3_files.tar.gz"
manifest_gz="GPL32421_InfiniumOmniExpress-24v1-3_A1.csv.gz"
manifest_csv="GPL32421_InfiniumOmniExpress-24v1-3_A1.csv"

geo_raw_url='https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSE262754&format=file'
geo_manifest_url='https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSE262754&format=file&file=GSE262754%5FInfiniumOmniExpress%2D24v1%2D3%5Ffiles%2Etar%2Egz&format=file'

genome_fasta_gz="${genome_fasta}.gz"

# ---------- Helper: reuse from shared downloads if present ----------
copy_from_downloads_if_available() {
    local fname="$1"
    if [[ -f "$downloads_dir/$fname" && ! -f "$data_dir/$fname" ]]; then
        log "Copying $fname from shared downloads directory..."
        cp "$downloads_dir/$fname" "$data_dir/"
    fi
}

download_if_missing() {
    local fname="$1"
    local url="$2"

    if [[ -f "$data_dir/$fname" ]]; then
        log "$fname already present locally. Skipping download."
        return 0
    fi

    copy_from_downloads_if_available "$fname"

    if [[ -f "$data_dir/$fname" ]]; then
        log "$fname successfully copied from shared downloads."
        return 0
    fi

    log "Downloading $fname..."
    wget --content-disposition --trust-server-names -O "$fname" "$url"
}

# ---------- Download or reuse GEO files ----------
download_if_missing "$geo_raw_tar" "$geo_raw_url"
download_if_missing "$geo_manifest_tar" "$geo_manifest_url"

# ---------- Extract GEO files ----------
if [[ ! -d "$data_dir/GSE262754_RAW_extracted" ]]; then
    log "Extracting $geo_raw_tar..."
    mkdir -p "$data_dir/GSE262754_RAW_extracted"
    tar -xvf "$geo_raw_tar" -C "$data_dir/GSE262754_RAW_extracted"
else
    log "GSE262754_RAW_extracted already exists. Skipping extraction."
fi

if [[ ! -d "$data_dir/GSE262754_manifest_extracted" ]]; then
    log "Extracting $geo_manifest_tar..."
    mkdir -p "$data_dir/GSE262754_manifest_extracted"
    tar -zxvf "$geo_manifest_tar" -C "$data_dir/GSE262754_manifest_extracted"
else
    log "GSE262754_manifest_extracted already exists. Skipping extraction."
fi

# ---------- Decompress IDAT files ----------
log "Decompressing IDAT files if needed..."
find "$data_dir/GSE262754_RAW_extracted" -type f -name "*.idat.gz" -print0 | while IFS= read -r -d '' f; do
    gzip -df "$f"
done

# ---------- Locate and decompress manifest CSV ----------
if [[ -f "$data_dir/GSE262754_manifest_extracted/$manifest_csv" ]]; then
    log "$manifest_csv already present."
else
    copy_from_downloads_if_available "$manifest_gz"

    if [[ -f "$data_dir/GSE262754_manifest_extracted/$manifest_gz" ]]; then
        log "Decompressing $manifest_gz..."
        gzip -df "$data_dir/GSE262754_manifest_extracted/$manifest_gz"
    else
        found_manifest_gz="$(find "$data_dir" -type f -name "$manifest_gz" | head -n 1 || true)"
        if [[ -n "$found_manifest_gz" ]]; then
            log "Copying and decompressing manifest from extracted archive..."
            cp "$found_manifest_gz" "$data_dir/GSE262754_manifest_extracted"
            gzip -df "$data_dir/GSE262754_manifest_extracted/$manifest_gz"
        else
            log "Manifest gz file not found in shared downloads or extracted archive."
        fi
    fi
fi

# ---------- Organize IDAT files by sample ----------
log "Organizing IDAT files into per-sample directories..."

find "$data_dir/GSE262754_RAW_extracted" -type f -name "*.idat" -print0 | while IFS= read -r -d '' idat_file; do
    fname="$(basename "$idat_file")"

    line_prefix="$(echo "$fname" | cut -d"_" -f1-3)"
    sample_prefix="$(echo "$fname" | cut -d"_" -f1,2)"

    sample_dir="$data_dir/$line_prefix"
    mkdir -p "$sample_dir"

    if [[ "$fname" == *_Grn.idat ]]; then
        target="$sample_dir/${sample_prefix}_Grn.idat"
    elif [[ "$fname" == *_Red.idat ]]; then
        target="$sample_dir/${sample_prefix}_Red.idat"
    else
        log "Skipping unexpected IDAT filename: $fname"
        continue
    fi

    if [[ -f "$target" ]]; then
        log "Target already exists, skipping move: $target"
    else
        mv "$idat_file" "$target"
    fi
done

# ---------- Genome setup ----------
samtools_bin="$base_dir/samtools/samtools"
genome_dir="$base_dir/genome"
mkdir -p "$genome_dir"

if [[ ! -x "$samtools_bin" ]]; then
    echo "Error: samtools executable not found or not executable: $samtools_bin" >&2
    exit 1
fi

cd "$genome_dir"

if [[ -f "$genome_dir/$genome_fasta" ]]; then
    log "$genome_fasta already present in genome directory."
else
    if [[ -f "$resources_dir/$genome_fasta" ]]; then
        log "Copying genome FASTA from resources directory..."
        cp "$resources_dir/$genome_fasta" "$genome_dir/"
    elif [[ -f "$downloads_dir/$genome_fasta" ]]; then
        log "Copying genome FASTA from shared downloads directory..."
        cp "$downloads_dir/$genome_fasta" "$genome_dir/"
    else
        log "$genome_fasta not found in resources or shared downloads."
        log "Downloading ${genome_fasta_gz} into resources directory..."

        mkdir -p "$resources_dir"

        if [[ ! -f "$resources_dir/$genome_fasta_gz" ]]; then
            wget -O "$resources_dir/$genome_fasta_gz" "$genome_url"
        else
            log "$genome_fasta_gz already exists in resources directory. Skipping download."
        fi
        
        if [[ ! -f "$resources_dir/$genome_fasta" ]]; then
            log "Decompressing $genome_fasta_gz in resources directory..."
            set +e
            gzip -df "$resources_dir/$genome_fasta_gz"
            gzip_status=$?
            set -e
 
            if [[ ! -f "$resources_dir/$genome_fasta" ]]; then
                echo "Error: failed to create $genome_fasta in resources directory." >&2
                exit 1
            fi
        
            if [[ $gzip_status -ne 0 ]]; then
                log "Warning: gzip returned non-zero status, but $genome_fasta was created successfully."
            fi
        fi

        log "Copying downloaded genome FASTA from resources directory..."
        cp "$resources_dir/$genome_fasta" "$genome_dir/"
    fi
fi

if [[ ! -f "$genome_dir/${genome_fasta}.fai" ]]; then
    log "Indexing genome FASTA with samtools faidx..."
    "$samtools_bin" faidx "$genome_dir/$genome_fasta"
else
    log "Genome FASTA index already exists. Skipping faidx."
fi

log "Data setup completed successfully."
