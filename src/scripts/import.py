"""
Manage files to be used as inputs in the ROBOT import workflow.

This script automatically edits the main input file for an ontology import
(src/ontology/robot_inputs/*_inputs.tsv).

The script can take the following actions on an import file:
    * IMPORT terms
    * IGNORE terms, preventing them from appearing in the resulting OWL file
    * REMOVE terms from the input file
    * SPLIT the input file into several build files to be passed to ROBOT

Flags modify the behavior of these actions:
    * LIMIT (-l) imports terms as upper limits to the hierarchy
    * PARENT (-p) sets a named parent for imported terms
    * SOURCE (-s) sets a non-default file path to use as the import source

Other actions can be used to choose a specific ontology file to import from:
    * CHANGE-SOURCE sets an IRI as the source file for an import module
    * GET-SOURCE downloads the source file for an import module
    * REMOVE-SOURCE removes a set source file, resetting to a default of
      http://purl.obolibrary.org/obo/<ONTOLOGY>.owl
"""


import argparse
import os
import re
from subprocess import run
from owl_reader import get_term_info, get_iri_from_label
from TSV_dict_converter import dict2TSV, TSV2dict


def import_file_check(path):
    """
    Check if an input file exists and create it if not
    """
    if not os.path.exists(path):
        override = input(f"Didn't find {path}. Create it? (y/n)\n")
        if override.lower() == "y" or override.lower() == "yes":
            robot_row = {
                "ontology ID": "ID",
                "label": "",
                "action": "",
                "logical type": "CLASS_TYPE",
                "parent class": "C %"
            }
            starter_dict = {
                "robot": robot_row,
            }
            dict2TSV(starter_dict, path)
        else:
            quit()


def read_to_list(txt):
    """
    Make a list of lines in a text file with newline characters removed
    """
    output = []
    with open(txt, "r") as file:
        lines = file.readlines()
        for line in lines:
            output.append(line.strip())
    return output


def write_to_txt(items, txt):
    """
    Write a text file with one list item per line
    """
    line_broken_items = [f"{item}\n" for item in items]
    with open(txt, "w") as file:
        file.writelines(line_broken_items)
        file.close()


def convert(string, format):
    """
    Convert OBO IRIs to CURIEs and vice versa
    """
    iri = re.search(r"http:\/\/purl\.obolibrary\.org\/obo\/([a-zA-Z]+)_(\d+)",
                    string)
    curie = re.search(r"([a-zA-Z]+):(\d+)", string)
    if not iri and not curie:
        output = None
        print(f"{string} isn't an IRI or a CURIE")
        quit()
    elif format == "iri":
        if iri:
            output = string
        elif curie:
            base = curie.group(1)
            num = curie.group(2)
            output = f"http://purl.obolibrary.org/obo/{base}_{num}"
    elif format == "curie":
        if curie:
            output = string
        elif iri:
            base = iri.group(1)
            num = iri.group(2)
            output = f"{base}:{num}"
    return output


def lookup_curie_from_label(label, source):
    """
    Find the CURIE of a term based on its label
    """
    iri = get_iri_from_label(label, source)
    if iri is None:
        print(f"Didn't find a CURIE for '{label}' in {source}.")
        curie = None
    else:
        curie = convert(iri, "curie")
    return curie


def make_curie_dict(curie, source, listmode=False):
    """
    Make a dict of a term's CURIE, label, and OWL type
    """
    try:
        owl_type, label, parent = get_term_info(curie, source, listmode)
        term_info = {
            "curie": curie,
            "label": label,
            "owl_type": owl_type
        }
        return term_info
    except TypeError:
        return None


def obsolescence_check(label):
    """
    Return True if a term is obsolete/deprecated and False if not
    """
    if "obsolete" in label.lower() or "deprecated" in label.lower():
        print(f"Term '{label}' is deprecated and will not be imported")
        obsolete = True
    else:
        obsolete = False
    return obsolete


def parse_term_input(string, ontology, source):
    """
    Handle term input that may be a CURIE, IRI, label, or path
    """
    error_message = "Try again with a text file, IRI, CURIE, or label."
    listmode = False
    if os.path.isfile(string):
        listmode = True
        root, ext = os.path.splitext(string)
        try:
            if ext.lower() != ".txt":
                raise ValueError("This path doesn't point to a text file.")
        except ValueError:
            print(f"{string} isn't a text file.")
            print(error_message)
            quit()
        term_list = read_to_list(string)
    else:
        term_list = [string,]
    input_dict = {}
    for term in term_list:
        iri = re.search(
            r"http:\/\/purl\.obolibrary\.org\/obo\/([a-zA-Z]+)_(\d+)",
            term
        )
        curie = re.search(r"([a-zA-Z]+):(\d+)", term)
        if iri:
            term_curie = convert(iri.group(0), "curie")
            curie_dict = make_curie_dict(term_curie, source, listmode)
            if curie_dict is None:
                continue
            if not obsolescence_check(curie_dict["label"]):
                input_dict[term_curie] = curie_dict
        elif curie:
            curie_dict = make_curie_dict(curie.group(0), source, listmode)
            if curie_dict is None:
                continue
            if not obsolescence_check(curie_dict["label"]):
                input_dict[term] = curie_dict
        else:
            try:
                label_curie = lookup_curie_from_label(term, source)
                if label_curie:
                    curie_dict = make_curie_dict(label_curie, source, listmode)
                    if curie_dict is None:
                        continue
                    if not obsolescence_check(curie_dict["label"]):
                        input_dict[label_curie] = curie_dict
                else:
                    raise ValueError("Couldn't find a term with this label")
            except ValueError:
                print(f"Label '{term}' wasn't found in {ontology}.")
                print(error_message)
                quit()
    return input_dict


def lookup_label(id, source, listmode=False):
    """
    Identify the label of a term based on its CURIE
    """
    curie = re.search(r"([a-zA-Z]+):(\d+)", id)
    output = id
    if curie:
        termtype, label, parent = get_term_info(id, source, listmode)
        if "obsolete" in label.lower() or "deprecated" in label.lower():
            print(f"{id} '{label}' is deprecated and will not be included in this import")
            output = "deprecated"
    return output


def lookup_parents(id, mode, source, listmode=False):
    """
    Identify superclasses of a term based on its CURIE
    """
    curie = re.search(r"([a-zA-Z]+):(\d+)", id)
    parents = set()
    if curie:
        _, _, parent = get_term_info(id, source, listmode)
        if parent != "" and parent != "http://www.w3.org/2002/07/owl#Thing":
            parent_curie = convert(parent, "curie")
            parent_list = [parent_curie,]
        else:
            parent_list = []
        if mode == "soft":
            parents = set(parent_list)
        elif mode == "hard":
            while len(parent_list) != 0:
                storage = set()
                for i in parent_list:
                    parents.add(i)
                    storage.add(i)
                parent_list = set()
                for i in storage:
                    _, _, upper_parent = get_term_info(i, source, listmode)
                    if upper_parent != "" and upper_parent != "http://www.w3.org/2002/07/owl#Thing":
                        upper_curie = convert(upper_parent, "curie")
                        parent_list.add(upper_curie)
    return parents


def do_import(term_dict, imports, limit, parent, source):
    """
    Import a term
    """
    for term, term_info in term_dict.items():
        act = True
        relate = False
        label = term_info["label"]
        if "owl:ObjectProperty" in term_info["owl_type"]:
            relate = True
        if term in imports.keys():
            act = False
            if imports[term]["action"] != "ignore":
                act_conditions = [
                    limit and imports[term]["action"] != "limit",
                    relate and imports[term]["action"] != "relate",
                    parent and imports[term]["parent class"] != parent
                ]
                if act_conditions != [False, False, False]:
                    act = True
                else:
                    print(f"{term} '{label}' is already imported")
            else:
                override = input(f"{term} '{label}' is ignored. Override? [y/n]\n")
                if override.lower() == "y" or override.lower() == "yes":
                    act = True
        if act:
            imports[term] = {
                "ontology ID": term,
                "label": label,
                "action": "import",
                "logical type": "",
                "parent class": ""
            }
            confirmation_text = ""
            if limit:
                imports[term]["action"] = "limit"
                confirmation_text = " as a limit"
            if parent:
                imports, confirmation_text = do_parent(
                    term_info,
                    parent,
                    imports,
                    source
                )
            if relate:
                imports[term]["action"] = "relate"
                confirmation_text = " as a relation"
            print(f"Added {term} '{label}' to import{confirmation_text}")


def do_ignore(term_dict, imports):
    """
    Prevent a term from being imported
    """
    for term, term_info in term_dict.items():
        label = term_info["label"]
        if term in imports.keys() and imports[term]["action"] == "ignored":
            print(f"{term} '{label}' is already ignored")
        else:
            imports[term] = {
                "ontology ID": term,
                "label": label,
                "action": "ignore",
                "logical type": "",
                "parent class": ""
            }
            print(f"Ignored {term} '{label}'")


def do_remove(term_dict, imports):
    """
    Remove references to a term in the import dict
    """
    for term, term_info in term_dict.items():
        label = term_info["label"]
        if term not in imports.keys():
            print(f"{term} '{label}' is not in this import")
        else:
            act = False
            if imports[term]["action"] == "ignore":
                override = input(f"{term} '{label}' is ignored. Remove anyway? [y/n]\n")
                if override.lower() == "y" or override.lower() == "yes":
                    act = True
                else:
                    print(f"{term} '{label}' was not removed from this import")
            else:
                act = True
            if act:
                del imports[term]
                print(f"Removed {term} '{label}' from this import")


def do_parent(term_info, parent, imports, source):
    """
    Assert a parent class for a term to be imported
    """
    confirmation_text = ""
    term = term_info["curie"]
    label = term_info["label"]
    act = True
    parents = lookup_parents(term, "hard", source)
    parent_labels = []
    for parent_id in parents:
        parent_label = lookup_label(parent_id, source)
        parent_labels.append(parent_label)
    if parent in parent_labels:
        print(f"{term} '{label}' is already a subclass of '{parent}' in the ontology")
        act = False
    if act:
        imports[term] = {
            "ontology ID": term,
            "label": label,
            "action": "import",
            "logical type": "subclass",
            "parent class": parent
        }
        confirmation_text = f" as a subclass of '{parent}'"
    return imports, confirmation_text


def split(ontology, imports_dict):
    """
    Split imports into build files needed by ROBOT import workflow
    """
    imports, ignore, parent, relation, limit = [], [], {}, [], []
    imports_path = os.path.join("build", f"{ontology}_import.txt")
    ignore_path = os.path.join("build", f"{ontology}_ignore.txt")
    parent_path = os.path.join("build", f"{ontology}_parent.tsv")
    relation_path = os.path.join("build", f"{ontology}_relations.txt")
    limit_path = os.path.join("build", f"{ontology}_limit.txt")
    parent["robot"] = imports_dict["robot"]
    for id, row in imports_dict.items():
        label = row["label"]
        if row["action"] == "import":
            imports.append(f"{id} # {label}")
            if row["parent class"] != "":
                parent[id] = row
        elif row["action"] == "ignore":
            ignore.append(f"{id} # {label}")
        elif row["action"] == "relate":
            relation.append(f"{id} # {label}")
        elif row["action"] == "limit":
            limit.append(f"{id} # {label}")
    for (xlist, xpath) in [
        (imports, imports_path),
        (ignore, ignore_path),
        (relation, relation_path),
        (limit, limit_path)
    ]:
        write_to_txt(sorted(xlist), xpath)
    dict2TSV(parent, parent_path)
    for i in imports_path, ignore_path, parent_path, relation_path, limit_path:
        print(f"Wrote {i}")


def universalize(action, input_dict, path, limit, parent, source):
    """
    Add term(s) to all import files in directory
    """
    directory = os.path.join("src", "ontology", "robot_inputs")
    for filename in os.listdir(directory):
        secondary_path = os.path.join(directory, filename)
        if os.path.isfile(secondary_path) and secondary_path != path:
            print(f"Universalizing to {filename}")
            secondary_imports = TSV2dict(secondary_path)
            if action == "import":
                do_import(input_dict, secondary_imports, limit, parent, source)
            if action == "ignore":
                do_ignore(input_dict, secondary_imports)
            if action == "remove":
                do_remove(input_dict, secondary_imports)
            dict2TSV(secondary_imports, secondary_path)


def update_import_source_tsv(path, ontology, iri):
    """
    Specify an IRI of a file to be used as the import source for an ontology
    """
    if os.path.isfile(path):
        import_source_dict = TSV2dict(path)
    else:
        import_source_dict = {}
    import_source_dict[ontology] = {
        "ontology": ontology,
        "IRI": iri
    }
    dict2TSV(import_source_dict, path)
    print(f"Set source for {ontology} as {iri}")


def remove_import_source(path, ontology):
    """
    Remove a line in the import source file
    """
    if not os.path.isfile(path):
        print(f"Didn't find {path}")
        quit()
    import_source_dict = TSV2dict(path)
    if ontology in import_source_dict.keys():
        del import_source_dict[ontology]
        dict2TSV(import_source_dict, path)
        print(f"Removed source for {ontology}")
    else:
        print(f"No source for {ontology} found in file")


def get_import_source_file(path, ontology):
    """
    Download the import source file for an ontology
    """
    import_source_dict = TSV2dict(path)
    if ontology not in import_source_dict.keys():
        iri = f"http://purl.obolibrary.org/obo/{ontology.lower()}.owl"
    else:
        iri = import_source_dict[ontology]["IRI"]
    file_destination = os.path.join("build", f"{ontology}_import_source.owl")
    run([
        "curl",
        "-sL",
        iri,
        "-o",
        file_destination
    ])
    print(f"Downloaded {ontology} import source file")


def check_input_file(ontology):
    """
    Check that labels in input file are up to date & replace as needed
    NOTE: This is still buggy.
    """
    input_path = os.path.join("src",
                              "ontology",
                              "robot_inputs",
                              f"{ontology}_input.tsv")
    input_dict = TSV2dict(input_path)
    source_file = os.path.join("build", f"{ontology}_import_source.owl")
    for id, rowdict in input_dict.items():
        if id == "ID":
            continue
        try:
            _, label, _ = get_term_info(id, source_file, listmode=True)
        except TypeError:
            source = id.split(":")
            source = source[0]
            alt_source = os.path.join("build", f"{source}_import_source.owl")
            if not os.path.isfile(alt_source):
                continue
            try:
                print(f"Checking {source} import...")
                _, label, _ = get_term_info(id, alt_source, listmode=True)
            except TypeError:
                continue
        if rowdict["label"] != label:
            rowdict["label"] = label
    dict2TSV(input_dict, input_path)


def main():
    """
    Validate paths and take specified action(s)
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("action",
                        choices=[
                            "import", "ignore", "remove", "split",
                            "change-source", "get-source", "remove-source",
                            "check-labels"
                                ],
                        help="What to do, e.g., add, ignore, or remove a term")
    parser.add_argument("ontology",
                        help="Which ontology import to edit, e.g., VO or OGMS")
    parser.add_argument("term",
                        nargs="?",
                        default=False,
                        help="An ontology CURIE/IRI/label, or a TSV or TXT")
    parser.add_argument("--iri", "-i", default=None,
                        help="An IRI to use as that ontology's source file")
    parser.add_argument("--limit", "-l", action="store_true",
                        help="Sets term as an upper limit to the hierarchy")
    parser.add_argument("--parent", "-p", default=False,
                        help="Sets intended parent for term, e.g., 'organ'")
    parser.add_argument("--reload", "-r", action="store_true",
                        help="Gets the new file after source IRI is changed")
    parser.add_argument("--universal", "-u", action="store_true",
                        help="Includes term in all input files")
    args = parser.parse_args()

    import_sources = os.path.join("src", "ontology", "import_sources.tsv")
    if args.action == "change-source":
        if not args.iri:
            print("Use --iri or -i to specify an IRI to set as the source.")
            quit()
        update_import_source_tsv(import_sources, args.ontology, args.iri)
        quit()
    if args.action == "remove-source":
        remove_import_source(import_sources, args.ontology)
        quit()
    if args.action == "get-source" or args.reload:
        get_import_source_file(import_sources, args.ontology)
        quit()
    if args.action == "check-labels":
        check_input_file(args.ontology)
        quit()

    path = os.path.join("src",
                        "ontology",
                        "robot_inputs",
                        f"{args.ontology}_input.tsv")
    import_file_check(path)
    imports = TSV2dict(path)
    if args.action == "split":
        split(args.ontology, imports)
        quit()
    if not args.term:
        print("This action needs a term or terms to act on.")
        print("Use a text file, IRI, CURIE, or label as the third argument.")
        quit()
    source = os.path.join("build", f"{args.ontology}_import_source.owl")
    input_dict = parse_term_input(args.term, args.ontology, source)
    if args.action == "import":
        do_import(input_dict, imports, args.limit, args.parent, source)
    if args.action == "ignore":
        do_ignore(input_dict, imports)
    if args.action == "remove":
        do_remove(input_dict, imports)
    dict2TSV(imports, path)
    if args.universal:
        universalize(args.action, input_dict, path,
                     args.limit, args.parent, source)


if __name__ == "__main__":
    main()
