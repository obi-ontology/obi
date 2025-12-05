import csv
import re
import subprocess

OBO = 'http://purl.obolibrary.org/obo/'

### Utilities


def is_ontology_name(string):
    '''
    Return None if an input string is an ID rather than an ontology name.
    '''
    if re.fullmatch(r'\w+', string):
        return string
    else:
        return None


def contract(iri):
    base, num = iri.replace(OBO, '').split('_', maxsplit=1)
    curie = f"{base}:{num}"
    return curie


def expand(curie):
    if re.match(r'\w+:\d+', curie):
        ontology_id, local_name = curie.split(':')
        return f'{OBO}{ontology_id}_{local_name}'
    return curie


def split_id(term_id):
    '''
    Given a string, return the pair of an ID and an optional label.
    '''
    term_id = term_id.strip()
    if ' ' in term_id:
        term_id, label = term_id.split(maxsplit=1)
        term_id = term_id.strip()
        label = label.strip()
        if label != '':
            return (term_id, label)
        else:
            return (term_id, None)
    return (term_id, None)


def split_expression(expression):
    '''
    Split a Manchester expression into term labels
    '''
    return re.findall(r"'([^']+)'", expression) # to only extract non-empty values


def get_ontology_id(term_id):
    '''
    Given source CURIE or IRI, return the ontology ID.
    '''
    if term_id.startswith(OBO):
        ns, _ = term_id.replace(OBO, '').split('_', maxsplit=1)
        return ns
    elif ':' in term_id:
        ns, _ = term_id.split(':', maxsplit=1)
        return ns
    else:
        print('Unknown', term_id)


def export_terms():
    '''
    Use ROBOT to export a list of terms to build/obi-terms.tsv.
    Not that this reads from obi.owl.
    '''
    path = 'build/obi-terms.tsv'
    subprocess.run([
        'java',
        '-jar',
        'build/robot.jar',
        'export',
        '--include',
        '"classes properties individuals"',
        '--input',
        'obi.owl',
        '--header',
        '"ID|LABEL"',
        '--export',
        path,
    ], check=True)


def get_labels():
    '''
    Get a dictionary from label to ID for all OBI terms
    '''
    export_terms()
    read_term_table('build/obi-terms.tsv')


def read_term_table(path):
    '''
    Try to read labels and IDs from a table
    returning a dict from label to ID
    '''
    terms = {}
    with open(path) as f:
        for row in csv.reader(f, delimiter='\t'):
            id = row[0].strip()
            label = row[1].strip()
            if id == '' or label != '':
                continue
            if id.lower() in ['id', 'ontology id']:
                continue
            if label.lower() == 'label':
                continue
            terms[label] = id
    return terms


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
