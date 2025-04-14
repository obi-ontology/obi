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
    with open(path, "w", newline="\n", encoding='utf-8') as tsv:
        writer = csv.DictWriter(tsv, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for (id, row) in xdict.items():
            writer.writerow(row)


def get_paths(ontology):
    base_path = os.path.join("src", "ontology", "robot_inputs")
    inputs = os.path.join(base_path, f"{ontology}_input.txt")
    blocklist = os.path.join(base_path, f"{ontology}_block.txt")
    edit = os.path.join(base_path, f"{ontology}_edit.tsv")
    return inputs, blocklist, edit


def check_files(ontology):
    inputs, blocklist, edit = get_paths(ontology)
    exists = True
    for file in inputs, blocklist, edit:
        if not os.path.exists(file):
            print(f"Didn't find {file}")
            exists = False
    return exists


def id_to_purl(id):
    id = id.replace(":", "_")
    id = id.upper()
    purl = f"http://purl.obolibrary.org/obo/{id}"
    return purl


def lookup_label(id):
    curie = re.search(r"([a-zA-Z]+):(\d+)", id)
    output = id
    if curie:
        curie_base = curie.group(1)
        curie_base = curie_base.lower()
        adapter = get_adapter(f"sqlite:obo:{curie_base}")
        label = adapter.label(id)
        output = label
    return output


def add_label_comment(purl):
    comment = re.search(r"#\s*[\w\d\s]", purl)
    if not comment:
        iri = re.search(r"([a-zA-Z]+)_(\d+)", purl)
        if iri:
            curie = f"{iri.group(1)}:{iri.group(2)}"
            label = lookup_label(curie)
            purl = re.sub("\n", f" # {label}\n", purl)
    return purl


def read_purls(path):
    with open(path, "r") as text:
        purls = text.readlines()
        output = []
        for purl in purls:
            output.append(purl.strip())
    return output


def write_purls(purl_list, path):
    output_purls = []
    for purl in purl_list:
        line_broken_purl = f"{purl}\n"
        labeled_purl = add_label_comment(line_broken_purl)
        if purl != "":
            output_purls.append(labeled_purl)
    f = open(path, "w")
    f.writelines(output_purls)


def add_term_to_file(term, path):
    purls = read_purls(path)
    purl_to_add = id_to_purl(term)
    in_file = False
    for purl in purls:
        if purl_to_add in purl:
            in_file = True
            break
    if in_file:
        print(f"{term} is already in {path}")
    else:
        purls.append(purl_to_add)
        purls = sorted(purls)
        write_purls(purls, path)
        print(f"Added {term} to {path}")


def remove_term_from_file(term, path):
    if ".tsv" in path:
        template_dict = TSV2dict(path)
        if term not in template_dict.keys():
            print(f"Confirmed {term} is not in {path}")
        else:
            del template_dict[term]
            print(f"Removed {term} from {path}")
    elif ".txt" in path:
        purls = read_purls(path)
        purl_to_remove = id_to_purl(term)
        in_file = False
        output_purls = []
        for purl in purls:
            if purl_to_remove in purl:
                in_file = True
            else:
                output_purls.append(purl)
        if not in_file:
            print(f"Confirmed {term} is not in {path}")
        else:
            if len(output_purls) >= len(purls):
                print("STOPPED: Output contains more IRIs than input")
            else:
                write_purls(output_purls, path)
                print(f"Removed {term} from {path}")


def add(term, ontology):
    inputs, blocklist, edit = get_paths(ontology)
    add_term_to_file(term, inputs)
    remove_term_from_file(term, blocklist)


def block(term, ontology):
    inputs, blocklist, edit = get_paths(ontology)
    add_term_to_file(term, blocklist)
    remove_term_from_file(term, inputs)
    remove_term_from_file(term, edit)


def drop(term, ontology):
    inputs, blocklist, edit = get_paths(ontology)
    remove_term_from_file(term, inputs)
    remove_term_from_file(term, blocklist)
    remove_term_from_file(term, edit)


def parent(term, parent, ontology):
    inputs, blocklist, edit = get_paths(ontology)
    add_term_to_file(term, inputs)
    remove_term_from_file(term, blocklist)
    template_dict = TSV2dict(edit)
    parent_label = lookup_label(term)
    if term in template_dict.keys() and template_dict[term]["parent class"] == parent_label:
        print(f"{term} is already a subclass of '{parent}' in {edit}")
    else:
        template_dict[term] = {
            "ontology ID": term,
            "logical type": "subclass",
            "parent class": parent_label,
        }
        dict2TSV(template_dict, edit)
        print(f"Asserted {term} is a subclass of '{parent}'")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", "-a", type=str, required=True,
                        choices=["add", "block", "drop", "parent"],
                        help="Action to take for chosen term, e.g., add")
    parser.add_argument("--ontology", "-o", type=str, required=True,
                        help="Which ontology import to edit, e.g., Uberon")
    parser.add_argument("--term", "-t", type=str, required=True,
                        help="An ontology term ID, e.g., UBERON:0000465")
    parser.add_argument("--parent", "-p", type=str,
                        help="Intended parent for term, e.g., 'material entity'")
    args = parser.parse_args()
    if check_files(args.ontology):
        if args.action == "add":
            add(args.term, args.ontology)
            if args.parent:
                parent(args.term, args.parent, args.ontology)
        if args.action == "block":
            block(args.term, args.ontology)
        if args.action == "drop":
            drop(args.term, args.ontology)
        if args.action == "parent":
            parent(args.term, args.parent, args.ontology)


if __name__ == "__main__":
    main()
