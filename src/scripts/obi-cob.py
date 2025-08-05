import os
import xml.sax
from datetime import date
from subprocess import run
from xml.sax.saxutils import XMLGenerator


TODAY = date.today().strftime("%Y-%m-%d")
OBO = "http://purl.obolibrary.org/obo"


class ImportModifier(xml.sax.ContentHandler):
    """
    Adjust imports by copying and modifying lines from obi-edit.owl
    """

    def __init__(self, output_file):
        self.generator = XMLGenerator(output_file,
                                      "utf-8",
                                      short_empty_elements=True)
        self.current_element = None
        self.copy_line = True

    def startDocument(self):
        self.generator.startDocument()

    def endDocument(self):
        self.generator.endDocument()

    def startElement(self, name, attrs):
        self.current_element = name
        new_attrs = dict(attrs)
        self.copy_line = True
        if name == "owl:Ontology" and "rdf:about" in attrs.keys():
            new_attrs["rdf:about"] = f"{OBO}/obi/dev/obi-cob-edit.owl"
        if name == "owl:imports" and "rdf:resource" in attrs.keys():
            resource = "rdf:resource"
            if attrs[resource] == f"{OBO}/bfo/2014-05-03/classes-only.owl":
                new_attrs[resource] = f"{OBO}/cob/releases/2025-02-20/cob.owl"
            elif attrs[resource] == f"{OBO}/obi/dev/external-byhand.owl":
                self.copy_line = False
            elif attrs[resource] == f"{OBO}/obi/dev/import/SO_imports.owl":
                RO_attrs = new_attrs.copy()
                RO_attrs[resource] = f"{OBO}/obi/dev/import/RO_imports.owl"
                self.generator.startElement(name, RO_attrs)
                self.generator.endElement(name)
            elif attrs[resource] == f"{OBO}/ro/releases/2024-04-24/core.owl":
                self.copy_line = False
        if self.copy_line:
            self.generator.startElement(name, new_attrs)

    def endElement(self, name):
        if self.copy_line:
            self.generator.endElement(name)

    def characters(self, content):
        if self.copy_line:
            self.generator.characters(content)


def line_edits(input, output):
    """
    Import COB, switch to OntoFox RO import, drop BFO, drop external-byhand
    """
    print("Importing COB")
    with open(input, "r") as infile, open(output, "w") as outfile:
        parser = xml.sax.make_parser()
        handler = ImportModifier(outfile)
        parser.setContentHandler(handler)
        parser.parse(infile)


def build_merged(obi_cob_edit, obi_cob_merged):
    """
    Convert edit file to merged file, format, and annotate
    """
    run([
        "build/robot", "convert",
        "-i", obi_cob_edit,
        "--format", "owl",
        "-o", obi_cob_edit
    ])
    run(["cp", "src/ontology/obi-cob-edit.owl", "src/ontology/obi-edit.owl"])
    run(["make", "build/obi_merged.owl"],
        capture_output=True)
    run(["cp", "build/obi_merged.owl", obi_cob_merged])
    run(["git", "restore", "src/ontology/obi-edit.owl"])


def diff(left, right):
    """
    Diff shortcut for ease of use
    """
    run([
        "build/robot", "diff",
        "--left", left,
        "--right", right,
        "--labels", "true",
        "--output", "build/obi_cob_diff.html",
        "--format", "html"
            ])


class MakeObsolete(xml.sax.ContentHandler):
    """
    Inserts lines to obsolete target classes
    """

    def __init__(self, output_file):
        self.generator = XMLGenerator(output_file,
                                      "utf-8",
                                      short_empty_elements=True)
        self.current_element = None
        self.copy_line = True
        self.in_axiom = False
        self.obsolete = False
        self.obsolete_label = True
        self.working_term = ""
        self.axioms = [
            "rdfs:subClassOf",
            "owl:equivalentClass",
            "owl:disjointWith"
            ]
        self.obsolete_terms = {
            "OBI_0000011": "COB_0000035",
            "OBI_0000047": "COB_0000026",
            "OBI_0000094": "COB_0000110",
            "OBI_0000968": "COB_0001300",
            "OBI_0100026": "COB_0000022",
        }

    def startDocument(self):
        self.generator.startDocument()

    def endDocument(self):
        self.generator.endDocument()

    def startElement(self, name, attrs):
        self.current_element = name
        if name == "owl:Class" and not self.in_axiom:
            if "rdf:about" in attrs.keys():
                for i in self.obsolete_terms.keys():
                    iri = f"{OBO}/{i}"
                    if attrs["rdf:about"] == iri:
                        self.working_term = i
                        self.obsolete = True
        if not self.copy_line and not self.in_axiom:
            self.copy_line = True
        if self.obsolete and name in self.axioms:
            self.in_axiom = True
            self.copy_line = False
        if self.obsolete and name == "rdfs:label":
            self.obsolete_label = True
            replacement = self.obsolete_terms[self.working_term]
            replaced_by = {"rdf:resource": f"{OBO}/{replacement}"}
            self.generator.startElement("obo:IAO_0100001", replaced_by)
            self.generator.endElement("obo:IAO_0100001")
        if self.copy_line:
            self.generator.startElement(name, attrs)

    def endElement(self, name):
        if self.obsolete and not self.in_axiom and name == "owl:Class":
            self.obsolete = False
        if self.obsolete and self.in_axiom and name in self.axioms:
            self.in_axiom = False
        if self.copy_line:
            self.generator.endElement(name)
        if self.obsolete_label:
            if name == "rdfs:label":
                depr_attrs = dict()
                depr_attrs["rdf:datatype"] = \
                    "http://www.w3.org/2001/XMLSchema#boolean"
                self.generator.startElement("owl:deprecated",
                                            depr_attrs)
                self.generator.characters("true")
                self.generator.endElement("owl:deprecated")
            self.obsolete_label = False

    def characters(self, content):
        if self.copy_line:
            if self.obsolete_label:
                content = f"obsolete {content}"
            self.generator.characters(content)


def obsolete(merged, obsoleted, replacements, renamed):
    """
    Obsolete and replace terms
    """
    print("Deprecating and replacing terms")
    with open(merged, "r") as infile, open(obsoleted, "w") as outfile:
        parser = xml.sax.make_parser()
        handler = MakeObsolete(outfile)
        parser.setContentHandler(handler)
        parser.parse(infile)
    run(["build/robot", "repair",
         "-i", obsoleted,
         "-o", renamed
         ])
    run([
        "build/robot", "rename",
        "--input", renamed,
        "--mappings", replacements,
        "--output", renamed,
        "--allow-duplicates", "true"
        ])


def clean_up_unused(renamed, cleaned):
    """
    Remove unused BFO classes and replace them as needed
    """
    print("Trimming unused BFO classes")
    run([
        "build/robot", "remove",
        "--input", renamed,
        "--term", "BFO:0000028",
        "--term", "BFO:0000066",
        "rename",  # This is for SO:region only.
        "--mapping", "obo:BFO_0000031", "obo:BFO_0000040",
        "remove",
        "--term", "IAO:0000030",
        "--select", """\"self parents\"""",
        "--trim", "false",
        "--output", cleaned
                ])


def finalize(cleaned, obi_cob):
    """
    Annotate the final output file
    """
    print("Annotating with version IRI")
    run(["cp", cleaned, "build/obi_merged.owl"])
    run(["make", "obi.owl"], capture_output=True)
    run(["cp", "obi.owl", cleaned])
    run(["git", "restore", "obi.owl"])
    run([
        "build/robot",
        "convert",
        "--input", cleaned,
        "--format", "owl",
        "--output", "build/obi_cob.tmp.owl",
        "annotate",
        "--ontology-iri",
        f"{OBO}/obi/obi-cob.owl",
        "--version-iri",
        f"{OBO}/obi/{TODAY}/obi-cob.owl",
        "--annotation", "owl:versionInfo", TODAY,
        "--output", obi_cob,
                    ])
    run([
        "rm", "build/obi_cob.tmp.owl"
        ])
    print("Wrote obi-cob.owl")


def main():
    obi_edit = os.path.join("src", "ontology", "obi-edit.owl")
    obi_cob_edit = os.path.join("src", "ontology", "obi-cob-edit.owl")
    merged = os.path.join("build", "obi_cob_merged.owl")
    obsoleted = os.path.join("build", "obi_cob_obsoleted.owl")
    renamed = os.path.join("build", "obi_cob_renamed.owl")
    replacements = os.path.join("src", "ontology", "obi_cob_replacements.tsv")
    cleaned = os.path.join("build", "obi_cob_cleaned.owl")
    obi_cob = os.path.join("views", "obi-cob.owl")
    line_edits(obi_edit, obi_cob_edit)
    build_merged(obi_cob_edit, merged)
    obsolete(merged, obsoleted, replacements, renamed)
    clean_up_unused(renamed, cleaned)
    finalize(cleaned, obi_cob)


if __name__ == "__main__":
    main()
