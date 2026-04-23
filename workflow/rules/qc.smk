rule parse_and_qc:
    input:
        f"{OUTPUT_PATH}/gtc2vcf/{GTC_BATCH}.tsv"
    output:
        probe_qc=f"{PARSED_PATH}/qc/probe_qc.tsv",
        sample_qc=f"{PARSED_PATH}/qc/sample_qc.tsv",
        probe_pfb=f"{PARSED_PATH}/qc/probe_pfb.tsv",
        per_sample_dir=directory(f"{PARSED_PATH}/per_sample"),
        plots=PLOT_TARGETS if PLOT_QC else []
    params:
        outdir=PARSED_PATH,
        gc_threshold=GC_THRESHOLD,
        dtype=DTYPE,
        workers=WORKERS,
        force_cpu="--force-cpu" if FORCE_CPU else "",
        plot_qc="yes" if PLOT_QC else "no"
    log:
        f"{PROJECT_ROOT}/logs/parse_and_qc.log"
    message:
        "Parsing matrix and generating QC outputs"
    shell:
        r"""
        mkdir -p {PROJECT_ROOT}/logs
        python3 workflow/scripts/parse_and_qc_hybrid.py \
            -i {input} \
            -o {params.outdir} \
            --gc-threshold {params.gc_threshold} \
            --dtype {params.dtype} \
            --workers {params.workers} \
            --plot-qc {params.plot_qc} \
            {params.force_cpu} > {log} 2>&1
        """
