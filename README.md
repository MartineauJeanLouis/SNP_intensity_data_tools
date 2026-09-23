# SNP_intensity_data_tools

A reproducible Snakemake workflow for processing Illumina SNP-array IDAT data, performing genotype calling, extracting intensity-derived features, and generating probe- and sample-level quality-control outputs with optional GPU acceleration.

## Overview

This workflow currently supports a pipeline that:

1. installs local toolchain dependencies (`htslib`, `bcftools`, `samtools`, `gtc2vcf` plugin sources, IAAP CLI)
2. prepares reference and dataset resources
3. converts IDAT files to GTC using IAAP
4. converts GTC-derived data into a tabular matrix using `bcftools +gtc2vcf`
5. parses the matrix into:
   - per-sample feature files
   - probe QC table
   - sample QC table
   - probe PFB table
   - optional QC plots

## Current implementation scope

The current workflow is configured for an Illumina OmniExpress array setup and a GEO-based data acquisition path centered on `GSE262754`. The repository structure is designed so those values can be changed through configuration.

## Repository structure

```text
config/                User-editable configuration
docs/                  Project documentation
resources/             Optional user-provided assets and cached resources
results/               Workflow outputs
tests/                 Minimal test scaffolding
workflow/              Snakemake workflow, rules, scripts, and environments
```

> 💼 Need help running or adapting this pipeline? see [Bioinformatics Services](#-bioinformatics-services).
> 💼 Need help with SNP-array data? See [Service Packages](#-service-packages).

## 📚 Documentation

For a detailed description of the pipeline architecture, SNP-array
processing, quality control, CNV analysis, results, and future development,
see the **[SNP Intensity Data Tools Wiki](../../wiki)**.


## 🧬 Bioinformatics Services

Beyond this open-source workflow, I provide professional bioinformatics services to help you move from raw data to actionable results — efficiently, reproducibly, and at scale.

### 📩 Get in touch

If you’re working with SNP-array data and need support — whether technical, analytical, or infrastructural — feel free to reach out.

**Contact:** martineau.jeanlouis.bioinfo2017@gmail.com

You can also open an issue to start a discussion about your needs.