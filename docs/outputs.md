```markdown
# Outputs

## Main output directories

### `results/<project>/output/gtc_data/`
Generated `.gtc` files.

### `results/<project>/output/gtc.list.txt`
List of `.gtc` files used downstream.

### `results/<project>/output/gtc2vcf/<batch>.tsv`
Intermediate wide matrix.

### `results/<project>/output/Final_output/qc/probe_qc.tsv`
Probe-level QC table containing:
- Name
- Chr
- Position
- n_samples_pass
- n_samples_total
- probe_call_rate

### `results/<project>/output/Final_output/qc/sample_qc.tsv`
Sample-level QC table containing:
- Sample
- n_probes_pass
- n_probes_total
- sample_genotyping_success_rate

### `results/<project>/output/Final_output/qc/probe_pfb.tsv`
Probe-level PFB table containing:
- Name
- Chr
- Position
- n_samples_with_valid_gt
- B_observed
- total_expected
- PFB

### `results/<project>/output/Final_output/per_sample/`
One TSV per sample with standardized columns:
- Name
- Chr
- Position
- `<sample>.gcScore`
- `<sample>.B Allele Freq`
- `<sample>.Log R Ratio`
- `<sample>.X`
- `<sample>.Y`
- `<sample>.GT`

### `results/<project>/output/Final_output/qc/plots/`
Optional PNG plots:
- sample genotyping success rate
- probe call rate
- probe PFB
- histograms
- density plots
