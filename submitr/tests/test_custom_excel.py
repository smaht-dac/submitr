import os
from dcicutils.structured_data import StructuredDataSet
from submitr.custom_excel import CustomExcel

TEST_EXCEL_FILE = os.path.join(os.path.dirname(__file__), "data", "test_custom_column_mappings.xlsx")
EXPECTED_RESULT = {
    "ExternalQualityMetric": [
        {
            "submitted_id": "NYU_EXTERNAL-QUALITY-METRIC_COLO829BLT50",
            "submission_centers": "nyu_ttd",
            "category": "HiDEF-seq",
            "qc_values": [
                {
                    "derived_from": "total_raw_reads_sequenced",
                    "value": 11870183,
                    "key": "Total Raw Reads Sequenced",
                    "tooltip": "# of reads (150bp)"
                },
                {
                    "derived_from": "total_raw_bases_sequenced",
                    "value": 44928835584,
                    "key": "Total Raw Bases Sequenced"
                },
                {
                    "derived_from": "prefiltering_number_of_consensus_molecules",
                    "value": 5935091,
                    "key": "Pre-filtering # of Consensus Molecules",
                    "tooltip": "Number of DNA molecules identified"
                },
                {
                    "derived_from": "prefiltering_genome_coverage",
                    "value": 14.98,
                    "key": "Pre-filtering Genome Coverage"
                },
                {
                    "derived_from": "prefiltering_number_of_reads_per_consensus_molecule",
                    "value": 2,
                    "key": "Pre-filtering Number of Reads per Consensus Molecule"
                },
                {
                    "derived_from": "postfiltering_number_of_consensus_molecules",
                    "value": 3108138,
                    "key": "Post-filtering Number of Consensus Molecules"
                },
                {
                    "derived_from": "fraction_prefiltering_molecules_passing_filters",
                    "value": 0.52,
                    "key": "Fraction of Pre-filtering Consensus Molecules that Pass Filters"
                },
                {
                    "derived_from": "number_postfiltering_consensus_base_pairs",
                    "value": 2957487201,
                    "key": "Number of Final Post-filtering Consensus Interrogated Base Pairs",
                    "tooltip": "After applying all filters for variant calling, e.e. Mapping quality, Low complexity regions, a4s2 duplex reconstruction criteria, etc."  # noqa
                },
                {
                    "derived_from": "somatic_snv_count_by_molecule",
                    "value": 1034,
                    "key": "Somatic SNV Count by Molecule"
                },
                {
                    "derived_from": "snv_mutation_burden_by_molecule",
                    "value": 3.5e-07,
                    "key": "Somatic SNV Mutation Burden by Molecule",
                    "tooltip": "Detected somatic mutation / final consensus interrogated base pairs"
                }
            ],
            "sample_cost": "414",
            "cost_efficiency": "140"
        },
        {
            "submitted_id": "NYU_EXTERNAL-QUALITY-METRIC_XYZZY",
            "submission_centers": "nyu_ttd",
            "category": "HiDEF-xyzzy",
            "qc_values": [
                {
                    "derived_from": "total_raw_reads_sequenced",
                    "value": 123,
                    "key": "Total Raw Reads Sequenced",
                    "tooltip": "# of reads (150bp)"
                },
                {
                    "derived_from": "total_raw_bases_sequenced",
                    "value": 456,
                    "key": "Total Raw Bases Sequenced"
                },
                {
                    "derived_from": "prefiltering_number_of_consensus_molecules",
                    "value": 5935091,
                    "key": "Pre-filtering # of Consensus Molecules",
                    "tooltip": "Number of DNA molecules identified"
                },
                {
                    "derived_from": "prefiltering_genome_coverage",
                    "value": 14.98,
                    "key": "Pre-filtering Genome Coverage"
                },
                {
                    "derived_from": "prefiltering_number_of_reads_per_consensus_molecule",
                    "value": 2,
                    "key": "Pre-filtering Number of Reads per Consensus Molecule"
                },
                {
                    "derived_from": "postfiltering_number_of_consensus_molecules",
                    "value": 3108138,
                    "key": "Post-filtering Number of Consensus Molecules"
                },
                {
                    "derived_from": "fraction_prefiltering_molecules_passing_filters",
                    "value": 0.52,
                    "key": "Fraction of Pre-filtering Consensus Molecules that Pass Filters"
                },
                {
                    "derived_from": "number_postfiltering_consensus_base_pairs",
                    "value": 2957487201,
                    "key": "Number of Final Post-filtering Consensus Interrogated Base Pairs",
                    "tooltip": "After applying all filters for variant calling, e.e. Mapping quality, Low complexity regions, a4s2 duplex reconstruction criteria, etc."  # noqa
                },
                {
                    "derived_from": "somatic_snv_count_by_molecule",
                    "value": 1034,
                    "key": "Somatic SNV Count by Molecule"
                },
                {
                    "derived_from": "snv_mutation_burden_by_molecule",
                    "value": 3.5e-07,
                    "key": "Somatic SNV Mutation Burden by Molecule",
                    "tooltip": "Detected somatic mutation / final consensus interrogated base pairs"
                }
            ],
            "sample_cost": "414",
            "cost_efficiency": "140"
        },
        {
            "qc_values": [
                {
                    "derived_from": "total_raw_reads_sequenced",
                    "key": "Total Raw Reads Sequenced",
                    "tooltip": "# of reads (150bp)"
                },
                {
                    "derived_from": "total_raw_bases_sequenced",
                    "key": "Total Raw Bases Sequenced"
                },
                {
                    "derived_from": "prefiltering_number_of_consensus_molecules",
                    "value": 12,
                    "key": "Pre-filtering # of Consensus Molecules",
                    "tooltip": "Number of DNA molecules identified"
                },
                {
                    "derived_from": "prefiltering_genome_coverage",
                    "value": 34.5,
                    "key": "Pre-filtering Genome Coverage"
                },
                {
                    "derived_from": "prefiltering_number_of_reads_per_consensus_molecule",
                    "value": 6,
                    "key": "Pre-filtering Number of Reads per Consensus Molecule"
                },
                {
                    "derived_from": "postfiltering_number_of_consensus_molecules",
                    "value": 789,
                    "key": "Post-filtering Number of Consensus Molecules"
                },
                {
                    "derived_from": "fraction_prefiltering_molecules_passing_filters",
                    "value": 10.11,
                    "key": "Fraction of Pre-filtering Consensus Molecules that Pass Filters"
                },
                {
                    "derived_from": "number_postfiltering_consensus_base_pairs",
                    "value": 1213,
                    "key": "Number of Final Post-filtering Consensus Interrogated Base Pairs",
                    "tooltip": "After applying all filters for variant calling, e.e. Mapping quality, Low complexity regions, a4s2 duplex reconstruction criteria, etc."  # noqa
                },
                {
                    "derived_from": "somatic_snv_count_by_molecule",
                    "value": 150,
                    "key": "Somatic SNV Count by Molecule"
                }
            ],
            "sample_cost": "789",
            "cost_efficiency": "14"
        }
    ],
    "Analyte": [
        {
            "submitted_id": "NYU_ANALYTE_COLO829BLT50",
            "submission_centers": "nyu_ttd",
            "molecule": "DNA",
            "molecule_detail": "Total DNA",
            "dna_integrity_number": "9.8",
            "dna_integrity_number_instrument": "Agilent 4150 TapeStation",
            "samples": "NYU_CELL-CULTURE-SAMPLE_COLO829BLT50",
            "analyte_preparation": "NYU_ANALYTE-PREPARATION_QIAGEN_CELL-KIT"
        }
    ]
}


def test_custom_excel():
    data = StructuredDataSet(excel_class=CustomExcel)
    data.load_file(TEST_EXCEL_FILE)
    assert data.data == EXPECTED_RESULT
