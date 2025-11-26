import os
from xml.sax import make_parser
from xml.sax.saxutils import XMLFilterBase
from obi.ontofox import Ontofox, Term
from obi.util import contract


class UsageFound(Exception):
    pass


class UsageFinder(XMLFilterBase):
    """
    Identifies if a particular term is used in another term's axioms
    """

    def __init__(self, iri, parent=None):
        self.in_axiom = False
        self.axiom_type = None
        self.iri = iri
        super().__init__(parent)

    def startElement(self, name, attrs):
        axioms = ["rdfs:subClassOf", "owl:equivalentClass", "owl:disjointWith"]
        if name in axioms and not self.in_axiom:
            self.in_axiom = True
            self.axiom_type = name
        if self.in_axiom:
            if "rdf:about" in attrs.keys() and \
                    attrs["rdf:about"] == self.iri:
                raise UsageFound
            elif "rdf:resource" in attrs.keys() and \
                    attrs["rdf:resource"] == self.iri:
                raise UsageFound
        if self.in_axiom and "rdf:resource" in attrs.keys():
            if attrs["rdf:resource"] == self.iri:
                raise UsageFound()
        elif name == "obo:IAO_0100001" and "rdf:resource" in attrs.keys():
            if attrs["rdf:resource"] == self.iri:
                raise UsageFound()

    def endElement(self, name):
        if self.in_axiom and name == self.axiom_type:
            self.in_axiom = False
            self.axiom_type = None


def is_used_in(iri, owl_file):
    """
    Return True if a term is used in the axioms of an OWL file and False if not
    """
    found = False
    reader = UsageFinder(iri, make_parser())
    try:
        reader.parse(owl_file)
    except UsageFound:
        found = True
    return found


def check_file(ontology):
    print(f"Checking {ontology} config file for unused terms...")
    unused = []
    path = Ontofox.find(ontology)
    if not path:
        raise Exception(f'No OntoFox configuration file for {ontology}')
    config = Ontofox(path)
    for key in config.terms.keys():
        if not is_used_in(key, "obi.owl"):
            unused.append(key)
    if len(unused) == 0:
        print(f"\tNo unused terms found in {ontology} config file")
    else:
        unused_count = len(unused)
        plural = "s"
        if unused_count == 1:
            plural = ""
        print(f"\t{unused_count} unused term{plural} found in {ontology} config file")
        for iri in unused:
            curie = contract(iri)
            config.remove(Term(curie, None))
        config.sort()
        config.save()
