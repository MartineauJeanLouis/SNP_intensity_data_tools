# SNP Intensity Data Tools: Reproducible SNP-Array Processing, Quality Control and CNV Analysis

**Author:** Martineau Jean-Louis  
**Workflow engine:** Snakemake  
**Primary CNV caller:** PennCNV  
**Primary data type:** Illumina SNP-array intensity data  
**Platform:** Linux

---
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22920948.svg)](https://doi.org/10.5281/zenodo.22920948)
![GitHub release](https://img.shields.io/github/v/release/MartineauJeanLouis/SNP_intensity_data_tools)
![GitHub license](https://img.shields.io/github/license/MartineauJeanLouis/SNP_intensity_data_tools)
![GitHub stars](https://img.shields.io/github/stars/MartineauJeanLouis/SNP_intensity_data_tools?style=flat)
---

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
> 💼 Need help with SNP-array data? See [Service Packages](#-bioinformatics-services).

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

## Citation

If you use SNP Intensity Data Tools in research, please cite the archived software release associated with the version used for the analysis.

Users should also cite the original publications and software resources underlying the analytical components used in their analysis, particularly PennCNV and Snakemake.

---

## References

1- Jean Louis Martineau. (2019). Python based parallel CNV calling prioritizing mpi4py usage and memory optimization (Version 1.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.3497400

2- Wang K, Li M, Hadley D, Liu R, Glessner J, Grant SFA, Hakonarson H, Bucan M. **PennCNV: an integrated hidden Markov model designed for high-resolution copy number variation detection in whole-genome SNP genotyping data.** *Genome Research*. 2007;17(11):1665–1674. doi:10.1101/gr.6861907.

3- Köster J, Rahmann S. **Snakemake—a scalable bioinformatics workflow engine.** *Bioinformatics*. 2012;28(19):2520–2522. doi:10.1093/bioinformatics/bts480.

4- Genovese G. **gtc2vcf — conversion of Illumina and Affymetrix microarray data using the bcftools plugin framework.**

5- Petr Danecek, James K Bonfield, Jennifer Liddle, John Marshall, Valeriu Ohan, Martin O Martin-Almeda, Andrew Weller, Bhupinder Singh, Shane McCarthy, Richard Durbin, Twelve years of SAMtools and BCFtools, GigaScience, Volume 10, Issue 2, February 2021, giab008, https://doi.org/10.1093/gigascience/giab008

6- Li, H., et al. (2009). The Sequence Alignment/Map format and SAMtools. Bioinformatics, 25(16), 2078–2079.

7- Bonfield JK, Marshall J, Danecek P, Li H, Ohan V, Whitwham A, Keane T, Davies RM, HTSlib: C library for reading/writing high-throughput sequencing data, GigaScience (2021) 10(2) giab007

8- Narasimhan V, Danecek P, Scally A, Xue Y, Tyler-Smith C, and Durbin R, BCFtools/RoH: a hidden Markov model approach for detecting autozygosity from next-generation sequencing data, Bioinformatics (2016) 32(11) 1749-51

9- Danecek P, McCarthy SA, HipSci Consortium, and Durbin R, A Method for Checking Genomic Integrity in Cultured Cell Lines from SNP Genotyping Data, PLoS One (2016) 11(5) e0155014

---
