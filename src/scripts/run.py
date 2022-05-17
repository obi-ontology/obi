#!/usr/bin/env python3
import os

from nanobot import run


if __name__ == '__main__':
    #os.chdir("../..")
    run(
        "build/obi-tables.db",
        "src/table.tsv",
        base_ontology="obi",
        default_params={"view": "tree"},
        default_table="obi",
        # cgi_path="/OBI/branches/demo-site/views/src/scripts/run.py",
        # log_file="obi.log",
        hide_index=True,
        max_children=100,
        title="OBI",
    )
