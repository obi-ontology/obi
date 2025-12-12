import csv
import re
import subprocess

OBO = 'http://purl.obolibrary.org/obo/'

### Utilities

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
    return read_term_table('build/obi-terms.tsv')


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
            if id == '' or label == '':
                continue
            if id.lower() in ['id', 'ontology id']:
                continue
            if label.lower() == 'label':
                continue
            terms[label] = id
    return terms

