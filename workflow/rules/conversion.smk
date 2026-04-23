rule idat_to_gtc:
    input:
        install_done=INSTALL_DONE,
        refdata_done=REFDATA_DONE
    output:
        gtc_list=f"{OUTPUT_PATH}/gtc.list.txt",
        gtc_dir=directory(f"{OUTPUT_PATH}/gtc_data")
    threads: IDAT_TO_GTC_THREADS
    log:
        f"{PROJECT_ROOT}/logs/idat_to_gtc.log"
    message:
        "Converting IDAT files to GTC"
    shell:
        r"""
        mkdir -p {PROJECT_ROOT}/logs
        export THREADS={threads}
        export BATCH_SIZE={config[runtime][batch_size]}
        bash workflow/scripts/idat_to_gtc.sh {PROJECT_ROOT} {DATA_DIR} > {log} 2>&1
        """


rule gtc_to_tsv:
    input:
        install_done=INSTALL_DONE,
        refdata_done=REFDATA_DONE,
        gtc_list=f"{OUTPUT_PATH}/gtc.list.txt",
        gtc_dir=f"{OUTPUT_PATH}/gtc_data",
        fasta=f"{PROJECT_ROOT}/genome/{GENOME_FASTA}",
        fai=f"{PROJECT_ROOT}/genome/{GENOME_FASTA}.fai"
    output:
        f"{OUTPUT_PATH}/gtc2vcf/{GTC_BATCH}.tsv"
    log:
        f"{PROJECT_ROOT}/logs/gtc_to_tsv.log"
    message:
        "Generating intensity/genotype TSV from GTC files"
    shell:
        r"""
        mkdir -p {PROJECT_ROOT}/logs
        bash workflow/scripts/gtc_to_tsv.sh {PROJECT_ROOT} {DATA_DIR} {GTC_BATCH} {GENOME_FASTA} > {log} 2>&1
        """
