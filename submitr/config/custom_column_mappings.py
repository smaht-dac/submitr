_CUSTOM_COLUMN_MAPPINGS_EXTERNAL_QUALITY_METRIC = {
    "total_raw_reads_sequenced": {
        "qc_values#0.derived_from": "{name}",
        "qc_values#0.value": "{value}",
        "qc_values#0.key": "Total Raw Reads Sequenced",
        "qc_values#0.tooltip": "# of reads (150bp)"
    },
    "total_raw_bases_sequenced": {
        "qc_values#1.derived_from": "{name}",
        "qc_values#1.value": "{value}",
        "qc_values#1.key": "Total Raw Bases Sequenced",
        "qc_values#1.tooltip": None
    },
    "prefiltering_number_of_consensus_molecules": {
        "qc_values#2.derived_from": "{name}",
        "qc_values#2.value": "{value}",
        "qc_values#2.key": "Pre-filtering # of Consensus Molecules",
        "qc_values#2.tooltip": "Number of DNA molecules identified"
    },
    "prefiltering_genome_coverage": {
        "qc_values#3.derived_from": "{name}",
        "qc_values#3.value": "{value}",
        "qc_values#3.key": "Pre-filtering Genome Coverage",
        "qc_values#3.tooltip": None
    },
    "prefiltering_number_of_reads_per_consensus_molecule": {
        "qc_values#4.derived_from": "{name}",
        "qc_values#4.value": "{value}",
        "qc_values#4.key": "Pre-filtering Number of Reads per Consensus Molecule",
        "qc_values#4.tooltip": None
    },
    "postfiltering_number_of_consensus_molecules": {
        "qc_values#5.derived_from": "{name}",
        "qc_values#5.value": "{value}",
        "qc_values#5.key": "Post-filtering Number of Consensus Molecules",
        "qc_values#5.tooltip": None
    },
    "fraction_prefiltering_molecules_passing_filters": {
        "qc_values#6.derived_from": "{name}",
        "qc_values#6.value": "{value}",
        "qc_values#6.key": "Fraction of Pre-filtering Consensus Molecules that Pass Filters",
        "qc_values#6.tooltip": None
    },
    "number_postfiltering_consensus_base_pairs": {
        "qc_values#7.derived_from": "{name}",
        "qc_values#7.value": "{value}",
        "qc_values#7.key": "Number of Final Post-filtering Consensus Interrogated Base Pairs",
        "qc_values#7.tooltip": "After applying all filters for variant calling, e.e. Mapping quality, Low complexity regions, a4s2 duplex reconstruction criteria, etc."  # noqa
    },
    "somatic_snv_count_by_molecule": {
        "qc_values#8.derived_from": "{name}",
        "qc_values#8.value": "{value}",
        "qc_values#8.key": "Somatic SNV Count by Molecule",
        "qc_values#8.tooltip": None
    },
    "snv_mutation_burden_by_molecule": {
        "qc_values#9.derived_from": "{name}",
        "qc_values#9.value": "{value}",
        "qc_values#9.key": "Somatic SNV Mutation Burden by Molecule",
        "qc_values#9.tooltip": "Detected somatic mutation / final consensus interrogated base pairs"
    }
}

CUSTOM_COLUMN_MAPPINGS = {
    "ExternalQualityMetric": _CUSTOM_COLUMN_MAPPINGS_EXTERNAL_QUALITY_METRIC
}
