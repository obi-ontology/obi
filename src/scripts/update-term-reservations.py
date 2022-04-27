import csv
import logging

from argparse import ArgumentParser, FileType


def main():
	parser = ArgumentParser()
	parser.add_argument("reservations", type=FileType("r"))
	parser.add_argument("obi_terms", type=FileType("r"))
	parser.add_argument("output", type=FileType("w"))
	args = parser.parse_args()

	obi_terms = {}
	reader = csv.reader(args.obi_terms, delimiter="\t")
	next(reader)
	for row in reader:
		obi_terms[row[0]] = row[1]

	out_rows = []
	reader = csv.DictReader(args.reservations, delimiter="\t")
	fnames = None
	for row in reader:
		if not fnames:
			fnames = row.keys()
		term_id = row["ID"]
		term_label = row["label"]
		if term_id in obi_terms:
			obi_label = obi_terms[term_id]
			if term_label != obi_label:
				logging.warning(f"Reservation table label ('{term_label}') for {term_id} does not match label in OBI ('{obi_label}')")
			row["merged"] = True
		else:
			row["merged"] = False
		out_rows.append(row)

	writer = csv.DictWriter(args.output, delimiter="\t", lineterminator="\n", fieldnames=fnames)
	writer.writeheader()
	writer.writerows(out_rows)


if __name__ == '__main__':
	main()
