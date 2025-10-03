#!/usr/bin/env python3

import click
import csv

import obi.util as util

from obi.ontofox import Ontofox
from obi.template import Template
from obi.imports import import_term


### CLI

@click.group()
def cli():
    '''
    Utilities for managing OBI
    '''
    pass


@cli.group()
def term():
    '''
    Work with ontology terms
    '''
    pass


@term.command('list')
def list_terms():
    '''
    List all terms use in OBI, including imports
    '''
    util.export_terms()
    path = 'build/obi-terms.tsv'
    with open(path) as f:
        rows = csv.reader(f, delimiter='\t')
        for row in rows:
            print(row[0], '\t', row[1])


@term.command('import')
@click.argument('term_ids', nargs=-1)
def import_terms(term_ids):
    '''
    Import one or more terms from source ontologies
    '''
    if len(term_ids) < 1:
        print('ERROR: Please provide at least one term ID to import.')
        exit(1)
    for term_id in term_ids:
        import_term(term_id)


@cli.group('import')
def imports():
    '''
    Work with ontology imports
    '''
    pass


@imports.command('normalize')
@click.argument('ontology_ids', nargs=-1)
def normalize_import(ontology_ids):
    '''
    Normalize import files
    '''
    if len(ontology_ids) < 1:
        for path in Ontofox.list():
            Ontofox.normalize(path)
    else:
        for ontology_id in ontology_ids:
            path = Ontofox.find(ontology_id)
            if path:
                Ontofox.normalize(path)


@cli.group()
def template():
    '''
    Work with term templates
    '''
    pass


def template_paths(template_names):
    '''
    Given a list of template names, return a list of template paths  
    '''
    if len(template_names) == 0:
        paths = Template.list()
    else:
        paths = []
        for template_name in template_names:
            path = Template.find(template_name)
            if path:
                paths.append(path)
    return paths


@template.command('check')
@click.argument('template_names', nargs=-1)
def check_templates(template_names):
    '''
    Check templates for missing terms
    '''
    labels = util.get_labels()
    terms = set(labels.keys())
    for path in template_paths(template_names):
        template = Template(path)
        missing = template.missing(terms)
        if missing:
            print(f'ERROR: {len(missing)} missing term(s)')
            for term in missing:
                print(term)


@template.command('match')
@click.argument('template_name', nargs=1)
@click.argument('term_file', nargs=1, type=click.Path())
def match_tempaltes(template_name, term_file):
    '''
    Check a template for missing terms, then try to find them
    '''
    path = Template.find(template_name)
    if not path:
        print(f'ERROR: no template found for {template_name}')
        exit(1)
    template = Template(path)

    labels = util.get_labels()
    new_terms = util.read_term_table(term_file)

    found, missing = template.match(labels, new_terms)
    if found:
        print(f'Found {len(found)} term(s)')
        for term in found:
            print(term)
    if found and missing:
        print()
    if missing:
        print(f'ERROR: {len(missing)} missing term(s)')
        for term in missing:
            print(term)
        exit(1)

@template.command('import')
@click.argument('template_name', nargs=1)
@click.argument('term_file', nargs=1, type=click.Path())
def import_templates(template_name, term_file):
    '''
    Check a template for missing terms, then try to import them
    '''
    path = Template.find(template_name)
    if not path:
        print(f'ERROR: no template found for {template_name}')
        exit(1)
    template = Template(path)

    labels = util.get_labels()
    new_terms = util.read_term_table(term_file)
    found, missing = template.import_found(labels, new_terms)
    if found:
        print(f'Found {len(found)} term(s)')
        for term in found:
            print(term)
    if found and missing:
        print()
    if missing:
        print(f'ERROR: {len(missing)} missing term(s)')
        for term in missing:
            print(term)
        exit(1)


if __name__ == '__main__':
    cli()
