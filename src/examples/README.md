# OBI RDF examples

Turtle examples of OBI instance data, requested in https://github.com/obi-ontology/obi/issues/1886

`blood-glucose.ttl` renders Figure 2 of https://doi.org/10.1371/journal.pone.0154556 . James A. Overton made an earlier rendering of the same figure in 2015, https://github.com/jamesaoverton/obi-experiment/blob/master/glucose.ttl . `blood-glucose.ttl` leaves out the figure's specimen role and measure function, because typing the specimen as 'blood specimen' and the device as 'glucometer' already implies them.

`exome-sequencing.ttl` renders the biobank encounter, specimen collection, DNA extraction, exome sequencing, allele calling and health care encounter parts of the graph on the 2019 TURBO poster, https://github.com/PennTURBO/Turbo-Documentation/blob/master/IBI_CIC_TURBO_MAM_20190102.pdf .

`neon-soil-metagenome.ttl` renders the pooling, DNA extraction, library preparation, metagenome sequencing, read quality control, assembly, annotation and binning steps recorded by the National Microbiome Data Collaborative (NMDC) for the National Ecological Observatory Network (NEON) soil metagenomes study, https://data.microbiomedata.org/details/study/nmdc:sty-11-34xj1150 .

Each example imports `obi.owl`, so OWL tools treat its properties as object and data properties. `catalog-v001.xml` points that import at `build/obi_merged.owl`. `make verify-examples` (part of `make test`) reasons over the examples merged with OBI and fails on inconsistency.
