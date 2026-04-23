# Workflow overview

## Steps

### 1. Toolchain installation
Builds local copies of:
- htslib
- bcftools
- samtools

Downloads or installs:
- `gtc2vcf` plugin source files
- IAAP CLI from a user-provided tarball

### 2. Data and reference preparation
- downloads or reuses GEO archives
- extracts raw IDAT files
- extracts manifest resources
- organizes IDAT files into sample directories
- copies or downloads reference genome FASTA
- creates FASTA index with `samtools faidx`

### 3. IDAT to GTC
Runs IAAP `gencall` to create `.gtc` files and a `gtc.list.txt` manifest.

### 4. GTC to TSV
Uses `bcftools +gtc2vcf` to derive a tabular matrix with one column per sample and per-probe payloads:

```text
gcScore|BAF|LRR|X|Y|GT
