#!/usr/bin/env python3
#
# Sort template files by ID and save them as clean TSV with Unix line endings.

import csv, os


def sort_template(path):
    rows = []
    try:
        with open(path, "r") as tsv:
            rows = list(csv.reader(tsv, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar='"'))
    except Exception as e:
        print(f"Failed to read {path}")
        raise(e)
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
            if name.endswith('.tsv'):
                paths.append(os.path.join(root, name))

    for path in paths:
        sort_template(path)


if __name__ == "__main__":
    main()
