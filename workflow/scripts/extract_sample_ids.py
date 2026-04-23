#!/usr/bin/env python3

import argparse

def main():
    parser = argparse.ArgumentParser(description="Extract sample IDs from wide matrix header.")
    parser.add_argument("--input", required=True, help="Input GTC-derived TSV")
    parser.add_argument("--output", required=True, help="Output samples.txt")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as fh:
        header = fh.readline().rstrip("\n").split("\t")

    if len(header) < 4:
        raise ValueError("Expected at least 4 columns: ID, CHROM, POS, and one sample column.")

    sample_ids = header[3:]

    with open(args.output, "w", encoding="utf-8") as out:
        for sample in sample_ids:
            sample = sample.strip()
            if sample:
                out.write(sample + "\n")

if __name__ == "__main__":
    main()