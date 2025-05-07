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
            "status": "",
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
                "status": "",
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


def lookup_label(id):
    """
    Identify the label of a term based on its CURIE
    """
    curie = re.search(r"([a-zA-Z]+):(\d+)", id)
    output = id
    if curie:
        curie_base = curie.group(1)
        curie_base = curie_base.lower()
        adapter = get_adapter(f"sqlite:obo:{curie_base}")
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
            print(f"WARN: {id} is deprecated and will not be included in this import")
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
        adapter = get_adapter(f"sqlite:obo:{curie_base}")
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


def add(term, imports, relation=False, upper=False):
    """
    Add a term to be imported
    """
    term = convert(term, "curie")
    act = True
    if term in imports.keys():
        act = False
        if imports[term]["status"] != "block":
            if relation and imports[term]["status"] != "relate":
                act = True
            elif upper and imports[term]["status"] != "upper":
                act = True
            else:
                print(f"{term} is already in this import file")
        else:
            override = input(f"{term} is blocked out of this import. Override? (y/n)\n")
            if override.lower() == "y" or override.lower() == "yes":
                act = True
    if act:
        label = lookup_label(term)
        if label != "deprecated":
            imports[term] = {
                "ontology ID": term,
                "label": label,
                "status": "input",
                "logical type": "",
                "parent class": ""
            }
            status_text = ""
            if relation:
                imports[term]["status"] = "relate"
                status_text = " as a relation"
            if upper:
                imports[term]["status"] = "upper"
                status_text = " as an upper-level term"
            print(f"Added {term} to import{status_text}")


def block(term, imports):
    """
    Block a term from being imported
    """
    term = convert(term, "curie")
    if term in imports.keys() and imports[term]["status"] == "block":
        print(f"{term} is already blocked out of this import")
    else:
        label = lookup_label(term)
        if label != "deprecated":
            imports[term] = {
                "ontology ID": term,
                "label": label,
                "status": "block",
                "logical type": "",
                "parent class": ""
            }
            print(f"Blocked {term} out of this import")


def drop(term, imports):
    """
    Remove references to a term in the import dict
    """
    term = convert(term, "curie")
    if term not in imports.keys():
        print(f"{term} is not in this import file")
    else:
        if imports[term]["status"] == "block":
            override = input(f"{term} is blocked out of this import. Drop the block? (y/n)\n")   
            if override.lower() == "y" or override.lower() == "yes":
                act = True
            else:
                act = False
                print(f"{term} was not dropped from this import file")
        else:
            act = True
        if act:
            del imports[term]
            print(f"Dropped {term} from this import file")


def parent(term, parent, imports):
    """
    Assert a parent class for a term to be imported
    """
    term = convert(term, "curie")
    act = True
    parents = lookup_parents(term, "hard")
    parent_labels = []
    for parent_id in parents:
        parent_label = lookup_label(parent_id)
        parent_labels.append(parent_label)
    if term in imports.keys():
        if imports[term]["status"] == "block":
            act = False
            override = input(f"{term} is blocked out of this import. Do you want to import this term? (y/n)\n")
            if override.lower() == "y" or override.lower() == "yes":
                act = True
        elif imports[term]["status"] == "parent":
            if imports[term]["parent class"] == parent:
                act = False
                print(f"{term} is already imported as a subclass of {parent}")
    if parent in parent_labels:
        print(f"{term} is already a subclass of '{parent}' in the ontology")
        act = False
    if act:
        label = lookup_label(term)
        if label != "deprecated":
            imports[term] = {
                "ontology ID": term,
                "label": label,
                "status": "parent",
                "logical type": "subclass",
                "parent class": parent
            }
            print(f"Added {term} to import as a subclass of {parent}")


def split(ontology, imports):
    """
    Split imports into build files needed by ROBOT import workflow
    """
    inputs, blocklist, parent, relation, upper = [], [], {}, [], []
    inputs_path = os.path.join("build", f"{ontology}_input.txt")
    blocklist_path = os.path.join("build", f"{ontology}_blocklist.txt")
    parent_path = os.path.join("build", f"{ontology}_parent.tsv")
    relation_path = os.path.join("build", f"{ontology}_relations.txt")
    upper_path = os.path.join("build", f"{ontology}_upper.txt")
    parent["robot"] = imports["robot"]
    for id, row in imports.items():
        label = row["label"]
        if row["status"] == "input":
            inputs.append(f"{id} # {label}")
        elif row["status"] == "block":
            blocklist.append(f"{id} # {label}")
        elif row["status"] == "parent":
            inputs.append(f"{id} # {label}")
            parent[id] = row
        elif row["status"] == "relate":
            relation.append(f"{id} # {label}")
        elif row["status"] == "upper":
            upper.append(f"{id} # {label}")
    for (xlist, xpath) in [
        (inputs, inputs_path),
        (blocklist, blocklist_path),
        (relation, relation_path),
        (upper, upper_path)
    ]:
        write_to_txt(sorted(xlist), xpath)
    dict2TSV(parent, parent_path)
    for i in inputs_path, blocklist_path, parent_path, relation_path, upper_path:
        print(f"Wrote {i}")


def main():
    """
    Validate paths and take specified action(s)
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", "-a", type=str, required=True,
                        choices=["add", "block", "drop", "parent", "split"],
                        help="Action to take for chosen term, e.g., add")
    parser.add_argument("--ontology", "-o", type=str, required=True,
                        help="Which ontology import to edit, e.g., Uberon")
    parser.add_argument("--term", "-t", type=str,
                        help="An ontology term ID, e.g., UBERON:0000465")
    parser.add_argument("--termlist", "-l", type=str,
                        help="A text file containing a list of ontology IDs")
    parser.add_argument("--parent", "-p", type=str,
                        help="Intended parent for term, e.g., 'organ'")
    parser.add_argument("--relation", "-r", type=str,
                        help="'--relation True' indicates term is a relation")
    parser.add_argument("--upper", "-u", type=str,
                        help="'--upper True' sets the term as an upper term")
    args = parser.parse_args()
    path = os.path.join("src",
                        "ontology",
                        "robot_inputs",
                        f"{args.ontology}_input.tsv")
    file_check(path)
    if args.action != "split" and not args.term and not args.termlist:
        print("Use --term or --termlist to indicate the term(s) to act on.")
        quit()
    imports = TSV2dict(path)
    terms = read_to_list(args.termlist) if args.termlist else [args.term,]
    if args.action == "add":
        for term in terms:
            add(term, imports, args.relation, args.upper)
            if args.parent:
                parent(term, args.parent, imports)
    if args.action == "block":
        for term in terms:
            block(term, imports)
    if args.action == "drop":
        for term in terms:
            drop(term, imports)
    if args.action == "parent":
        if not args.parent:
            print("No parent term specified. Use --parent or -p to set parent")
            quit()
        for term in terms:
            parent(term, args.parent, imports)
    if args.action == "split":
        split(args.ontology, imports)
    dict2TSV(imports, path)


if __name__ == "__main__":
    main()
