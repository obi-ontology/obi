import obi.cmd as cmd
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
        term_dict, imports = imp.prepare(ontology_id, term_id)
        imp.do_ignore(ontology_id, term_dict, imports)
    else:
        raise Exception(f'No ROBOT configuration file for {ontology_id}: {term_id}')


def import_term(ontology_id, term_id, label=None):
    '''
    Import a term from a source ontology
    '''
    if not label:
        term_id, label = util.split_id(term_id)
    if imp.find(ontology_id):
        term_dict, imports = imp.prepare(ontology_id, term_id)
        imp.do_import(ontology_id, term_dict, imports)
    else:
        path = Ontofox.find(ontology_id)
        if path:
            config = Ontofox(path)
            config.add(Term(term_id, label))
            config.sort()
            config.save()
        else:
            raise Exception(f'No Ontofox or ROBOT configuration file for {ontology_id}: {term_id}')


def remove_term(ontology_id, term_id, label=None):
    '''
    Remove a term from an import config file
    '''
    if imp.find(ontology_id):
        term_dict, imports = imp.prepare(ontology_id, term_id)
        imp.do_remove(ontology_id, term_dict, imports)
    else:
        path = Ontofox.find(ontology_id)
        if path:
            config = Ontofox(path)
            config.remove(Term(term_id, label))
            config.sort()
            config.save()
        else:
            raise Exception(f'No Ontofox or ROBOT configuration file for {ontology_id}: {term_id}')


def refresh(ontology_id):
    '''
    Refresh the OWL file of an import module
    '''
    if imp.find(ontology_id):
        imp.refresh_module(ontology_id)
    else:
        path = Ontofox.find(ontology_id)
        if path:
            cmd.build_ontofox_module(ontology_id)
        else:
            raise Exception(f'No Ontofox or ROBOT configuration file for {ontology_id}')
