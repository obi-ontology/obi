# OBI RDF examples

Turtle examples of OBI instance data, requested in https://github.com/obi-ontology/obi/issues/1886

`blood-glucose.ttl` renders Figure 2 of https://doi.org/10.1371/journal.pone.0154556 . James A. Overton made an earlier rendering of the same figure in 2015, https://github.com/jamesaoverton/obi-experiment/blob/master/glucose.ttl .

Each example imports `obi.owl`, so OWL tools treat its properties as object and data properties. `catalog-v001.xml` points that import at `build/obi_merged.owl`. `make verify-examples` (part of `make test`) reasons over the examples merged with OBI and fails on inconsistency.
