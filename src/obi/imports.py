import obi.util as util
from obi.ontofox import Ontofox, Term


def import_term(term_id, label=None):
    '''
    Import a term from a source ontology
    '''
    if not label:
        term_id, label = util.split_id(term_id)
    ontology_id = util.get_ontology_id(term_id)
    if not ontology_id:
        raise Exception(f'No ontology ID found for term {term_id}')

    path = Ontofox.find(ontology_id)
    if path:
        config = Ontofox(path)
        config.add(Term(term_id, label))
        config.sort()
        config.save()
    else:
        raise Exception(f'No Ontofox configuration file for {ontology_id}: {term_id}')


