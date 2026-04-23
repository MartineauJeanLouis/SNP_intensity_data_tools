#!/usr/bin/env python3

import argparse
import os
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def find_sample_columns(df):
    sample_prefix = None
    for col in df.columns:
        if col.endswith(".Log R Ratio"):
            sample_prefix = col[: -len(".Log R Ratio")]
            break
    if sample_prefix is None:
        raise ValueError("Could not infer sample prefix from per-sample TSV.")
    return sample_prefix, f"{sample_prefix}.Log R Ratio", f"{sample_prefix}.B Allele Freq"


def sanitize(text):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(text))


def main():
    parser = argparse.ArgumentParser(description="Plot top CNVs by confidence")
    parser.add_argument("--top-cnv", required=True, help="Input top CNVs TSV")
    parser.add_argument("--per-sample-dir", required=True, help="Directory with per-sample TSV files")
    parser.add_argument("--output-dir", required=True, help="Output plot directory")
    parser.add_argument("--done-file", required=True, help="Sentinel file")
    parser.add_argument("--width", type=float, default=12.0)
    parser.add_argument("--height", type=float, default=7.0)
    parser.add_argument("--pad-probes", type=int, default=300, help="Number of probes upstream/downstream to include")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    top_df = pd.read_csv(args.top_cnv, sep="\t")
    generated = 0

    for _, row in top_df.iterrows():
        sample = row["sample"]
        chrom = str(row["chr"])
        start = int(row["start"])
        end = int(row["end"])
        rank = int(row["rank"])
        conf = row["confidence"]
        state = row.get("state", "")

        sample_file = os.path.join(args.per_sample_dir, f"{sample}.tsv")
        if not os.path.isfile(sample_file):
            continue

        df = pd.read_csv(sample_file, sep="\t")
        sample_prefix, lrr_col, baf_col = find_sample_columns(df)

        required = ["Chr", "Position", lrr_col, baf_col]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns in {sample_file}: {missing}")

        # Keep only the chromosome of interest
        chrom_df = df[df["Chr"].astype(str) == chrom].copy()

        chrom_df["Position"] = pd.to_numeric(chrom_df["Position"], errors="coerce")
        chrom_df[lrr_col] = pd.to_numeric(chrom_df[lrr_col], errors="coerce")
        chrom_df[baf_col] = pd.to_numeric(chrom_df[baf_col], errors="coerce")

        chrom_df = chrom_df.dropna(subset=["Position"]).copy()
        chrom_df = chrom_df.sort_values("Position").reset_index(drop=True)

        # Identify CNV probes
        cnv_mask = (chrom_df["Position"] >= start) & (chrom_df["Position"] <= end)
        cnv_idx = np.where(cnv_mask)[0]

        if len(cnv_idx) == 0:
            continue

        # Extend plotting window by a fixed number of probes
        pad = args.pad_probes
        plot_start_idx = max(0, cnv_idx[0] - pad)
        plot_end_idx = min(len(chrom_df) - 1, cnv_idx[-1] + pad)

        region = chrom_df.iloc[plot_start_idx:plot_end_idx + 1].copy()
        sub = chrom_df.loc[cnv_mask].copy()

        fig, axes = plt.subplots(2, 1, figsize=(args.width, args.height), sharex=True)

        # -------------------------
        # LRR plot
        # -------------------------
        # Background region
        axes[0].scatter(region["Position"], region[lrr_col], s=10, alpha=0.35)

        # CNV probes highlighted
        axes[0].scatter(sub["Position"], sub[lrr_col], s=14, color="red", alpha=0.9)

        # CNV line from start to end
        #axes[0].plot(sub["Position"], sub[lrr_col], linewidth=1.5, color="red")

        # Reference / boundaries
        axes[0].axhline(0, linestyle="--", linewidth=1)
        axes[0].axvline(start, linestyle="--", color="black", linewidth=1)
        axes[0].axvline(end, linestyle="--", color="black", linewidth=1)

        axes[0].set_ylabel("Log R Ratio")
        axes[0].set_title(
            f"Rank {rank} | {sample} | {chrom}:{start}-{end} | state={state} | conf={conf}"
        )

        # -------------------------
        # BAF plot
        # -------------------------
        # Background region
        axes[1].scatter(region["Position"], region[baf_col], s=10, alpha=0.35)

        # CNV probes highlighted
        axes[1].scatter(sub["Position"], sub[baf_col], s=14, color="red", alpha=0.9)

        # Reference / boundaries
        axes[1].axhline(0.5, linestyle="--", color="black", linewidth=1)
        axes[1].axvline(start, linestyle="--", color="black", linewidth=1)
        axes[1].axvline(end, linestyle="--", color="black", linewidth=1)

        axes[1].set_xlabel("Genomic position")
        axes[1].set_ylabel("B Allele Frequency")

        plt.tight_layout()

        out_name = f"rank{rank}_{sanitize(sample)}_{sanitize(chrom)}_{start}_{end}.png"
        out_path = os.path.join(args.output_dir, out_name)
        plt.savefig(out_path, dpi=200)
        plt.close(fig)

        generated += 1

    with open(args.done_file, "w", encoding="utf-8") as fh:
        fh.write(f"generated_plots\t{generated}\n")


if __name__ == "__main__":
    main()
