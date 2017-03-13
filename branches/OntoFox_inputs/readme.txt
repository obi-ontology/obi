OntoFox tool website:

http://ontofox.hegroup.org/index.php


Go to section "2. Data input using local text file:", upload OntoFox input file and then save the output OWL file

For UO instance output, following modification need to be made:
	replace 'owl:Class' by 'owl:NamedIndividual' of imported terms (not their parent classes)
	replace 'rdfs:subClassOf' by 'rdf:type'