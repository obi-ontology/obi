import sqlite3

from argparse import ArgumentParser
from cmi_pb_script.load import configure_and_load_db, grammar, read_config_files
from cmi_pb_script.cmi_pb_grammar import TreeToDict
from lark import Lark


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("table")
    parser.add_argument("db")
    args = parser.parse_args()

    config = read_config_files(args.table, Lark(grammar, parser="lalr", transformer=TreeToDict()))
    with sqlite3.connect(args.db) as conn:
        config["db"] = conn
        # config["db"].execute("PRAGMA foreign_keys = ON")
        configure_and_load_db(config)
