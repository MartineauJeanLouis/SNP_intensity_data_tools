#!/usr/bin/env python3

import argparse
import os
import re
from pathlib import Path
import pandas as pd

REGION_RE = re.compile(r'^(chr[\w]+):(\d+)-(\d+)')
KEYVAL_RE = re.compile(r'(\w+)=([^\s]+)')

def parse_rawcnv_line(line, sample):
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    region_match = REGION_RE.match(line)
    if not region_match:
        return None

    chrom, start, end = region_match.groups()
    kv = dict(KEYVAL_RE.findall(line))

    numsnp = kv.get("numsnp", kv.get("nsnp", ""))
    length = kv.get("length", "")
    conf = kv.get("conf", kv.get("confidence", ""))
    state = kv.get("state", kv.get("cn", kv.get("CN", "")))

    try:
        conf_val = float(conf)
    except Exception:
        conf_val = float("nan")

    return {
        "sample": sample,
        "chr": chrom,
        "start": int(start),
        "end": int(end),
        "numsnp": numsnp,
        "length": length,
        "state": state,
        "confidence": conf_val,
        "raw_line": line,
    }

def main():
    parser = argparse.ArgumentParser(description="Summarize PennCNV rawcnv files")
    parser.add_argument("--inputs", nargs="+", required=True, help="Input rawcnv files")
    parser.add_argument("--all-output", required=True, help="Output all_cnvs.tsv")
    parser.add_argument("--top-output", required=True, help="Output topN CNVs TSV")
    parser.add_argument("--top-n", type=int, default=5, help="Top N CNVs by confidence")
    args = parser.parse_args()

    rows = []

    for filepath in args.inputs:
        sample = Path(filepath).name
        sample = re.sub(r"^autosome_", "", sample)
        sample = re.sub(r"\.rawcnv$", "", sample)

        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                row = parse_rawcnv_line(line, sample)
                if row is not None:
                    rows.append(row)

    df = pd.DataFrame(rows)

    if df.empty:
        df = pd.DataFrame(columns=[
            "sample", "chr", "start", "end", "numsnp",
            "length", "state", "confidence", "raw_line"
        ])
        top_df = df.copy()
    else:
        df = df.sort_values(["confidence", "sample"], ascending=[False, True], na_position="last")
        top_df = df.head(args.top_n).copy()
        top_df.insert(0, "rank", range(1, len(top_df) + 1))

    os.makedirs(os.path.dirname(args.all_output), exist_ok=True)
    os.makedirs(os.path.dirname(args.top_output), exist_ok=True)

    df.to_csv(args.all_output, sep="\t", index=False)
    top_df.to_csv(args.top_output, sep="\t", index=False)

if __name__ == "__main__":
    main()