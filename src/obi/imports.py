import obi.imp as imp
import obi.util as util
from obi.ontofox import Ontofox, Term


def ignore_term(ontology_id, term_id, label=None):
    '''
    Ignore a term in a ROBOT import config file
    '''
    if not label:
        term_id, label = util.split_id(term_id)
    if imp.find(ontology_id):
        imp.act('ignore', ontology_id, term_id)
    else:
        raise Exception(f'No ROBOT configuration file for {ontology_id}: {term_id}')



def import_term(ontology_id, term_id, label=None):
    '''
    Import a term from a source ontology
    '''
    if not label:
        term_id, label = util.split_id(term_id)
    path = Ontofox.find(ontology_id)
    if imp.find(ontology_id):
        imp.act('import', ontology_id, term_id)
    elif path:
        config = Ontofox(path)
        config.add(Term(term_id, label))
        config.sort()
        config.save()
    else:
        raise Exception(f'No Ontofox or ROBOT configuration file for {ontology_id}: {term_id}')


def remove_term(ontology_id, term_id):
    '''
    Remove a term from an import config file
    '''
    path = Ontofox.find(ontology_id)
    if imp.find(ontology_id):
        imp.act('remove', ontology_id, term_id)
    elif path:
        config = Ontofox(path)
        print("Removing from OntoFox file")
    else:
        raise Exception(f'No Ontofox or ROBOT configuration file for {ontology_id}: {term_id}')
