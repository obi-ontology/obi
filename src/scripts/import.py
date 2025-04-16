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


def read_to_list(txt):
    output = []
    with open(txt, "r") as file:
        lines = file.readlines()
        for line in lines:
            output.append(line.strip())
    return output


def write_to_txt(items, txt):
    line_broken_items = [f"{item}\n" for item in items]
    with open(txt, "w") as file:
        file.writelines(line_broken_items)
        file.close()


def convert(string, format):
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
    curie = re.search(r"([a-zA-Z]+):(\d+)", id)
    output = id
    if curie:
        curie_base = curie.group(1)
        curie_base = curie_base.lower()
        adapter = get_adapter(f"sqlite:obo:{curie_base}")
        label = adapter.label(id)
        output = label
        if "obsolete" in label.lower() or "deprecated" in label.lower():
            print(f"WARN: {id} is deprecated and will not be included in this import")
            output = "deprecated"
    return output


def add(term, imports):
    term = convert(term, "curie")
    act = True
    if term in imports.keys():
        act = False
        if imports[term]["action"] != "block":
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
                "action": "input",
                "logical type": "",
                "parent class": ""
            }
            print(f"Added {term} to import")


def block(term, imports):
    term = convert(term, "curie")
    if term in imports.keys() and imports[term]["action"] == "block":
        print(f"{term} is already blocked out of this import")
    else:
        label = lookup_label(term)
        if label != "deprecated":
            imports[term] = {
                "ontology ID": term,
                "label": label,
                "action": "block",
                "logical type": "",
                "parent class": ""
            }
            print(f"Blocked {term} out of this import")


def drop(term, imports):
    term = convert(term, "curie")
    if term not in imports.keys():
        print(f"{term} is not in this import file")
    else:
        if imports[term]["action"] == "block":
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
    term = convert(term, "curie")
    act = True
    if term in imports.keys():
        if imports[term]["action"] == "block":
            act = False
            override = input(f"{term} is blocked out of this import. Do you want to import this term? (y/n)\n")
            if override.lower() == "y" or override.lower() == "yes":
                act = True
        elif imports[term]["action"] == "parent":
            if imports[term]["parent class"] == parent:
                act = False
                print(f"{term} is already imported as a subclass of {parent}")
    if act:
        label = lookup_label(term)
        if label != "deprecated":
            imports[term] = {
                "ontology ID": term,
                "label": label,
                "action": "parent",
                "logical type": "subclass",
                "parent class": parent
            }
            print(f"Added {term} to import as a subclass of {parent}")


def split(ontology, imports):
    inputs, blocklist, parent = [], [], {}
    inputs_path = os.path.join("build", f"{ontology}_input.txt")
    blocklist_path = os.path.join("build", f"{ontology}_blocklist.txt")
    parent_path = os.path.join("build", f"{ontology}_parent.tsv")
    parent["robot"] = imports["robot"]
    for id, row in imports.items():
        label = row["label"]
        if row["action"] == "input":
            inputs.append(f"{id} # {label}")
        elif row["action"] == "block":
            blocklist.append(f"{id} # {label}")
        elif row["action"] == "parent":
            inputs.append(f"{id} # {label}")
            parent[id] = row
    inputs = sorted(inputs)
    write_to_txt(inputs, inputs_path)
    blocklist = sorted(blocklist)
    write_to_txt(blocklist, blocklist_path)
    dict2TSV(parent, parent_path)
    print(f"Wrote {inputs_path}\nWrote {blocklist_path}\nWrote {parent_path}")


def main():
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
    args = parser.parse_args()
    path = os.path.join("src",
                        "ontology",
                        "robot_inputs",
                        f"{args.ontology}_input.tsv")
    if not os.path.exists(path):
        print(f"Didn't find {path}")
        quit()
    if args.action != "split" and not args.term and not args.termlist:
        print("Use --term or --termlist to indicate the term(s) to act on.")
        quit()
    imports = TSV2dict(path)
    terms = read_to_list(args.termlist) if args.termlist else [args.term,]
    if args.action == "add":
        for term in terms:
            add(term, imports)
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
