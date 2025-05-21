"""
Manage files to be used as inputs in the ROBOT import workflow.

This script performs two basic functions: editing the main ROBOT input file
(src/ontology/robot_inputs/*_inputs.tsv) and splitting that file into the
three build files that are used directly in the ROBOT import workflow. The
splitting function is called in the Makefile.

The script can take the following actions on the ROBOT input file:
    * ADD a term to the input file to be imported
    * BLOCK a term from being imported
    * DROP references to a term in the input file
    * Set a PARENT for a term to be imported

The script will not allow addition of terms that are already in the import
file or terms that are deprecated. It also will not allow the user to set a
parent for a term that is already a hierarchical parent of that term in the
source ontology. It will ask for confirmation when overriding a block on
a term by adding, dropping, or setting a parent for that term.
"""


import argparse
import csv
import os
import re
from oaklib import get_adapter
from oaklib.datamodels.search import SearchProperty, SearchConfiguration


def TSV2dict(path):
    """
    Make a dict from a ROBOT template with ontology IDs as dict keys
    """
    header_row = None
    with open(path, "r", encoding="UTF-8") as infile:
        reader = csv.DictReader(infile, delimiter="\t")
        output = {}
        for row in reader:
            if not header_row:
                header_row = list(row.keys())
            id = row["ontology ID"].strip()
            if id == "":
                continue
            if id == "ID":
                for i in row:
                    output["robot"] = row
            else:
                for i in row:
                    output[id] = row
        return output


def dict2TSV(xdict, path):
    """
    Make a ROBOT template from a dict input with ontology IDs as dict keys
    """
    rows = [i for i in xdict.keys()]
    first = rows[0]
    fieldnames = [i for i in xdict[first].keys()]
    ids = []
    if "robot" not in xdict.keys():
        xdict["robot"] = {
            "ontology ID": "ID",
            "label": "",
            "action": "",
            "logical type": "CLASS_TYPE",
            "parent class": "C %"
        }
    for key in xdict.keys():
        if key != "robot":
            ids.append(key)
    sorted_ids = sorted(ids)
    with open(path, "w", newline="\n", encoding='utf-8') as tsv:
        writer = csv.DictWriter(tsv, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerow(xdict["robot"])
        for id in sorted_ids:
            writer.writerow(xdict[id])


def file_check(path):
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


def lookup_curie_from_label(label, ontology):
    """
    Find the CURIE of a term based on its label
    """
    try:
        adapter = get_adapter(f"sqlite:obo:{ontology.lower()}")
        config = SearchConfiguration(properties=[SearchProperty.ALIAS])
        curies = [id for id in adapter.basic_search(label, config=config)]
        curie = curies[0]  # This may not be the right way.
    except IndexError:
        print(f"Didn't find a CURIE for {label} in {ontology}.")
        curie = None
    return curie


def make_curie_dict(curie, ontology):
    """
    Make a dict of a term's CURIE, label, and OWL type
    """
    adapter = get_adapter(f"sqlite:obo:{ontology.lower()}")
    label = adapter.label(curie)
    owl_type = adapter.owl_type(curie)
    term_info = {
        "curie": curie,
        "label": label,
        "owl_type": owl_type
    }
    return term_info


def obsolescence_check(label):
    if "obsolete" in label.lower() or "deprecated" in label.lower():
        print(f"Term '{label}' is deprecated and will not be imported")
        obsolete = True
    else:
        obsolete = False
    return obsolete


def parse_term_input(string, ontology):
    """
    Handle term input that may be a CURIE, IRI, label, or path
    """
    error_message = "Try again with a text file, IRI, CURIE, or label."
    if os.path.isfile(string):
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
            term_curie = convert(term, "curie")
            curie_dict = make_curie_dict(term_curie, ontology)
            if not obsolescence_check(curie_dict["label"]):
                input_dict[term_curie] = curie_dict
        elif curie:
            curie_dict = make_curie_dict(term, ontology)
            if not obsolescence_check(curie_dict["label"]):
                input_dict[term] = curie_dict
        else:
            try:
                label_curie = lookup_curie_from_label(term, ontology)
                if label_curie:
                    curie_dict = make_curie_dict(label_curie, ontology)
                    if not obsolescence_check(curie_dict["label"]):
                        input_dict[label_curie] = curie_dict
                else:
                    raise ValueError("Couldn't find a term with this label")
            except ValueError:
                print(f"Label '{term}' wasn't found in {ontology}.")
                print(error_message)
                quit()
    return input_dict


def lookup_label(id):
    """
    Identify the label of a term based on its CURIE
    """
    curie = re.search(r"([a-zA-Z]+):(\d+)", id)
    output = id
    if curie:
        curie_base = curie.group(1)
        adapter = get_adapter(f"sqlite:obo:{curie_base.lower()}")
        label = adapter.label(id)
        output = label
        if type(label) != str and curie_base == "bfo":
            adapter = get_adapter("sqlite:obo:ro")
            label = adapter.label(id)
            if type(label) != str:
                output = ""
            else:
                output = label
        if "obsolete" in label.lower() or "deprecated" in label.lower():
            print(f"{id} '{label}' is deprecated and will not be included in this import")
            output = "deprecated"
    return output


def lookup_parents(id, mode):
    """
    Identify superclasses of a term based on its CURIE
    """
    curie = re.search(r"([a-zA-Z]+):(\d+)", id)
    parents = set()
    if curie:
        curie_base = curie.group(1)
        curie_base = curie_base.lower()
        adapter = get_adapter(f"sqlite:obo:{curie_base.lower()}")
        parent_list = adapter.hierarchical_parents(id)
        if mode == "soft":
            parents = parent_list
        elif mode == "hard":
            while len(parent_list) != 0:
                storage = set()
                for i in parent_list:
                    parents.add(i)
                    storage.add(i)
                parent_list = set()
                for i in storage:
                    upper_parents = adapter.hierarchical_parents(i)
                    for i in upper_parents:
                        parent_list.add(i)
    return parents


def do_import(term_dict, imports, limit, parent):
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
                    imports
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


def do_parent(term_info, parent, imports):
    """
    Assert a parent class for a term to be imported
    """
    confirmation_text = ""
    term = term_info["curie"]
    label = term_info["label"]
    act = True
    parents = lookup_parents(term, "hard")
    parent_labels = []
    for parent_id in parents:
        parent_label = lookup_label(parent_id)
        parent_labels.append(parent_label)
    if parent in parent_labels:
        print(f"{term} '{label}' is already a subclass of '{parent}' in the ontology")
        act = False
    if act:
        imports[term] = {
            "ontology ID": term,
            "label": label,
            "action": "parent",
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
        elif row["action"] == "ignore":
            ignore.append(f"{id} # {label}")
        elif row["action"] == "parent":
            imports.append(f"{id} # {label}")
            parent[id] = row
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


def main():
    """
    Validate paths and take specified action(s)
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("action",
                        choices=["import", "ignore", "remove", "split"],
                        help="What to do, e.g., add, ignore, or remove a term")
    parser.add_argument("ontology",
                        help="Which ontology import to edit, e.g., VO or OGMS")
    parser.add_argument("term",
                        nargs="?",
                        default=False,
                        help="An ontology CURIE/IRI/label, or a TSV or TXT")
    parser.add_argument("--limit", "-l", action="store_true",
                        help="Sets term as an upper limit to the hierarchy")
    parser.add_argument("--parent", "-p", default=False,
                        help="Sets intended parent for term, e.g., 'organ'")
    args = parser.parse_args()
    path = os.path.join("src",
                        "ontology",
                        "robot_inputs",
                        f"{args.ontology}_input.tsv")
    file_check(path)
    imports = TSV2dict(path)
    if args.action == "split":
        split(args.ontology, imports)
        quit()
    if not args.term:
        print("This action needs a term or terms to act on.")
        print("Use a text file, IRI, CURIE, or label as the third argument.")
        quit()
    input_dict = parse_term_input(args.term, args.ontology)
    if args.action == "import":
        do_import(input_dict, imports, args.limit, args.parent)
    if args.action == "ignore":
        do_ignore(input_dict, imports)
    if args.action == "remove":
        do_remove(input_dict, imports)
    dict2TSV(imports, path)


if __name__ == "__main__":
    main()
