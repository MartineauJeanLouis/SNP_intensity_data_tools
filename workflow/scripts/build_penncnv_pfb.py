#!/usr/bin/env python3

import argparse
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description="Build PennCNV PFB file from probe_pfb.tsv")
    parser.add_argument("--input", required=True, help="Input probe_pfb.tsv")
    parser.add_argument("--output", required=True, help="Output prob.pfb")
    args = parser.parse_args()

    df = pd.read_csv(args.input, sep="\t")

    required = ["Name", "Chr", "Position", "PFB"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in probe_pfb.tsv: {missing}")

    out = df[["Name", "Chr", "Position", "PFB"]].copy()
    out = out.rename(columns={"Name": "SNP"})
    
    # Remove leading 'chr' prefix for PennCNV compatibility
    out["Chr"] = out["Chr"].astype(str).str.replace(r"^chr", "", regex=True)

    out.to_csv(args.output, sep="\t", index=False)

if __name__ == "__main__":
    main()
