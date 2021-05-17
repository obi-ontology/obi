#!/usr/bin/env python3
#
# Relabel a term by ID.

import csv
import os
import re
import sqlite3
import subprocess
import sys

from argparse import ArgumentParser
from locate import get_term_id, locate_term

EDIT_DB = "build/obi-edit.db"
MERGED_DB = "build/obi_merged.db"
OBI_EDIT = "src/ontology/obi-edit.owl"
TEMPLATES_DIR = "src/ontology/templates"
IMPORTS_DIR = "src/ontology/OntoFox_inputs"


def get_ttl(cur):
    """Get the statements table as lines of Turtle (the lines are returned as a list).
    Copied from ontodev-gizmos 'extract' module."""
    # Get ttl lines
    cur.execute(
        """WITH literal(value, escaped) AS (
              SELECT DISTINCT
                value,
                replace(replace(replace(value, '\\', '\\\\'), '"', '\\"'), '
            ', '\\n') AS escaped
              FROM statements
            )
            SELECT
              '@prefix ' || prefix || ': <' || base || '> .'
            FROM prefix
            UNION ALL
            SELECT DISTINCT
               subject
            || ' '
            || predicate
            || ' '
            || coalesce(
                 object,
                 '"' || escaped || '"^^' || datatype,
                 '"' || escaped || '"@' || language,
                 '"' || escaped || '"'
               )
            || ' .'
            FROM statements LEFT JOIN literal ON statements.value = literal.value;"""
    )
    lines = []
    for row in cur.fetchall():
        line = row[0]
        if not line:
            continue
        # Replace newlines
        line = line.replace("\n", "\\n")
        lines.append(line)

    return lines


def replace_usages(old_label, new_label):
    for f in os.listdir(TEMPLATES_DIR):
        if not f.endswith(".tsv"):
            continue
        path = os.path.join(TEMPLATES_DIR, f)
        rows = []
        has_change = False
        with open(path, "r") as fr:
            reader = csv.reader(fr, delimiter="\t")
            for row in reader:
                itms = []
                for itm in row:
                    # Some columns have splits, make sure we check all items
                    subitms = []
                    for subitm in itm.split("|"):
                        if subitm.strip() == old_label:
                            has_change = True
                            subitms.append(new_label)
                        else:
                            subitms.append(subitm)
                    itms.append("|".join(subitms))
                rows.append(itms)
        if has_change:
            with open(path, "w") as fw:
                writer = csv.writer(fw, delimiter="\t", lineterminator="\n")
                writer.writerows(rows)


def update_obi(cur, term_id, new_label):
    # Retrieve the old label
    cur.execute(
        "SELECT value FROM statements WHERE stanza = ? AND predicate = 'rdfs:label'", (term_id,)
    )
    res = cur.fetchone()
    if not res:
        print("ERROR: Unable to find label for " + term_id)
        sys.exit(1)
    old_label = res[0]

    # Update the database with new label
    cur.execute(
        "UPDATE statements SET value = ? WHERE stanza = ? AND predicate = 'rdfs:label'",
        (new_label, term_id),
    )

    # Write to TTL in build directory
    ttl = get_ttl(cur)

    # Fix issues with ontology IRIs
    ttl.insert(0, "@prefix : <http://purl.obolibrary.org/obo/obi/dev/obi-edit.owl#> .")
    ttl = "\n".join(ttl).replace(
        "obo:obi/dev/obi-edit.owl", "<http://purl.obolibrary.org/obo/obi/dev/obi-edit.owl>"
    )
    ttl = re.sub(
        r"owl:imports obo:(.+)\.owl", "owl:imports <http://purl.obolibrary.org/obo/\g<1>.owl>", ttl
    )
    with open("build/obi-edit.ttl", "w") as f:
        f.write(ttl)

    # Convert the ttl to RDF/XML
    subprocess.check_output(
        "java -jar build/robot.jar convert --input build/obi-edit.ttl --output " + OBI_EDIT,
        shell=True,
    )
    return old_label


def update_template(loc, term_id, new_label):
    rows = []
    with open(loc, "r") as f:
        reader = csv.DictReader(f, delimiter="\t")
        headers = reader.fieldnames
        # Some templates have label capitalized
        if "Label" in headers:
            label_col = "Label"
        else:
            label_col = "label"
        for row in reader:
            if row["Ontology ID"] == term_id:
                old_label = row.get(label_col)
                row[label_col] = new_label
            rows.append(row)
    with open(loc, "w") as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return old_label


def main():
    parser = ArgumentParser()
    parser.add_argument("term")
    parser.add_argument("new_label")
    args = parser.parse_args()

    term = args.term
    new_label = args.new_label

    # Use OBI merged to locate term
    with sqlite3.connect(MERGED_DB) as conn:
        cur = conn.cursor()

        # Check if term is a not a CURIE, we need to find the ID
        term_id = get_term_id(cur, term)
        if not term_id:
            print(f"ERROR: '{term}' does not exist in OBI")
            sys.exit(1)

        # First figure out where the term lives
        loc = locate_term(cur, term_id, include_line=False)
        if not loc:
            print(f"ERROR: Unable to locate {term_id}")
            sys.exit(1)

    if loc == OBI_EDIT:
        # Switch to OBI edit to make updates
        with sqlite3.connect(EDIT_DB) as conn:
            cur = conn.cursor()
            old_label = update_obi(cur, term_id, new_label)
    elif loc.startswith(TEMPLATES_DIR):
        old_label = update_template(loc, term_id, new_label)
    else:
        # Term is in an import, we cannot update the label
        print("ERROR: Unable to update the label of a non-OBI term at this time.")
        sys.exit(1)

    # Then go through all the templates and find usages
    replace_usages(old_label, new_label)


if __name__ == "__main__":
    main()
