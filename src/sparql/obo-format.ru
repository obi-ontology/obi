PREFIX obo: <http://purl.obolibrary.org/obo/>
PREFIX oboInOwl: <http://www.geneontology.org/formats/oboInOwl#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

# Change 'alternative term' to OBO synonym
INSERT { ?s oboInOwl:hasExactSynonym ?syn }
WHERE { ?s obo:IAO_0000118 ?syn } ;

# Change 'NIADID GSCID-BRC alternative term ' to OBO synonym
INSERT { ?s oboInOwl:hasExactSynonym ?syn }
WHERE { ?s obo:OBI_0001886 ?syn } ;

# Change 'ISA alternative term' to OBO synonym
INSERT { ?s oboInOwl:hasExactSynonym ?syn }
WHERE { ?s obo:OBI_0001847 ?syn } ;

# Change 'IEDB alternative term' to OBO synonym
INSERT { ?s oboInOwl:hasExactSynonym ?syn }
WHERE { ?s obo:OBI_9991118 ?syn } ;

# Change 'term editor' to created by (making a list to prevent OBO error)
INSERT { ?s oboInOwl:created_by ?termEds }
WHERE { SELECT (GROUP_CONCAT(?termEd;separator=", ") AS ?termEds) WHERE {
        	?s obo:IAO_0000117 ?termEd 
        } } ;

# if it has more than one definition, remove them both for now
# we need to fix versioning on imported terms
DELETE { ?s obo:IAO_0000115 ?def }
WHERE { ?s obo:IAO_0000115 ?def, ?def2 .
		FILTER(?def != ?def2) } ;

# handle ientities with multiple labels by marking one precious
# indiscriminately picks which label to use (first one in group)
INSERT { ?s rdfs:label-precious ?precious }
WHERE {
  {
    SELECT ?s (STRBEFORE(GROUP_CONCAT(?dupLabel; separator="|"), "|") AS ?precious) WHERE {
      ?s rdfs:label ?label, ?dupLabel .
      FILTER (?label != ?dupLabel)
    }
    GROUP BY ?s
  }
} ;

# then removing all others and changing the 'precious' to regular label
DELETE { 
  ?s rdfs:label-precious ?labelP .
  ?s rdfs:label ?label .
}
INSERT { ?s rdfs:label ?labelP }
WHERE { 
  ?s rdfs:label-precious ?labelP .
  ?s rdfs:label ?label .
}
