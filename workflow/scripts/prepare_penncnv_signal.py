#!/usr/bin/env python3

import argparse
import pandas as pd

def infer_sample_prefix(columns):
    for col in columns:
        if col.endswith(".Log R Ratio"):
            return col[: -len(".Log R Ratio")]
    return None

def main():
    parser = argparse.ArgumentParser(description="Prepare PennCNV signal file from per-sample TSV")
    parser.add_argument("--input", required=True, help="Input per-sample TSV")
    parser.add_argument("--output", required=True, help="Output PennCNV signal TSV")
    args = parser.parse_args()

    df = pd.read_csv(args.input, sep="\t")
    sample_prefix = infer_sample_prefix(df.columns)

    if sample_prefix is None:
        raise ValueError("Could not infer sample prefix from per-sample TSV columns.")

    baf_col = f"{sample_prefix}.B Allele Freq"
    lrr_col = f"{sample_prefix}.Log R Ratio"

    required = ["Name", "Chr", "Position", baf_col, lrr_col]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in per-sample TSV: {missing}")

    out = pd.DataFrame({
        "Name": df["Name"],
        "Chr": df["Chr"],
        "Position": df["Position"],
        "B Allele Freq": pd.to_numeric(df[baf_col], errors="coerce"),
        "Log R Ratio": pd.to_numeric(df[lrr_col], errors="coerce"),
    })

    out.to_csv(args.output, sep="\t", index=False)

if __name__ == "__main__":
    main()