==============
Type Hierarchy
==============
Below is a depiction of the parent/child relationship hierarchy of the types supported by SMaHT Portal.
Items suffixed with **(A)** are abstract types which may not be directly created.

.. raw:: html

    <pre>
        └─ <a href='../object_model.html#types'><b>Types</b></a>
           ├── <a href='types/analyte.html'>Analyte</a>
           ├── <a href='types/assay.html'>Assay</a>
           ├── <a href='types/cell_line.html'>CellLine</a>
           ├── <a href='types/consortium.html'>Consortium</a>
           ├── <a href='types/death_circumstances.html'>DeathCircumstances</a>
           ├── <a href='types/demographic.html'>Demographic</a>
           ├── <a href='types/diagnosis.html'>Diagnosis</a>
           ├── <a href='types/document.html'>Document</a>
           ├── <a href='types/donor.html'>Donor</a>
           ├── <a href='types/exposure.html'>Exposure</a>
           ├── <a href='types/family_history.html'>FamilyHistory</a>
           ├── <a href='types/file.html'>File</a> <small><b>(A)</b></small>
           │   ├── <a href='types/output_file.html'>OutputFile</a>
           │   ├── <a href='types/reference_file.html'>ReferenceFile</a>
           │   └── <a href='types/submitted_file.html'>SubmittedFile</a> <small><b>(A)</b></small>
           │       ├── <a href='types/aligned_reads.html'>AlignedReads</a>
           │       ├── <a href='types/unaligned_reads.html'>UnalignedReads</a>
           │       └── <a href='types/variant_calls.html'>VariantCalls</a>
           ├── <a href='types/file_format.html'>FileFormat</a>
           ├── <a href='types/file_set.html'>FileSet</a>
           ├── <a href='types/filter_set.html'>FilterSet</a>
           ├── <a href='types/histology.html'>Histology</a>
           ├── <a href='types/image.html'>Image</a>
           ├── <a href='types/library.html'>Library</a>
           ├── <a href='types/medical_history.html'>MedicalHistory</a>
           ├── <a href='types/medical_treatment.html'>MedicalTreatment</a>
           ├── <a href='types/ontology_term.html'>OntologyTerm</a>
           ├── <a href='types/preparation.html'>Preparation</a> <small><b>(A)</b></small>
           │   ├── <a href='types/analyte_preparation.html'>AnalytePreparation</a>
           │   ├── <a href='types/library_preparation.html'>LibraryPreparation</a>
           │   └── <a href='types/sample_preparation.html'>SamplePreparation</a>
           ├── <a href='types/preparation_kit.html'>PreparationKit</a>
           ├── <a href='types/protocol.html'>Protocol</a>
           ├── <a href='types/quality_metric.html'>QualityMetric</a>
           ├── <a href='types/reference_genome.html'>ReferenceGenome</a>
           ├── <a href='types/sample.html'>Sample</a> <small><b>(A)</b></small>
           │   ├── <a href='types/cell_culture_sample.html'>CellCultureSample</a>
           │   ├── <a href='types/cell_sample.html'>CellSample</a>
           │   └── <a href='types/tissue_sample.html'>TissueSample</a>
           ├── <a href='types/sample_source.html'>SampleSource</a> <small><b>(A)</b></small>
           │   ├── <a href='types/cell_culture.html'>CellCulture</a>
           │   │   └── <a href='types/cell_culture_mixture.html'>CellCultureMixture</a>
           │   └── <a href='types/tissue.html'>Tissue</a>
           ├── <a href='types/sequencer.html'>Sequencer</a>
           ├── <a href='types/sequencing.html'>Sequencing</a>
           ├── <a href='types/software.html'>Software</a>
           ├── <a href='types/submission_center.html'>SubmissionCenter</a>
           ├── <a href='types/tissue_collection.html'>TissueCollection</a>
           ├── <a href='types/treatment.html'>Treatment</a>
           └── <a href='types/user.html'>User</a>

    </pre>
