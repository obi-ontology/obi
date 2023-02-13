#!/usr/bin/env python3
#
# Sort template files by ID and save them as clean TSV with Unix line endings.

import csv, os


def sort_template(path):
    print(path)
    rows = []
    with open(path, "r") as tsv:
        reader = csv.reader(tsv, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar='"')

        # Get the index of the ID column
        headers = next(reader)
        rows.append(headers)
        id_idx = None
        if "ontology ID" in headers:
            id_idx = headers.index("ontology ID")

        # Get the ROBOT headers to search for SPLITs
        robot_headers = next(reader)
        rows.append(robot_headers)

        # Track IDs to check for duplicates
        ids = set()
        row_idx = 2
        for row in reader:
            row_idx += 1
            # Check for duplicate IDs
            if id_idx is not None:
                term_id = row[id_idx]
                if term_id in ids:
                    raise Exception(
                        f"Duplicate entry for {term_id} on row {row_idx} of {os.path.basename(path)}"
                    )
                ids.add(term_id)
            i = 0
            cells = []
            # For each cell, make sure SPLITs are not surrounded by whitespace
            for cell in row:
                try:
                    header = robot_headers[i]
                except:
                    # This is usually caused by extra trailing whitespace
                    if cell == "":
                        continue
                    else:
                        cells.append(cell)
                if "SPLIT=|" in header and "|" in cell:
                    # Strip whitespace around pipe
                    cells.append("|".join([x.strip() for x in cell.split("|")]))
                else:
                    cells.append(cell)
                i += 1
            rows.append(cells)

    headers = rows[0:2]
    terms = rows[2:]
    terms.sort(key=lambda x: x[0])
    with open(path, "w") as tsv:
        writer = csv.writer(
            tsv, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE, escapechar='"'
        )
        writer.writerows(headers)
        writer.writerows(terms)


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(base, "../ontology/")
    paths = []
    for root, dirs, files in os.walk(template_dir):
        for name in files:
            if name.endswith(".tsv"):
                paths.append(os.path.join(root, name))

    for path in paths:
        sort_template(path)


if __name__ == "__main__":
    main()
