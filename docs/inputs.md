```markdown
# Inputs

## Required logical inputs

- Illumina IDAT files
- manifest resources:
  - `.egt`
  - `.bpm`
  - manifest `.csv`
- reference genome FASTA

## Current expected layout

The current workflow scripts assume a GEO-derived layout and currently use manifest files extracted under a dataset-specific directory.

## Intermediate matrix schema

The intermediate TSV produced from the GTC step has:

- `ID`
- `CHROM`
- `POS`
- one sample column per sample

Each sample cell contains:

```text
gcScore|BAF|LRR|X|Y|GT
