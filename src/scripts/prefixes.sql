CREATE TABLE IF NOT EXISTS prefix (
  prefix TEXT PRIMARY KEY,
  base TEXT NOT NULL
);

INSERT OR IGNORE INTO prefix VALUES
("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
("rdfs", "http://www.w3.org/2000/01/rdf-schema#"),
("xsd", "http://www.w3.org/2001/XMLSchema#"),
("owl", "http://www.w3.org/2002/07/owl#"),
("oio", "http://www.geneontology.org/formats/oboInOwl#"),
("dce", "http://purl.org/dc/elements/1.1/"),
("dct", "http://purl.org/dc/terms/"),
("foaf", "http://xmlns.com/foaf/0.1/"),
("obo", "http://purl.obolibrary.org/obo/"),

("BFO", "http://purl.obolibrary.org/obo/BFO_"),
("CHMO", "http://purl.obolibrary.org/obo/CHMO_"),
("CL", "http://purl.obolibrary.org/obo/CL_"),
("CLO", "http://purl.obolibrary.org/obo/CLO_"),
("CHEBI", "http://purl.obolibrary.org/obo/CHEBI_"),
("ENVO", "http://purl.obolibrary.org/obo/ENVO_"),
("GO", "http://purl.obolibrary.org/obo/GO_"),
("HP", "http://purl.obolibrary.org/obo/HP_"),
("IAO", "http://purl.obolibrary.org/obo/IAO_"),
("IDO", "http://purl.obolibrary.org/obo/IDO_"),
("NCBITaxon", "http://purl.obolibrary.org/obo/NCBITaxon_"),
("OBI", "http://purl.obolibrary.org/obo/OBI_"),
("OGMS", "http://purl.obolibrary.org/obo/OGMS_"),
("OMIABIS", "http://purl.obolibrary.org/obo/OMIABIS_"),
("OMRSE", "http://purl.obolibrary.org/obo/OMRSE_"),
("PATO", "http://purl.obolibrary.org/obo/PATO_"),
("PR", "http://purl.obolibrary.org/obo/PR_"),
("SO", "http://purl.obolibrary.org/obo/SO_"),
("UBERON", "http://purl.obolibrary.org/obo/UBERON_"),
("UO", "http://purl.obolibrary.org/obo/UO_"),
("VO", "http://purl.obolibrary.org/obo/VO_");
