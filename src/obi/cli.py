#!/usr/bin/env python3

import click
import csv
import os

import obi.ontofox2robot as ontofox2robot
import obi.util as util

from obi.ontofox import Ontofox
from obi.template import Template
from obi.imports import ignore_term, import_term, remove_term, refresh
from obi.imp import change_source_iri, download_source_file
from obi.clean_ontofox_imports import check_file


# CLI


@click.group()
def cli():
    """
    Utilities for managing OBI
    """
    pass


@cli.group()
def term():
    """
    Work with ontology terms
    """
    pass


@term.command("list")
def list_terms():
    """
    List all terms use in OBI, including imports
    """
    util.export_terms()
    path = "build/obi-terms.tsv"
    with open(path) as f:
        rows = csv.reader(f, delimiter="\t")
        for row in rows:
            print(row[0], "\t", row[1])


@term.command("ignore")
@click.argument("ontology_id", nargs=1)
@click.argument("term_ids", nargs=-1)
def ignore_terms(ontology_id, term_ids):
    """
    Set one or more terms as ignored in ROBOT import config files
    """
    if not util.is_ontology_name(ontology_id):
        id_tuple = (ontology_id,)
        term_ids = id_tuple + term_ids
        ontology_id = util.get_ontology_id(ontology_id)
    for term_id in term_ids:
        ignore_term(ontology_id, term_id)


@term.command("import")
@click.argument("ontology_id", nargs=1)
@click.argument("term_ids", nargs=-1)
def import_terms(ontology_id, term_ids):
    """
    Import one or more terms from source ontologies
    """
    if not util.is_ontology_name(ontology_id):
        id_tuple = (ontology_id,)
        term_ids = id_tuple + term_ids
        ontology_id = util.get_ontology_id(ontology_id)
    for term_id in term_ids:
        import_term(ontology_id, term_id)


@term.command("remove")
@click.argument("ontology_id", nargs=1)
@click.argument("term_ids", nargs=-1)
def remove_terms(ontology_id, term_ids):
    """
    Remove one or more terms from import config files
    """
    if not util.is_ontology_name(ontology_id):
        id_tuple = (ontology_id,)
        term_ids = id_tuple + term_ids
        ontology_id = util.get_ontology_id(ontology_id)
    for term_id in term_ids:
        remove_term(ontology_id, term_id)


@cli.group("import")
def imports():
    """
    Work with ontology imports
    """
    pass


@imports.command("convert")
@click.argument("ontology_id", nargs=1)
def convert(ontology_id):
    """
    Create a ROBOT config file based on an Ontofox config file
    """
    ontology_id = ontology_id.upper()
    ontofox2robot.convert(ontology_id)


@imports.command("refresh")
@click.argument("ontology_id", nargs=1)
def refresh_module(ontology_id):
    """
    Rebuild the OWL file of a particular ontology import
    """
    refresh(ontology_id)


@imports.command("normalize")
@click.argument("ontology_ids", nargs=-1)
def normalize_import(ontology_ids):
    """
    Normalize import files
    """
    if len(ontology_ids) < 1:
        for path in Ontofox.list():
            Ontofox.normalize(path)
    else:
        for ontology_id in ontology_ids:
            path = Ontofox.find(ontology_id)
            if path:
                Ontofox.normalize(path)


@imports.command("clean")
@click.argument("ontology_ids", nargs=-1)
def clean_import(ontology_ids):
    """
    Remove unused terms from import config files
    """
    if len(ontology_ids) < 1:
        for path in Ontofox.list():
            filename = os.path.basename(path)
            ontology_id = filename.replace("_input.txt", "")
            check_file(ontology_id)
    else:
        for ontology_id in ontology_ids:
            check_file(ontology_id)


@cli.group("source")
def source():
    """
    Work with ROBOT import source files
    """
    pass


@source.command("set")
@click.argument("ontology", nargs=1)
@click.argument("iri", nargs=1)
def set_source(ontology, iri):
    """
    Set the IRI of the import source file for a ROBOT import
    """
    change_source_iri(ontology, iri)


@source.command("download")
@click.argument("ontology", nargs=1)
def download_source(ontology):
    """
    Download the import source file for a ROBOT import
    """
    download_source_file(ontology)


@source.command("remove")
@click.argument("ontology", nargs=1)
def remove_source(ontology):
    """
    Remove an IRI from the TSV of import source file IRIs
    """
    change_source_iri(ontology, "")


@cli.group()
def template():
    """
    Work with term templates
    """
    pass


def template_paths(template_names):
    """
    Given a list of template names, return a list of template paths
    """
    if len(template_names) == 0:
        paths = Template.list()
    else:
        paths = []
        for template_name in template_names:
            path = Template.find(template_name)
            if path:
                paths.append(path)
    return paths


@template.command("check")
@click.argument("template_names", nargs=-1)
def check_templates(template_names):
    """
    Check templates for missing terms
    """
    labels = util.get_labels()
    terms = set(labels.keys())
    for path in template_paths(template_names):
        template = Template(path)
        missing = template.missing(terms)
        if missing:
            print(f"ERROR: {len(missing)} missing term(s)")
            for term in missing:
                print(term)


@template.command("match")
@click.argument("template_name", nargs=1)
@click.argument("term_file", nargs=1, type=click.Path())
def match_tempaltes(template_name, term_file):
    """
    Check a template for missing terms, then try to find them
    """
    path = Template.find(template_name)
    if not path:
        print(f"ERROR: no template found for {template_name}")
        exit(1)
    template = Template(path)

    labels = util.get_labels()
    new_terms = util.read_term_table(term_file)

    found, missing = template.match(labels, new_terms)
    if found:
        print(f"Found {len(found)} term(s)")
        for term in found:
            print(term)
    if found and missing:
        print()
    if missing:
        print(f"ERROR: {len(missing)} missing term(s)")
        for term in missing:
            print(term)
        exit(1)


@template.command("import")
@click.argument("template_name", nargs=1)
@click.argument("term_file", nargs=1, type=click.Path())
def import_templates(template_name, term_file):
    """
    Check a template for missing terms, then try to import them
    """
    path = Template.find(template_name)
    if not path:
        print(f"ERROR: no template found for {template_name}")
        exit(1)
    template = Template(path)

    labels = util.get_labels()
    new_terms = util.read_term_table(term_file)
    found, missing = template.import_found(labels, new_terms)
    if found:
        print(f"Found {len(found)} term(s)")
        for term in found:
            print(term)
    if found and missing:
        print()
    if missing:
        print(f"ERROR: {len(missing)} missing term(s)")
        for term in missing:
            print(term)
        exit(1)


if __name__ == "__main__":
    cli()
