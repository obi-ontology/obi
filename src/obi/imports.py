import obi.util as util
from obi.ontofox import Ontofox, Term


def import_term(ontology_id, term_id, label=None):
    '''
    Import a term from a source ontology
    '''
    print(f"importing {term_id} from {ontology_id}")
    if not label:
        term_id, label = util.split_id(term_id)
    path = Ontofox.find(ontology_id)
    if path:
        config = Ontofox(path)
        config.add(Term(term_id, label))
        config.sort()
        config.save()
    else:
        raise Exception(f'No Ontofox configuration file for {ontology_id}: {term_id}')


