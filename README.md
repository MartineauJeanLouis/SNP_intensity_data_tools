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

## 🧬 Bioinformatics Services

Beyond this open-source workflow, I provide professional bioinformatics services to help you move from raw data to actionable results — efficiently, reproducibly, and at scale.

### What I can help you with

**🔹 SNP-array data processing & QC**
- End-to-end handling of Illumina IDAT data
- Genotype calling, intensity extraction (BAF, LRR), and QC reporting
- Probe- and sample-level quality assessment
- PFB estimation and dataset validation

**🔹 Custom pipeline development**
- Adapt this workflow to your specific dataset, platform, or study design
- Extend to additional analyses (e.g., CNV, population structure, ML pipelines)
- Integration with existing lab or institutional workflows

**🔹 High-performance & scalable execution**
- Deployment on HPC clusters or cloud platforms
- Parallelization and performance optimization (CPU/GPU)
- Handling large cohorts and high-throughput studies

**🔹 Data interpretation & downstream analysis**
- QC interpretation and troubleshooting
- Identification of problematic samples or probes
- Guidance on best practices for downstream analyses

**🔹 Reproducibility & infrastructure**
- Fully reproducible pipeline setups (Snakemake, environments, containers)
- Version-controlled workflows for publications or regulatory contexts
- Assistance preparing pipelines for sharing or long-term maintenance

---

### Why work with me

- ✔️ End-to-end expertise: from raw IDAT files to analysis-ready outputs  
- ✔️ Reproducible workflows built with Snakemake best practices  
- ✔️ Experience handling real-world, messy datasets  
- ✔️ Focus on performance, scalability, and clarity of results  
- ✔️ Flexible collaboration (one-time projects or ongoing support)

---

## 💼 Service Packages

To make collaboration simple and transparent, I offer structured service packages:

### 🟢 Quick QC & Data Health Check
Fast assessment of SNP-array data quality, including QC metrics, plots, and a short summary report.

### 🟡 Standard SNP-Array Processing
End-to-end processing from IDAT files to clean, analysis-ready outputs with QC interpretation.

### 🔴 Advanced Analysis & Custom Pipeline
Custom workflows, non-standard datasets, performance optimization, and extended analysis.

### 🔵 Deployment & Reproducibility Setup
Full setup of the pipeline on HPC or cloud infrastructure, with reproducible environments.

### 🧠 Consultation & Interpretation
Dedicated session to review results and guide next analytical steps.

📩 Contact me with a short description of your project for a tailored recommendation.

### 💰 Pricing

Projects are typically scoped based on dataset size, complexity, and level of customization.

Typical ranges:

- Small datasets / standard runs: **$300 – $1,000 CAD**
- Custom analysis projects: **$1,000 – $5,000 CAD**
- Large-scale or advanced projects: **$5,000+ CAD**

Hourly consulting is also available.

Please reach out with a brief description of your project for a tailored estimate.

### 📩 Get in touch

If you’re working with SNP-array data and need support — whether technical, analytical, or infrastructural — feel free to reach out.

**Contact:** martineau.jeanlouis.bioinfo2017@gmail.com

You can also open an issue to start a discussion about your needs.