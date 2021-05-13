#!/usr/bin/env python3

import argparse
import csv
import os

from openpyxl import load_workbook

parser = argparse.ArgumentParser(description="Read TSV from Excel")
parser.add_argument("input", type=str, help="Excel file to read")
parser.add_argument("sheet", type=str, help="Sheet name to read")
parser.add_argument("output", type=str, help="TSV file to output")
args = parser.parse_args()

wb = load_workbook(args.input)
ws = wb[args.sheet]

rows = []
for row in ws:
    values = []
    for cell in row:
        if cell.value is None:
            values.append("")
        else:
            values.append(cell.value)
    if row:
      rows.append(values)

with open(args.output, "w") as f:
  writer = csv.writer(f, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE, escapechar='"')
  writer.writerows(rows)
