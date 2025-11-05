import csv


def TSV2dict(path):
    """
    Make a dict from a ROBOT template
    """
    header_row = None
    with open(path, "r", encoding="UTF-8") as infile:
        reader = csv.DictReader(infile, delimiter="\t")
        output = {}
        for row in reader:
            if not header_row:
                header_row = list(row.keys())
            if "ontology" in row.keys():
                id = row["ontology"].strip()
            else:
                id = row["ontology ID"].strip()
            if id == "":
                continue
            if id == "ID":
                for i in row:
                    output["robot"] = row
            else:
                for i in row:
                    output[id] = row
        return output


def dict2TSV(xdict, path):
    """
    Make a ROBOT template from a dict input
    """
    rows = [i for i in xdict.keys()]
    first = rows[0]
    fieldnames = [i for i in xdict[first].keys()]
    ids = []
    if "ontology ID" in fieldnames and "robot" not in xdict.keys():
        xdict["robot"] = {
            "ontology ID": "ID",
            "label": "",
            "action": "",
            "logical type": "CLASS_TYPE",
            "parent class": "C %"
        }
    for key in xdict.keys():
        if key != "robot":
            ids.append(key)
    sorted_ids = sorted(ids)
    with open(path, "w", newline="\n", encoding='utf-8') as tsv:
        writer = csv.DictWriter(tsv, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        if "robot" in xdict.keys():
            writer.writerow(xdict["robot"])
        for id in sorted_ids:
            writer.writerow(xdict[id])


def read_to_list(txt):
    """
    Make a list of lines in a text file with newline characters removed
    """
    output = []
    with open(txt, "r") as file:
        lines = file.readlines()
        for line in lines:
            output.append(line.strip())
    return output


def get_used_terms(target_term_file):
    assays = TSV2dict("src/ontology/templates/assays.tsv")
    ids = TSV2dict("obi_termlist.tsv")
    target_terms = read_to_list(target_term_file)
    annotations = [
        "BFO:0000179",
        "BFO:0000180",
        "IAO:0000111",
        "IAO:0000112",
        "IAO:0000114",
        "IAO:0000115",
        "IAO:0000117",
        "IAO:0000118",
        "IAO:0000119",
        "IAO:0000232",
        "IAO:0000233",
        "IAO:0000234",
        "IAO:0000412",
        "IAO:0000600",
        "IAO:0000601",
        "IAO:0000602",
        "IAO:0010000",
        "OBI:0001847",
        "OBI:9991118",
        "RO:0001900"
    ]
    cols = [
       "parent class",
       "material processing technique",
       "detection technique",
       "evaluant",
       "measurand",
       "analyte",
       "device",
       "reagent",
       "molecular label",
       "input",
       "output",
       "target entity",
       "target context",
       "objective"
    ]
    used_terms = set()
    for id, rowdict in assays.items():
        if id in target_terms:
            for key, val in rowdict.items():
                if key in cols and val != "":
                    used_terms.add(val)
    used_term_ids = []
    for term in used_terms:
        for id, rowdict in ids.items():
            if term == rowdict["LABEL"]:
                used_term_ids.append(id)
    for i in target_terms:
        used_term_ids.append(i)
    for i in annotations:
        used_term_ids.append(i)
    used_term_ids = sorted(used_term_ids)
    used_term_ids = [f"{item}\n" for item in used_term_ids]
    with open("relevant_ids.txt", "w") as file:
        file.writelines(used_term_ids)
        file.close()


if __name__ == "__main__":
    target_term_file = "src/ontology/templates/hcc_assay_list.txt"
    get_used_terms(target_term_file)
