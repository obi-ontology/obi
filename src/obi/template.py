import csv
import os

import obi.util as util

from obi.imports import import_term


class Template:
    '''
    A ROBOT template
    '''
    def __init__(self, path=None):
        self.columns = []
        self.config = []
        self.rows = []

        if path:
            if os.path.isfile(path):
                self.path = path
            else:
                path = Template.find(path)
                if path:
                    self.path = path
        if path:
            self.load(path)

    @staticmethod
    def list():
        '''
        List the template files
        '''
        dir = os.path.join('src', 'ontology', 'templates')
        filenames = os.listdir(dir)
        filenames.sort()
        results = []
        for filename in filenames:
            if filename.endswith('.tsv'):
                path = os.path.join(dir, filename)
                if os.path.isfile(path):
                    results.append(path)
        return results

    @staticmethod
    def find(template_id):
        '''
        Given an ontology identifier,
        return the path to its template file,
        or None
        '''
        for path in Template.list():
            filename = os.path.basename(path)
            filename, ext = os.path.splitext(filename)
            if filename.lower() == template_id:
                return path

    def load(self, path):
        '''
        Load a template from a path
        '''
        with open(path) as f:
            self.rows = list(csv.DictReader(f, delimiter='\t'))
            self.config = self.rows.pop(0)
            self.columns = list(self.config.keys())

    def logical_columns(self):
        '''
        Return a list of the logical columns of this template
        '''
        logical_columns = []
        for key, value in self.config.items():
            if value.startswith('C '):
                logical_columns.append(key)
        return logical_columns

    def references(self):
        '''
        Return a set of the labels used in the logical columns,
        not include terms defined in this template
        '''
        logical_columns = self.logical_columns()
        terms = set()
        labels = {}
        for row in self.rows:
            id = row['ontology ID']
            label = row['label']
            labels[label] = id
            for column in logical_columns:
                term = row[column].strip()
                parts = [p.strip() for p in term.split('|')]
                for term in parts:
                    if term.startswith('('):
                        for term in util.split_expression(term):
                            terms.add(term)
                    else:
                        terms.add(term.strip('\'\"').strip())
        terms.remove('')
        return terms - set(labels.keys())

    def missing(self, labels):
        '''
        Return a set of references from this template
        that can't be found in the given set of labels
        '''
        return self.references() - set(labels)

    def match(self, labels, new_terms):
        '''
        Given a set of labels for currently define terms,
        and a dict from label to ID for new terms we can import,
        return a dict of missing terms found in new_terms,
        and a set of terms that are still missing
        '''
        missing = set()
        found = {}
        for term in self.missing(labels):
            if term in new_terms:
                id = new_terms[term]
                found[term] = id
                # import_term(new_terms[term], term)
            else:
                missing.add(term)
        return found, missing

    def import_found(self, labels, new_terms):
        '''
        Given a set of labels for currently define terms,
        and a dict from label to ID for new terms we can import,
        for all terms that can't be found in the current labels,
        try to find and import a new term
        '''
        found, missing = self.match(labels, new_terms)
        for label, id in found.items():
            import_term(id, label)
        return found, missing
