#!/usr/bin/env python3

import os
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    cp = None
    GPU_AVAILABLE = False


FIELDS = ["gcScore", "B Allele Freq", "Log R Ratio", "X", "Y", "GT"]
GC_INDEX = 0
GT_INDEX = 5

GT_MAP = {
    "0/0": "AA",
    "0/1": "AB",
    "1/1": "BB"
}

GT_B_COUNT = {
    "AA": 0,
    "AB": 1,
    "BB": 2
}


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Hybrid CPU/GPU parser for genotype matrix. "
            "CPU handles parsing and writing; GPU handles matrix-wide QC."
        )
    )
    parser.add_argument("-i", "--input", required=True, help="Input matrix file")
    parser.add_argument("-o", "--output-dir", required=True, help="Output directory")
    parser.add_argument("--sep", default="\t", help=r"Input delimiter (default: tab)")
    parser.add_argument("--gc-threshold", type=float, required=True, help="gcScore threshold")
    parser.add_argument("--dtype", default="float32", choices=["float32", "float64"])
    parser.add_argument("--workers", type=int, default=4, help="CPU workers for per-sample writing")
    parser.add_argument(
        "--force-cpu",
        action="store_true",
        help="Disable GPU even if CuPy is installed"
    )
    parser.add_argument(
        "--plot-qc",
        choices=["yes", "no"],
        default="no",
        help="Whether to generate QC plots (default: no)"
    )
    return parser.parse_args()


def ensure_dirs(base_dir: str):
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(os.path.join(base_dir, "qc"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "per_sample"), exist_ok=True)


def validate_required_columns(df: pd.DataFrame):
    required = ["CHROM", "POS"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required common columns: {missing}")


def get_common_columns(df: pd.DataFrame, probe_col: str) -> pd.DataFrame:
    """
    Return standardized common columns:
    Name, Chr, Position
    """
    return pd.DataFrame({
        "Name": df[probe_col].astype(str),
        "Chr": df["CHROM"].astype(str),
        "Position": df["POS"].astype(str),
    })


def split_sample_column(series: pd.Series, sample_name: str) -> pd.DataFrame:
    split_df = series.fillna("").astype(str).str.split("|", expand=True)

    if split_df.shape[1] != len(FIELDS):
        bad_rows = series[
            series.fillna("").astype(str).str.count(r"\|") != (len(FIELDS) - 1)
        ]
        raise ValueError(
            f"Sample '{sample_name}' has malformed entries.\n"
            f"Expected {len(FIELDS)} pipe-separated fields.\n"
            f"Examples:\n{bad_rows.head()}"
        )

    return split_df


def parse_sample_column(series: pd.Series, sample_name: str, dtype: str) -> pd.DataFrame:
    split_df = split_sample_column(series, sample_name)

    out = pd.DataFrame()

    numeric_fields = ["gcScore", "B Allele Freq", "Log R Ratio", "X", "Y"]
    for i, field in enumerate(numeric_fields):
        col_name = f"{sample_name}.{field}"
        out[col_name] = pd.to_numeric(split_df.iloc[:, i], errors="coerce").astype(dtype)

    gt_raw = split_df.iloc[:, GT_INDEX].astype(str).str.strip()
    gt_encoded = gt_raw.map(GT_MAP)

    gt_encoded = gt_encoded.fillna(
        gt_raw.where(gt_raw.isin(["AA", "AB", "BB"]), np.nan)
    )
    out[f"{sample_name}.GT"] = gt_encoded

    return out


def extract_gcscore_vector(series: pd.Series, sample_name: str, dtype: str) -> np.ndarray:
    split_df = split_sample_column(series, sample_name)
    gc = pd.to_numeric(split_df.iloc[:, GC_INDEX], errors="coerce").astype(dtype).to_numpy()
    return gc


def extract_gt_bcount_vector(series: pd.Series, sample_name: str) -> np.ndarray:
    """
    Return vector with:
      AA -> 0
      AB -> 1
      BB -> 2
    invalid/missing -> -1
    """
    split_df = split_sample_column(series, sample_name)
    gt_raw = split_df.iloc[:, GT_INDEX].astype(str).str.strip()

    gt_encoded = gt_raw.map(GT_MAP)
    gt_encoded = gt_encoded.fillna(gt_raw.where(gt_raw.isin(["AA", "AB", "BB"]), np.nan))

    bcount = gt_encoded.map(GT_B_COUNT).fillna(-1).astype(np.int8).to_numpy()
    return bcount


def build_gcscore_matrix(df: pd.DataFrame, sample_columns, dtype: str) -> np.ndarray:
    gc_vectors = []
    for sample in sample_columns:
        gc_vectors.append(extract_gcscore_vector(df[sample], sample, dtype))
    return np.column_stack(gc_vectors)


def build_gt_bcount_matrix(df: pd.DataFrame, sample_columns) -> np.ndarray:
    gt_vectors = []
    for sample in sample_columns:
        gt_vectors.append(extract_gt_bcount_vector(df[sample], sample))
    return np.column_stack(gt_vectors)


def compute_qc_gpu(probe_ids, sample_names, gc_matrix: np.ndarray, gc_threshold: float):
    g_gc = cp.asarray(gc_matrix)
    pass_mask = g_gc >= gc_threshold

    n_probes, n_samples = pass_mask.shape

    probe_pass = cp.sum(pass_mask, axis=1)
    sample_pass = cp.sum(pass_mask, axis=0)

    probe_call_rate = probe_pass / n_samples
    sample_success_rate = sample_pass / n_probes

    probe_qc_df = pd.DataFrame({
        "Name": probe_ids,
        "n_samples_pass": cp.asnumpy(probe_pass),
        "n_samples_total": n_samples,
        "probe_call_rate": cp.asnumpy(probe_call_rate)
    })

    sample_qc_df = pd.DataFrame({
        "Sample": sample_names,
        "n_probes_pass": cp.asnumpy(sample_pass),
        "n_probes_total": n_probes,
        "sample_genotyping_success_rate": cp.asnumpy(sample_success_rate)
    })

    return probe_qc_df, sample_qc_df


def compute_qc_cpu(probe_ids, sample_names, gc_matrix: np.ndarray, gc_threshold: float):
    pass_mask = gc_matrix >= gc_threshold

    n_probes, n_samples = pass_mask.shape

    probe_pass = pass_mask.sum(axis=1)
    sample_pass = pass_mask.sum(axis=0)

    probe_call_rate = probe_pass / n_samples
    sample_success_rate = sample_pass / n_probes

    probe_qc_df = pd.DataFrame({
        "Name": probe_ids,
        "n_samples_pass": probe_pass,
        "n_samples_total": n_samples,
        "probe_call_rate": probe_call_rate
    })

    sample_qc_df = pd.DataFrame({
        "Sample": sample_names,
        "n_probes_pass": sample_pass,
        "n_probes_total": n_probes,
        "sample_genotyping_success_rate": sample_success_rate
    })

    return probe_qc_df, sample_qc_df


def compute_pfb_gpu(probe_ids, gt_bcount_matrix: np.ndarray):
    """
    PFB per probe:
      sum(B counts across valid samples) / (2 * number of valid samples)

    valid sample = GT in {AA, AB, BB}
    invalid/missing encoded as -1

    If no valid genotypes exist for a probe, set PFB to 0.0 so the
    downstream file never contains a blank value.
    """
    g_gt = cp.asarray(gt_bcount_matrix)

    valid_mask = g_gt >= 0
    valid_sample_count = cp.sum(valid_mask, axis=1)

    b_sum = cp.sum(cp.where(valid_mask, g_gt, 0), axis=1)
    denom = 2 * valid_sample_count

    pfb = cp.where(denom > 0, b_sum / denom, 0.0)

    probe_pfb_df = pd.DataFrame({
        "Name": probe_ids,
        "n_samples_with_valid_gt": cp.asnumpy(valid_sample_count),
        "B_observed": cp.asnumpy(b_sum),
        "total_expected": cp.asnumpy(denom),
        "PFB": cp.asnumpy(pfb)
    })

    return probe_pfb_df


def compute_pfb_cpu(probe_ids, gt_bcount_matrix: np.ndarray):
    valid_mask = gt_bcount_matrix >= 0
    valid_sample_count = valid_mask.sum(axis=1)

    b_sum = np.where(valid_mask, gt_bcount_matrix, 0).sum(axis=1)
    denom = 2 * valid_sample_count

    pfb = np.divide(
        b_sum,
        denom,
        out=np.zeros_like(b_sum, dtype=np.float64),
        where=denom > 0
    )

    probe_pfb_df = pd.DataFrame({
        "Name": probe_ids,
        "n_samples_with_valid_gt": valid_sample_count,
        "B_observed": b_sum,
        "total_expected": denom,
        "PFB": pfb
    })

    return probe_pfb_df


def write_qc_files(output_dir: str, probe_qc_df: pd.DataFrame, sample_qc_df: pd.DataFrame, probe_pfb_df: pd.DataFrame):
    probe_qc_file = os.path.join(output_dir, "qc", "probe_qc.tsv")
    sample_qc_file = os.path.join(output_dir, "qc", "sample_qc.tsv")
    probe_pfb_file = os.path.join(output_dir, "qc", "probe_pfb.tsv")

    probe_qc_df.to_csv(probe_qc_file, sep="\t", index=False)
    sample_qc_df.to_csv(sample_qc_file, sep="\t", index=False)

    probe_pfb_df = probe_pfb_df.copy()
    probe_pfb_df["PFB"] = pd.to_numeric(probe_pfb_df["PFB"], errors="coerce").fillna(0.0)
    probe_pfb_df.to_csv(probe_pfb_file, sep="\t", index=False)

    return probe_qc_file, sample_qc_file, probe_pfb_file

def plot_qc_data(output_dir: str, sample_qc_df: pd.DataFrame, probe_qc_df: pd.DataFrame, probe_pfb_df: pd.DataFrame):
    plots_dir = os.path.join(output_dir, "qc", "plots")
    os.makedirs(plots_dir, exist_ok=True)

    def clean_numeric(series):
        y = pd.to_numeric(series, errors="coerce").to_numpy()
        y = y[~np.isnan(y)]
        return y

    def smooth_density_from_hist(values, bins=100, window=7):
        hist, edges = np.histogram(values, bins=bins, density=True)
        centers = (edges[:-1] + edges[1:]) / 2

        if window < 3:
            return centers, hist

        kernel = np.ones(window, dtype=float) / window
        smooth = np.convolve(hist, kernel, mode="same")
        return centers, smooth

    # -------- Sample genotyping success rate (sorted scatter) --------
    sample_plot = os.path.join(plots_dir, "sample_genotyping_success_rate.png")
    plt.figure(figsize=(10, 5))

    y = clean_numeric(sample_qc_df["sample_genotyping_success_rate"])
    y = np.sort(y)
    x = np.arange(len(y))

    plt.scatter(x, y, s=12, alpha=0.7)
    plt.xlabel("Sorted sample index")
    plt.ylabel("Genotyping success rate")
    plt.title("Sample genotyping success rate (sorted)")
    plt.tight_layout()
    plt.savefig(sample_plot, dpi=200)
    plt.close()

    # -------- Probe call rate (sorted scatter) --------
    probe_call_plot = os.path.join(plots_dir, "probe_call_rate.png")
    plt.figure(figsize=(10, 5))

    y = clean_numeric(probe_qc_df["probe_call_rate"])
    y = np.sort(y)
    x = np.arange(len(y))

    plt.scatter(x, y, s=4, alpha=0.5)
    plt.xlabel("Sorted probe index")
    plt.ylabel("Probe call rate")
    plt.title("Probe call rate (sorted)")
    plt.tight_layout()
    plt.savefig(probe_call_plot, dpi=200)
    plt.close()

    # -------- Probe PFB (sorted scatter) --------
    probe_pfb_plot = os.path.join(plots_dir, "probe_pfb.png")
    plt.figure(figsize=(10, 5))

    y = clean_numeric(probe_pfb_df["PFB"])
    y = np.sort(y)
    x = np.arange(len(y))

    plt.scatter(x, y, s=4, alpha=0.5)
    plt.xlabel("Sorted probe index")
    plt.ylabel("Probe PFB")
    plt.title("Probe PFB (sorted)")
    plt.tight_layout()
    plt.savefig(probe_pfb_plot, dpi=200)
    plt.close()

    # -------- Probe call rate histogram --------
    probe_call_hist = os.path.join(plots_dir, "probe_call_rate_histogram.png")
    plt.figure(figsize=(10, 5))

    y = clean_numeric(probe_qc_df["probe_call_rate"])
    plt.hist(y, bins=100, density=False)
    plt.xlabel("Probe call rate")
    plt.ylabel("Count")
    plt.title("Histogram of probe call rate")
    plt.tight_layout()
    plt.savefig(probe_call_hist, dpi=200)
    plt.close()

    # -------- Probe call rate density --------
    probe_call_density = os.path.join(plots_dir, "probe_call_rate_density.png")
    plt.figure(figsize=(10, 5))

    y = clean_numeric(probe_qc_df["probe_call_rate"])
    centers, density = smooth_density_from_hist(y, bins=100, window=7)
    plt.plot(centers, density, linewidth=1.5)
    plt.xlabel("Probe call rate")
    plt.ylabel("Density")
    plt.title("Density plot of probe call rate")
    plt.tight_layout()
    plt.savefig(probe_call_density, dpi=200)
    plt.close()

    # -------- Probe PFB histogram --------
    probe_pfb_hist = os.path.join(plots_dir, "probe_pfb_histogram.png")
    plt.figure(figsize=(10, 5))

    y = clean_numeric(probe_pfb_df["PFB"])
    plt.hist(y, bins=100, density=False)
    plt.xlabel("Probe PFB")
    plt.ylabel("Count")
    plt.title("Histogram of probe PFB")
    plt.tight_layout()
    plt.savefig(probe_pfb_hist, dpi=200)
    plt.close()

    # -------- Probe PFB density --------
    probe_pfb_density = os.path.join(plots_dir, "probe_pfb_density.png")
    plt.figure(figsize=(10, 5))

    y = clean_numeric(probe_pfb_df["PFB"])
    centers, density = smooth_density_from_hist(y, bins=100, window=7)
    plt.plot(centers, density, linewidth=1.5)
    plt.xlabel("Probe PFB")
    plt.ylabel("Density")
    plt.title("Density plot of probe PFB")
    plt.tight_layout()
    plt.savefig(probe_pfb_density, dpi=200)
    plt.close()

    return (
        sample_plot,
        probe_call_plot,
        probe_pfb_plot,
        probe_call_hist,
        probe_call_density,
        probe_pfb_hist,
        probe_pfb_density,
    )

def write_one_sample(
    sample_name: str,
    sample_series: pd.Series,
    common_cols: pd.DataFrame,
    out_dir: str,
    dtype: str
):
    parsed = parse_sample_column(sample_series, sample_name, dtype).reset_index(drop=True)
    out_df = pd.concat([common_cols.reset_index(drop=True), parsed], axis=1)
    out_path = os.path.join(out_dir, f"{sample_name}.tsv")
    out_df.to_csv(out_path, sep="\t", index=False)
    return out_path


def main():
    args = parse_args()
    ensure_dirs(args.output_dir)

    print("Reading input...")
    df = pd.read_csv(args.input, sep=args.sep, dtype=str)

    if df.shape[1] < 4:
        raise ValueError("Input must contain at least probe ID, CHROM, POS, and one sample column.")

    validate_required_columns(df)

    probe_col = df.columns[0]
    reserved_cols = {probe_col, "CHROM", "POS"}
    sample_columns = [c for c in df.columns if c not in reserved_cols]

    if not sample_columns:
        raise ValueError("No sample columns found after excluding probe ID, CHROM, and POS.")

    common_cols = get_common_columns(df, probe_col)
    probe_ids = common_cols["Name"].to_numpy()

    print("Building gcScore matrix on CPU...")
    gc_matrix = build_gcscore_matrix(df, sample_columns, args.dtype)

    print("Building GT B-count matrix on CPU...")
    gt_bcount_matrix = build_gt_bcount_matrix(df, sample_columns)

    use_gpu = GPU_AVAILABLE and not args.force_cpu

    if use_gpu:
        print("Computing QC on GPU...")
        probe_qc_df, sample_qc_df = compute_qc_gpu(
            probe_ids=probe_ids,
            sample_names=sample_columns,
            gc_matrix=gc_matrix,
            gc_threshold=args.gc_threshold
        )
        print("Computing PFB on GPU...")
        probe_pfb_df = compute_pfb_gpu(
            probe_ids=probe_ids,
            gt_bcount_matrix=gt_bcount_matrix
        )
    else:
        print("Computing QC on CPU...")
        probe_qc_df, sample_qc_df = compute_qc_cpu(
            probe_ids=probe_ids,
            sample_names=sample_columns,
            gc_matrix=gc_matrix,
            gc_threshold=args.gc_threshold
        )
        print("Computing PFB on CPU...")
        probe_pfb_df = compute_pfb_cpu(
            probe_ids=probe_ids,
            gt_bcount_matrix=gt_bcount_matrix
        )

    # Add Chr and Position to probe-level outputs
    probe_meta = common_cols[["Name", "Chr", "Position"]]
    probe_qc_df = probe_meta.merge(probe_qc_df, on="Name", how="left")
    probe_pfb_df = probe_meta.merge(probe_pfb_df, on="Name", how="left")

    probe_qc_file, sample_qc_file, probe_pfb_file = write_qc_files(
        args.output_dir,
        probe_qc_df,
        sample_qc_df,
        probe_pfb_df
    )
    print(f"Wrote: {probe_qc_file}")
    print(f"Wrote: {sample_qc_file}")
    print(f"Wrote: {probe_pfb_file}")

    if args.plot_qc == "yes":
        print("Generating QC plots...")
        (
            sample_plot,
            probe_call_plot,
            probe_pfb_plot,
            probe_call_hist,
            probe_call_density,
            probe_pfb_hist,
            probe_pfb_density,
        ) = plot_qc_data(
            args.output_dir,
            sample_qc_df,
            probe_qc_df,
            probe_pfb_df
        )
        print(f"Wrote: {sample_plot}")
        print(f"Wrote: {probe_call_plot}")
        print(f"Wrote: {probe_pfb_plot}")
        print(f"Wrote: {probe_call_hist}")
        print(f"Wrote: {probe_call_density}")
        print(f"Wrote: {probe_pfb_hist}")
        print(f"Wrote: {probe_pfb_density}")

    print("Writing per-sample files on CPU...")
    per_sample_dir = os.path.join(args.output_dir, "per_sample")

    futures = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for sample in sample_columns:
            futures.append(
                ex.submit(
                    write_one_sample,
                    sample,
                    df[sample],
                    common_cols,
                    per_sample_dir,
                    args.dtype
                )
            )

        for fut in as_completed(futures):
            print(f"Wrote: {fut.result()}")

    print("Done.")


if __name__ == "__main__":
    main()
