rule install_toolchain:
    input:
        resources_dir=RESOURCES_DIR
    output:
        touch(INSTALL_DONE)
    threads: INSTALL_THREADS
    log:
        f"{PROJECT_ROOT}/logs/install_toolchain.log"
    message:
        "Installing local toolchain dependencies"
    shell:
        r"""
        mkdir -p {PROJECT_ROOT}/logs {STATE_DIR}
        export JOBS={threads}
        bash workflow/scripts/install_toolchain.sh {PROJECT_ROOT} {input.resources_dir} > {log} 2>&1
        touch {output}
        """


rule prepare_reference_and_data:
    input:
        install_done=INSTALL_DONE,
        resources_dir=RESOURCES_DIR
    output:
        touch(REFDATA_DONE),
        fasta=f"{PROJECT_ROOT}/genome/{GENOME_FASTA}",
        fai=f"{PROJECT_ROOT}/genome/{GENOME_FASTA}.fai"
    log:
        f"{PROJECT_ROOT}/logs/prepare_reference_and_data.log"
    message:
        "Preparing dataset resources and reference genome"
    shell:
        r"""
        mkdir -p {PROJECT_ROOT}/logs {STATE_DIR}
        bash workflow/scripts/refdata_downloader.sh \
            {PROJECT_ROOT} \
            {DATA_DIR} \
            {input.resources_dir} \
            {GENOME_FASTA} \
            {GENOME_URL} > {log} 2>&1
        touch {output[0]}
        """
