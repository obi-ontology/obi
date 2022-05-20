#!/usr/bin/env python3
import os

from nanobot import run


if __name__ == '__main__':
    os.chdir("../..")
    run(
        "build/obi-tables.db",
        "src/table.tsv",
        base_ontology="obi",
        cgi_path="/OBI/branches/demo-site/views/src/scripts/run.py",
        default_params={"view": "tree"},
        default_table="obi",
        hide_index=True,
        import_table="import",
        max_children=100,
        title="OBI",
        tree_predicates=[
            "rdfs:label",
            "IAO:0000111",
            "IAO:0000114",
            "IAO:0000118",
            "IAO:0000115",
            "IAO:0000119",
            "IAO:0000112",
            "IAO:0000117",
            "IAO:0000116",
            "IAO:0000232",
            "IAO:0000234",
            "IAO:0000233",
            "rdfs:subClassOf",
            "*"
        ]
    )
