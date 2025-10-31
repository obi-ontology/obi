import io
import os
import unittest

from natsort import natsorted

from obi.util import expand


sections = {
    'ontology_iri': '[URI of the OWL(RDF/XML) output file]',
    'source_ontologies': '[Source ontology]',
    'lower': '[Low level source term URIs]',
    'upper': '[Top level source term URIs and target direct superclass URIs]',
    'settings': '[Source term retrieval setting]',
    'annotations': '[Source annotation URIs]',
}

class Term:
    '''
    A single ontology term, with IRI and optional label and parent term. 
    '''
    def __init__(self, iri, label=None, subClassOf=None):
        '''
        Create a term from an IRI. Allow for a "#" followed by a label.
        '''
        iri = iri.strip()
        iri = expand(iri)
        if '#' in iri:
            iri, label = iri.split('#', maxsplit=1)
            iri = iri.strip()
            label = label.strip()
        self.iri = iri
        self.label = label
        self.subClassOf = subClassOf
        self.upper = False

    def __str__(self):
        '''
        Render this term as an IRI with label as an optional comment.
        '''
        if self.label:
            return f'{self.iri} # {self.label}'
        else:
            return self.iri

    def __eq__(self, other):
        '''
        Compare terms by IRI alone.
        '''
        return other and self.iri == other.iri

    def __ne__(self, other):
        '''
        Compare terms by IRI alone.
        '''
        return not self.__eq__(other)

    def __hash__(self):
        '''
        Hash terms by IRI alone.
        '''
        return hash((self.iri))


class Ontofox:
    '''
    Ontofox configuration.
    See: https://ontofox.hegroup.org
    '''
    def __init__(self, path=None):
        self.path = None
        self.ontology_iri = ''
        self.sources = []
        self.terms = {}
        self.settings = []
        self.annotations = []

        if path:
            if os.path.isfile(path):
                self.path = path
            else:
                path = Ontofox.find(path)
                if path:
                    self.path = path
        if self.path:
            self.load(self.path)

    def read(self, buffer):
        '''
        Read an Ontofox configuration file into this class
        '''
        section = ''
        last_upper_iri = None
        for line in buffer.readlines():
            line = line.strip()
            if line == '':
                continue

            if line.startswith('['):
                found = False
                for s, header in sections.items():
                    if line == header:
                        section = s
                        found = True
                        break
                if not found:
                    raise Exception(f'Unhandled section: {line}')
                continue

            if section == 'ontology_iri':
                self.ontology_iri = line
            elif section == 'source_ontologies':
                self.sources.append(line)
            elif section == 'lower':
                term = Term(line)
                if term.iri in self.terms:
                    raise Exception(f'Duplicate lower term: {line}')
                self.add(Term(line))
            elif section == 'upper':
                if line.startswith('subClassOf'):
                    parent = Term(line.replace('subClassOf', ''))
                    self.terms[last_upper_iri].subClassOf = parent
                else:
                    term = Term(line)
                    term.upper = True
                    self.add(term)
                    last_upper_iri = term.iri
            elif section == 'settings':
                self.settings.append(line)
            elif section == 'annotations':
                self.annotations.append(line)
            else:
                continue

    def load(self, path):
        '''
        Load an Ontofox configuration file
        '''
        with open(path) as f:
            self.read(f)

    def add(self, term):
        '''
        Add a term to this configuration
        '''
        self.terms[term.iri] = term

    def remove(self, term):
        '''
        Remove a term from this configuration
        '''
        del self.terms[term.iri]
        for i, j in self.terms.items():
            if j.subClassOf and j.subClassOf == term:
                j.subClassOf = None

    def sort(self):
        '''
        Sort terms by ID
        '''
        terms = {}
        for key in natsorted(self.terms.keys()):
            terms[key] = self.terms[key]
        self.terms = terms

    def write(self, buffer):
        '''
        Write this configuration to a buffer
        '''
        print('[URI of the OWL(RDF/XML) output file]', file=buffer)
        if self.ontology_iri != '':
            print(self.ontology_iri, file=buffer)
        print('', file=buffer)

        print('[Source ontology]', file=buffer)
        for line in self.sources:
            print(line, file=buffer)
        print('', file=buffer)

        print('[Low level source term URIs]', file=buffer)
        for term in self.terms.values():
            # TODO: could exclude upper terms
            print(term, file=buffer)
        print('', file=buffer)

        print('[Top level source term URIs and target direct superclass URIs]', file=buffer)
        for term in self.terms.values():
            if term.subClassOf:
                print(term, file=buffer)
                print('subClassOf', term.subClassOf, file=buffer)
        print('', file=buffer)

        print('[Source term retrieval setting]', file=buffer)
        for line in self.settings:
            print(line, file=buffer)
        print('', file=buffer)

        print('[Source annotation URIs]', file=buffer)
        for line in self.annotations:
            print(line, file=buffer)

    def save(self):
        '''
        Save an Ontofox configuration file
        '''
        if self.path is None:
            raise Exception('No path to save to')
        with open(self.path, 'w') as f:
            self.write(f)

    def save_as(self, path):
        '''
        Save an Ontofox configuration file to a path
        '''
        with open(path, 'w') as f:
            self.write(f)

    def __str__(self):
        '''
        Render this configuration to a string
        '''
        buffer = io.StringIO()
        self.write(buffer)
        return buffer.getvalue()

    @staticmethod
    def list():
        '''
        List the Ontofox configuration files
        '''
        dir = os.path.join('src', 'ontology', 'OntoFox_inputs')
        filenames = os.listdir(dir)
        filenames.sort()
        results = []
        for filename in filenames:
            if filename.endswith('.txt') and '_input' in filename:
                path = os.path.join(dir, filename)
                if os.path.isfile(path):
                    results.append(path)
        return results

    @staticmethod
    def find(ontology_id):
        '''
        Given an ontology identifier,
        return the path to its Ontofox configuration file,
        or None
        '''
        for path in Ontofox.list():
            filename = os.path.basename(path)
            filename, ext = os.path.splitext(filename)
            if filename.lower().startswith(f'{ontology_id.lower()}_'):
                return path

    @staticmethod
    def normalize(path):
        '''
        Read, sort, then write an Ontofox configuration file
        '''
        ontofox = Ontofox(path)
        ontofox.sort()
        ontofox.save()


def roundtrip(path):
    '''
    Read then write an Ontofox configuration file
    '''
    filename = os.path.basename(path)
    print(f'Roundtrip test for {filename}: ', end='')

    ontofox = Ontofox()
    with open(path) as f:
        content = f.read()
    ontofox.load(path)

    dir = os.path.join('build', 'OntoFox_inputs')
    os.makedirs(dir, exist_ok=True)
    with open(os.path.join(dir, filename), 'w') as f:
        ontofox.write(f)

    if content == str(ontofox):
        print('PASS')
    else:
        print('FAIL')


def roundtrip_all():
    '''
    Roundtrip all files in the OntoFox_inputs directory
    '''
    for path in Ontofox.list():
        roundtrip(path)


def normalize_all():
    '''
    Normalize all files in the OntoFox_inputs directory
    '''
    for path in Ontofox.list():
        Ontofox.normalize(path)


class TestOntofox(unittest.TestCase):
    def test_empty(self):
        ontofox = Ontofox()
        self.assertEqual('''[URI of the OWL(RDF/XML) output file]

[Source ontology]

[Low level source term URIs]

[Top level source term URIs and target direct superclass URIs]

[Source term retrieval setting]

[Source annotation URIs]
''', str(ontofox))

    def test_lower(self):
        ontofox = Ontofox()
        ontofox.add(Term('http://example.com/a', 'A'))
        self.assertEqual('''[URI of the OWL(RDF/XML) output file]

[Source ontology]

[Low level source term URIs]
http://example.com/a # A

[Top level source term URIs and target direct superclass URIs]

[Source term retrieval setting]

[Source annotation URIs]
''', str(ontofox))

    def test_upper(self):
        ontofox = Ontofox()
        term = Term('http://example.com/a', 'A')
        term.subClassOf = Term('http://example.com/b')
        ontofox.add(term)
        self.assertEqual('''[URI of the OWL(RDF/XML) output file]

[Source ontology]

[Low level source term URIs]
http://example.com/a # A

[Top level source term URIs and target direct superclass URIs]
http://example.com/a # A
subClassOf http://example.com/b

[Source term retrieval setting]

[Source annotation URIs]
''', str(ontofox))

    def test_sort(self):
        ontofox = Ontofox()
        term = Term('http://example.com/y', 'Y')
        term.subClassOf = Term('http://example.com/a', 'A')
        ontofox.add(term)
        term = Term('http://example.com/x', 'X')
        term.subClassOf = Term('http://example.com/b', 'B')
        ontofox.add(term)
        ontofox.sort()
        self.assertEqual('''[URI of the OWL(RDF/XML) output file]

[Source ontology]

[Low level source term URIs]
http://example.com/x # X
http://example.com/y # Y

[Top level source term URIs and target direct superclass URIs]
http://example.com/x # X
subClassOf http://example.com/b # B
http://example.com/y # Y
subClassOf http://example.com/a # A

[Source term retrieval setting]

[Source annotation URIs]
''', str(ontofox))
