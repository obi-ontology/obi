"""
Read RDF/XML OWL files and identify annotations for specific terms.

This script is an accessory script for import.py that uses xml.sax to
parse XML. It enables the following types of searches:
    * Given a term's CURIE, return its OWL type, rdfs:label, and parent class
    * Given a term's label, return its IRI
"""


from xml.sax import make_parser
from xml.sax.saxutils import XMLFilterBase


class InformationFound(Exception):
    pass


class TermFinder(XMLFilterBase):
    """
    Identifies XML associated with a particular CURIE
    """

    def __init__(self, curie, label_text, parent_class, parent=None):
        curie_parts = curie.split(":")
        iri_base = "_".join(curie_parts)
        self.iri = f"http://purl.obolibrary.org/obo/{iri_base}"
        self.label = False
        self.match = False
        self.termtype = ""
        self.content = ""
        self.parent_class = ""
        super().__init__(parent)

    def startElement(self, name, attrs):
        options = ["owl:Class", "owl:AnnotationProperty", "owl:ObjectProperty", "rdf:Description"]
        parent_options = ["rdfs:subClassOf", "rdfs:subPropertyOf"]
        if name in options:
            if "rdf:about" in attrs.keys():
                if attrs["rdf:about"] == self.iri:
                    self.match = True
                    self.termtype = name
        elif name == "rdfs:label" and self.match:
            self.label = True
        elif name in parent_options and self.match:
            if "rdf:resource" in attrs.keys():
                self.parent_class = attrs["rdf:resource"]

    def characters(self, content):
        if self.label:
            self.label_text = content
            raise InformationFound()

    def endElement(self, name):
        pass


class FindByLabel(XMLFilterBase):
    """
    Identifies XML associated with a particular label
    """

    def __init__(self, label_text, iri, parent_class, parent=None):
        self.label_text = label_text
        self.iri = ""
        self.label = False
        self.match = False
        self.termtype = ""
        self.content = ""
        self.parent_class = ""
        super().__init__(parent)

    def startElement(self, name, attrs):
        options = ["owl:Class", "owl:AnnotationProperty", "owl:ObjectProperty", "rdf:Description"]
        parent_options = ["rdfs:subClassOf", "rdfs:subPropertyOf"]
        if name in options:
            if "rdf:about" in attrs.keys():
                self.termtype = name
                self.iri = attrs["rdf:about"]
        elif name == "rdfs:label":
            self.label = True
        elif name in parent_options and self.match:
            if "rdf:resource" in attrs.keys():
                self.parent_class = attrs["rdf:resource"]

    def characters(self, content):
        if self.label:
            if content == self.label_text:
                raise InformationFound()

    def endElement(self, name):
        pass


def get_term_info(curie, owl_file, listmode=False):
    """
    Return OWL type, label, and parent class of a term based on its CURIE
    """
    found = False
    label_text, parent_class = "", ""
    reader = TermFinder(curie, label_text, parent_class, make_parser())
    try:
        reader.parse(owl_file)
    except InformationFound:
        pass
        found = True
        return reader.termtype, reader.label_text, reader.parent_class
    if not found and listmode:
        print(f"Didn't find {curie} in this OWL file.")
    elif not found:
        raise ValueError(f"Didn't find {curie} in this OWL file.")


def get_iri_from_label(label, owl_file):
    """
    Return IRI of a term based on its label
    """
    iri, parent_class = "", ""
    reader = FindByLabel(label, iri, parent_class, make_parser())
    try:
        reader.parse(owl_file)
    except InformationFound:
        pass
        return reader.iri
