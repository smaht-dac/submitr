============
Object Model
============

..  Commented out (2023-03-04): Decided do not really need this as this is live on portal.
..    Below are the object types (and data), relevant for metadata submission, supported by SMaHT Portal.

.. raw:: html

    Below are the object <a target="_blank" href="https://data.smaht.org/profiles/" style="color:black">types</a>
    (and data) supported by SMaHT Portal which may be relevant for metadata submission;
    types marked with <b>(A)</b> indicate <i>abstract</i> types wihch cannot be created directly.
    Click on the name for more details.
    These can also be viewed within SMaHT Portal itself in a somewhat more rudimentary form <a target="_blank" href="https://data.smaht.org/submission-schemas/"><b>here</b><span class="fa fa-external-link" style="left:4pt;position:relative;top:2pt;" /></a>

    <p />

Types
-----

.. toctree::
   :hidden:
   :maxdepth: 1

.. raw:: html

    <table><tr><td>
    <ul>
        <li><a href='object_model/types/aligned_reads.html'>AlignedReads</a></li><li><a href='object_model/types/analyte.html'>Analyte</a></li><li><a href='object_model/types/analyte_preparation.html'>AnalytePreparation</a></li><li><a href='object_model/types/assay.html'>Assay</a></li><li><a href='object_model/types/cell_culture.html'>CellCulture</a></li><li><a href='object_model/types/cell_culture_mixture.html'>CellCultureMixture</a></li><li><a href='object_model/types/cell_culture_sample.html'>CellCultureSample</a></li><li><a href='object_model/types/cell_line.html'>CellLine</a></li><li><a href='object_model/types/cell_sample.html'>CellSample</a></li><li><a href='object_model/types/consortium.html'>Consortium</a></li><li><a href='object_model/types/death_circumstances.html'>DeathCircumstances</a></li><li><a href='object_model/types/demographic.html'>Demographic</a></li><li><a href='object_model/types/diagnosis.html'>Diagnosis</a></li><li><a href='object_model/types/document.html'>Document</a></li><li><a href='object_model/types/donor.html'>Donor</a></li><li><a href='object_model/types/exposure.html'>Exposure</a></li><li><a href='object_model/types/file.html'>File</a> <small><b>(A)</b></small></li>
    </ul>
    </td><td style="padding-left:20pt;">
    <ul>
        <li><a href='object_model/types/file_format.html'>FileFormat</a></li><li><a href='object_model/types/file_set.html'>FileSet</a></li><li><a href='object_model/types/filter_set.html'>FilterSet</a></li><li><a href='object_model/types/histology.html'>Histology</a></li><li><a href='object_model/types/image.html'>Image</a></li><li><a href='object_model/types/library.html'>Library</a></li><li><a href='object_model/types/library_preparation.html'>LibraryPreparation</a></li><li><a href='object_model/types/medical_history.html'>MedicalHistory</a></li><li><a href='object_model/types/molecular_test.html'>MolecularTest</a></li><li><a href='object_model/types/ontology_term.html'>OntologyTerm</a></li><li><a href='object_model/types/output_file.html'>OutputFile</a></li><li><a href='object_model/types/preparation.html'>Preparation</a> <small><b>(A)</b></small></li><li><a href='object_model/types/preparation_kit.html'>PreparationKit</a></li><li><a href='object_model/types/protocol.html'>Protocol</a></li><li><a href='object_model/types/quality_metric.html'>QualityMetric</a></li><li><a href='object_model/types/reference_file.html'>ReferenceFile</a></li><li><a href='object_model/types/reference_genome.html'>ReferenceGenome</a></li>
    </ul>
    </td><td style="padding-left:24pt;">
    <ul>
        <li><a href='object_model/types/sample.html'>Sample</a> <small><b>(A)</b></small></li><li><a href='object_model/types/sample_preparation.html'>SamplePreparation</a></li><li><a href='object_model/types/sample_source.html'>SampleSource</a> <small><b>(A)</b></small></li><li><a href='object_model/types/sequencer.html'>Sequencer</a></li><li><a href='object_model/types/sequencing.html'>Sequencing</a></li><li><a href='object_model/types/software.html'>Software</a></li><li><a href='object_model/types/submission_center.html'>SubmissionCenter</a></li><li><a href='object_model/types/submitted_file.html'>SubmittedFile</a> <small><b>(A)</b></small></li><li><a href='object_model/types/therapeutic.html'>Therapeutic</a></li><li><a href='object_model/types/tissue.html'>Tissue</a></li><li><a href='object_model/types/tissue_collection.html'>TissueCollection</a></li><li><a href='object_model/types/tissue_sample.html'>TissueSample</a></li><li><a href='object_model/types/treatment.html'>Treatment</a></li><li><a href='object_model/types/unaligned_reads.html'>UnalignedReads</a></li><li><a href='object_model/types/user.html'>User</a></li><li><a href='object_model/types/variant_calls.html'>VariantCalls</a></li>
    </ul>
    </td></tr></table>


.. tip::
    .. raw:: html

        To view the above types as a <a href="object_model/type_hierarchy.html" style="color:black;">type hierarchy</a>
        <a target="_blank" href="object_model/type_hierarchy.html"</a><b>here</b><span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a>

.. Commented out (2023-03-04): Decided do not really need this as this is live on portal.
.. Data
.. ----

.. .. toctree::
..    :hidden:
..    :maxdepth: 1

..    object_model/data/consortia
..    object_model/data/file_formats
..    object_model/data/reference_genomes
..    object_model/data/submission_centers

.. .. raw:: html
.. 
..     <ul>
..         <li> <a href="object_model/data/consortia.html">Consortia</a> </li>
..         <li> <a href="object_model/data/file_formats.html">File Formats</a> </li>
..         <li> <a href="object_model/data/reference_genomes.html">Reference Genomes</a> </li>
..         <li> <a href="object_model/data/submission_centers.html">Submission Centers</a> </li>
..     </ul>

Data
----

.. raw:: html

    <ul>
            <li> <a target="_blank" href="https://data.smaht.org/search/?type=Consortium">Consortia<span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a> </li>
            <li> <a target="_blank" href="https://data.smaht.org/search/?type=FileFormat">File Formats<span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a> </li>
            <li> <a target="_blank" href="https://data.smaht.org/search/?type=FileFormat&valid_item_types=AlignedReads">File Formats <small>(Aligned Reads)</small><span class="fa fa-external-link" style="left:6pt;position:relative;top:2pt;" /></a></li>
            <li> <a target="_blank" href="https://data.smaht.org/search/?type=FileFormat&valid_item_types=UnalignedReads">File Formats <small>(Unaligned Reads)</small><span class="fa fa-external-link" style="left:6pt;position:relative;top:2pt;" /></a></li>
            <li> <a target="_blank" href="https://data.smaht.org/search/?type=FileFormat&valid_item_types=VariantCalls">File Formats <small>(Variant Calls)</small><span class="fa fa-external-link" style="left:6pt;position:relative;top:2pt;" /></a></li>
            <li> <a target="_blank" href="https://data.smaht.org/search/?type=ReferenceGenome">Reference Genomes<span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a> </li>
            <li> <a target="_blank" href="https://data.smaht.org/search/?type=SubmissionCenter">Submission Centers<span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a> </li>
    </ul>


See Also
--------

.. raw:: html

    <ul>
        <li> <a target="_blank" href="object_model/type_hierarchy.html">Type Hierarchy<span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a> </li>
        <li> <a target="_blank" href="https://data.smaht.org/docs/additional-resources/sample-file-nomenclature">File and Sample Nomenclature<span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a> </li>
        <li> <a target="_blank" href="https://data.smaht.org/docs/user-guide/referencing-data">Referencing Existing Data<span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a> </li>
        <li> <a target="_blank" href="https://data.smaht.org/data/benchmarking">Benchmarking Data<span class="fa fa-external-link" style="left:4pt;position:relative;top:1pt;" /></a> </li>
    </ul>

.. raw:: html

    <span style="color:#aaaaaa;">[ <small>Generated: Tuesday, March 5, 2024 | 11:57 AM EST | <a target='_blank' style="color:#aaaaaa" href='https://data.smaht.org/profiles/?format=json'>data.smaht.org</a> | 0.29.0</small> ]</span><p />
    <p />
