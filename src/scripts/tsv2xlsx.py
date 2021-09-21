#!/usr/bin/env python3

import argparse
import csv
import os

from openpyxl import Workbook

parser = argparse.ArgumentParser(description="Merge TSV files into Excel")
parser.add_argument("output", type=str, help="Excel file to create")
parser.add_argument("inputs", type=str, nargs="+", help="TSV files to include")
args = parser.parse_args()

wb = Workbook()
wb.remove(wb.active)

for path in args.inputs:
    title, extension = os.path.splitext(os.path.basename(path))
    ws = wb.create_sheet(title)
    with open(path, "r") as tsvin:
        tsv = csv.reader(tsvin, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar='"')
        for row in tsv:
            ws.append(row[:])

wb.save(args.output)
