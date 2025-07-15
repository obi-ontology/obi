import csv
import os
import re
import xml.sax
from datetime import date
from subprocess import run
from xml.sax.saxutils import XMLGenerator


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
        obo = "http://purl.obolibrary.org/obo/"
        bfo = f"{obo}bfo/2014-05-03/classes-only.owl"
        cob = f"{obo}cob/releases/2025-02-20/cob.owl"
        obi_cob = f"{obo}obi/dev/obi-cob-edit.owl"
        xbh = f"{obo}obi/dev/external-byhand.owl"
        so_imp = f"{obo}obi/dev/import/SO_imports.owl"
        ro_imp = f"{obo}obi/dev/import/RO_imports.owl"
        ro = f"{obo}ro/releases/2024-04-24/core.owl"

        if name == "owl:Ontology" and "rdf:about" in attrs.keys():
            new_attrs["rdf:about"] = obi_cob
        if name == "owl:imports" and "rdf:resource" in attrs.keys():
            if attrs["rdf:resource"] == bfo:
                new_attrs["rdf:resource"] = cob
            elif attrs["rdf:resource"] == xbh:
                self.copy_line = False
            elif attrs["rdf:resource"] == so_imp:
                RO_attrs = new_attrs.copy()
                RO_attrs["rdf:resource"] = ro_imp
                self.generator.startElement(name, RO_attrs)
                self.generator.endElement(name)
            elif attrs["rdf:resource"] == ro:
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
        "robot", "convert",
        "-i", obi_cob_edit,
        "--format", "owl",
        "-o", obi_cob_edit
    ])
    run([
        "robot", "merge",
        "--input", obi_cob_edit,
        "query",
        "--format", "TTL",
        "--construct",
        "src/sparql/add-editor-preferred-term-construct.rq",
        "build/editor-preferred-terms.ttl",
        "--construct",
        "src/sparql/add-curation-status-construct.rq",
        "build/curation-status.ttl",
        "merge",
        "--input", "build/editor-preferred-terms.ttl",
        "--input", "build/curation-status.ttl",
        "query",
        "--update", "src/sparql/fix-iao.rq",
        "annotate",
        "--ontology-iri",
        f"{obo}obi/obi_cob_merged.owl",
        "--version-iri",
        f"{obo}obi/{today}/obi_cob_merged.owl",
        "--annotation", "owl:versionInfo", today,
        "--output", "build/obi_cob_merged.tmp.owl",
        ], capture_output=True)
    with open(obi_cob_merged, "w") as outfile:
        run(["sed", '/<owl:imports/d', "build/obi_cob_merged.tmp.owl"],
            stdout=outfile)
    run([
        "rm", "build/obi_cob_merged.tmp.owl"
        ])


def diff(left, right):
    """
    Diff shortcut for ease of use
    """
    run([
        "robot", "diff",
        "--left", left,
        "--right", right,
        "--labels", "true",
        "--output", "build/obi_cob_diff.html",
        "--format", "html"
            ])


def obsolete(merged, obsoleted):
    """
    Return a dict of lines from obsoleted terms, to be replaced later
    """
    print("Deprecating and replacing terms")
    output_lines = []
    obsolete_terms = [
        "OBI_0000011",
        "OBI_0000047",
        "OBI_0000094",
        "OBI_0000968",
        "OBI_0100026",
    ]
    replacements = {
        "OBI_0000011": "COB_0000035",
        "OBI_0000047": "COB_0000026",
        "OBI_0000094": "COB_0000110",
        "OBI_0000968": "COB_0001300",
        "OBI_0100026": "COB_0000022",
    }
    obsolete_dict = {
        "OBI_0000011": [],
        "OBI_0000047": [],
        "OBI_0000094": [],
        "OBI_0000968": [],
        "OBI_0100026": [],
    }
    term_start = "<!-- http://purl.obolibrary.org/obo/"
    term_end = "</owl:Class>"
    eq_start = "<owl:equivalentClass"
    sc_start = "<rdfs:subClassOf"
    dj_start = "<owl:disjointWith"
    eq_end = "</owl:equivalentClass"
    sc_end = "</rdfs:subClassOf"
    dj_end = "</owl:disjointWith"
    obsolete = False
    in_axiom = False
    working_term = None
    with open(merged, "r") as infile:
        lines = infile.readlines()
        for line in lines:
            copy_line = True
            add_obsolete_tag = False
            if term_start in line and not in_axiom:
                working_term = None
                for term in obsolete_terms:
                    if term in line:
                        obsolete = True
                        working_term = term
            if obsolete and term_end in line and not in_axiom:
                obsolete = False
            if obsolete:
                if eq_start in line or sc_start in line or dj_start in line:
                    copy_line = False
                    if "/>" not in line:
                        in_axiom = True
                if in_axiom:
                    copy_line = False
                    if eq_end in line or sc_end in line or dj_end in line:
                        copy_line = False
                        in_axiom = False
                if "rdfs:label" in line:
                    obsolete_label = r">obsolete \1<"
                    line = re.sub(r">([\w\s]+)<", obsolete_label, line)
                    add_obsolete_tag = True
            if copy_line and working_term is None:
                output_lines.append(line)
            elif copy_line:
                line_list = obsolete_dict[working_term]
                if add_obsolete_tag:
                    replacement = replacements[working_term]
                    replaced_by = f"""        <obo:IAO_0100001 rdf:resource="{obo}{replacement}"/>"""
                    line_list.append(replaced_by)
                    line_list.append(line)
                    line_list.append("""        <owl:deprecated rdf:datatype="http://www.w3.org/2001/XMLSchema#boolean">true</owl:deprecated>\n""")
                    add_obsolete_tag = False
                else:
                    line_list.append(line)
                obsolete_dict[working_term] = line_list
    with open(obsoleted, "w") as outfile:
        outfile.writelines(output_lines)
    return obsolete_dict


def restore_obsolete(renamed, obsolete_dict):
    """
    Add lines for obsoleted terms back in
    """
    obsolete_terms = [i for i in obsolete_dict.keys()]
    term_start = "<!-- http://purl.obolibrary.org/obo/"
    in_classes = False
    output_lines = []
    active = 0
    active_id = obsolete_terms[0]
    active_numeric = active_id.split("_")
    active_numeric = int(active_numeric[1])
    insert_obsolete_term = False
    stop_search = False
    with open(renamed, "r") as infile:
        lines = infile.readlines()
        for line in lines:
            if "<owl:Class rdf:about" in line:
                in_classes = True
            if term_start in line and in_classes:
                id = re.search(r"OBI_(\d+)", line)
                if id:
                    id_number = int(id.group(1))
                    if id_number > active_numeric:
                        insert_obsolete_term = True
            if insert_obsolete_term and not stop_search:
                for i in obsolete_dict[active_id]:
                    output_lines.append(i)
                active += 1
                insert_obsolete_term = False
                if active > 4:
                    stop_search
                else:
                    active_id = obsolete_terms[active]
                    active_numeric = active_id.split("_")
                    active_numeric = int(active_numeric[1])
            output_lines.append(line)
    with open(renamed, "w") as outfile:
        outfile.writelines(output_lines)


def rename(obsoleted, renamed, replacements, obsolete_dict):
    """
    Rename uses of obsoleted terms to their COB equivalents
    """
    run([
        "robot", "rename",
        "--input", obsoleted,
        "--mappings", replacements,
        "--output", renamed,
        "--allow-duplicates", "true"
            ])
    restore_obsolete(renamed, obsolete_dict)


def clean_up_unused(renamed, cleaned):
    """
    Remove unused BFO classes and replace them as needed
    """
    print("Trimming unused BFO classes")
    run([
        "robot", "remove",
        "--input", renamed,
        "--term", "BFO:0000028",
        "--term", "BFO:0000066",
        "rename",
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
    run([
        "robot",
        "convert",
        "--input", cleaned,
        "--format", "owl",
        "--output", "build/obi_cob.tmp.owl",
        "annotate",
        "--ontology-iri",
        f"{obo}obi/obi-cob.owl",
        "--version-iri",
        f"{obo}obi/{today}/obi-cob.owl",
        "--annotation", "owl:versionInfo", today,
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
    obi_cob = "obi-cob.owl"
    line_edits(obi_edit, obi_cob_edit)
    build_merged(obi_cob_edit, merged)
    obsolete_dict = obsolete(merged, obsoleted)
    rename(obsoleted, renamed, replacements, obsolete_dict)
    clean_up_unused(renamed, cleaned)
    finalize(cleaned, obi_cob)


if __name__ == "__main__":
    today = date.today().strftime("%Y-%m-%d")
    obo = "http://purl.obolibrary.org/obo/"
    main()
