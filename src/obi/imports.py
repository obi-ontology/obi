import obi.imp as imp
import obi.util as util
from obi.ontofox import Ontofox, Term


def import_term(ontology_id, term_id, label=None):
    '''
    Import a term from a source ontology
    '''
    if not label:
        term_id, label = util.split_id(term_id)
    path = Ontofox.find(ontology_id)
    if imp.find(ontology_id):
        print(f"Adding {term_id} to ROBOT import of {ontology_id}")
        imp.full_import(ontology_id, term_id)
    elif path:
        config = Ontofox(path)
        config.add(Term(term_id, label))
        config.sort()
        config.save()
    else:
        raise Exception(f'No Ontofox or ROBOT configuration file for {ontology_id}: {term_id}')
