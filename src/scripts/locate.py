#!/usr/bin/env python3
#
# Locate terms by ID or label.

import csv
import os
import re
import sqlite3
import sys

from argparse import ArgumentParser

OBI_DB = "build/obi_merged.db"
TEMPLATES_DIR = "src/ontology/templates"
IMPORTS_DIR = "src/ontology/OntoFox_inputs"


def locate_term(cur, term_id):
    for f in os.listdir(TEMPLATES_DIR):
        if not f.endswith(".tsv"):
            continue
        fname = os.path.join(TEMPLATES_DIR, f)
        try:
            with open(fname, "r") as fr:
                reader = csv.DictReader(fr, delimiter="\t")
                i = 1
                for row in reader:
                    i += 1
                    if term_id == row.get("Ontology ID"):
                        return fname + ":" + str(i)
        except Exception as e:
            raise Exception(f"Failed to read {fname}", e)
    for f in os.listdir(IMPORTS_DIR):
        if not f.endswith(".txt"):
            continue
        fname = os.path.join(IMPORTS_DIR, f)
        term_iri = "http://purl.obolibrary.org/obo/" + term_id.replace(":", "_")
        i = 0
        try:
            with open(fname, "r") as fr:
                for line in fr.readlines():
                    i += 1
                    if not line:
                        continue
                    if line.split(" ")[0].strip() == term_iri:
                        return fname + ":" + str(i)
        except Exception as e:
            raise Exception(f"Failed to read {fname}", e)
    cur.execute("SELECT * FROM statements WHERE stanza = ?", (term_id,))
    res = cur.fetchone()
    if res:
        fname = "src/ontology/obi-edit.owl"
        term_iri = "http://purl.obolibrary.org/obo/" + term_id.replace(":", "_")
        try:
            with open(fname, "r") as fr:
                for line in fr.readlines():
                    i += 1
                    if not line:
                        continue
                    if "rdf:about=" in line and term_iri in line:
                        return fname + ":" + str(i)
        except Exception as e:
            raise Exception(f"Failed to read {fname}", e)
    return None


def main():
    parser = ArgumentParser()
    parser.add_argument("terms", help="One or more space-separated IDs or labels", nargs="+")
    args = parser.parse_args()

    if not os.path.exists(OBI_DB):
        print("ERROR: database does not exist! Run 'make build/obi_merged.db' and try again.")
        sys.exit(1)

    locs = []
    with sqlite3.connect(OBI_DB) as conn:
        cur = conn.cursor()
        for term in args.terms:
            # Check if term is a not a CURIE, we need to find the ID
            if not re.match(r"^[A-Z]+:[0-9]+$", term):
                cur.execute(
                    "SELECT stanza FROM statements WHERE predicate = 'rdfs:label' AND value = ?",
                    (term,)
                )
                res = cur.fetchone()
                if not res:
                    locs.append([term, "NOT FOUND"])
                    continue
                term_id = res[0]
            else:
                term_id = term
            loc = locate_term(cur, term_id)
            if loc:
                locs.append([term, loc])
            else:
                locs.append([term, "NOT FOUND"])

    for term_loc in locs:
        print(f"{term_loc[0]}\t{term_loc[1]}")


if __name__ == '__main__':
    main()
