# OBI Command Line Package

[![Powered by ROBOT](https://img.shields.io/static/v1?label=powered%20by&message=ROBOT&color=green&style=flat)](http://robot.obolibrary.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Subcommands

### Term

`obi term` subcommands interact with individual terms in OBI.

#### List

`obi term list` lists all terms in OBI including imported terms.

#### Import

`obi term import` adds a term or terms to the import config file for one of OBI's import modules:

```
obi term import UBERON:0000062
# Adds UBERON:0000062 to the UBERON import config file
```

Sometimes it may be useful to import a term in an import module for an ontology that isn't the source of the term in order to ensure that term shows up in the module's hierarchy (e.g., including CL:cultured cell as the uppermost term in a CLO import module). To add a term to an import module for an ontology that isn't the source of the term, name the intended module before the term:

```
obi term import CLO CL:0000010 
# Adds CL:0000010 to the CLO import config file
```

You can identify a term to be imported by its CURIE, its IRI, or its label (though the latter requires a module to be specified):

```
obi term import UBERON organ
# Adds UBERON:0000062 ('organ') to the UBERON import config file
```

You can also provide a path to a text file containing one CURIE, IRI, or label per line:

```
obi term import PATO terms.txt
# Adds all terms in terms.txt to the PATO import config file
```

#### Ignore

`obi term ignore` prevents a term from being imported in a particular module even if it appears in axioms for other imported terms:

```
obi term ignore UBERON:0000062
# Prevents the UBERON import module from containing UBERON:0000062
```

```
obi term ignore IAO BFO:0000031
# Prevents the IAO import module from containing BFO:0000031
```

Like with `obi term import`, you can also provide an IRI, label, or a path to a text file containing one CURIE, IRI, or label per line.

#### Remove

`obi term remove` removes a term or terms from the import config file for one of OBI's import modules:

```
obi term remove UBERON:0000062
# Removes UBERON:0000062 from the UBERON import config file
```

```
obi term remove IAO BFO:0000031
# Removes BFO:0000031 from the IAO import config file
```

`remove` removes terms regardless of whether they're imported or ignored. Removing an imported term from the config file doesn't guarantee that it won't show up in the output module; depending on its relations to other imported terms, it may be imported anyway.

Like with `obi term import`, you can also provide an IRI, label, or a path to a text file containing one CURIE, IRI, or label per line.

### Import

`obi import` subcommands interact with import module files.

#### Clean

`obi import clean` removes unused terms (i.e., terms not occurring in any axioms of other terms in OBI) from import config files. It acts on config files listed as arguments, or all config files if no arguments are provided:

```
obi import clean UBERON PATO
# Removes unused terms from the UBERON and PATO config files
```

#### Convert

`obi import convert` creates a ROBOT import config file based on an OntoFox import config file. It acts on config files listed as arguments, or all config files if no arguments are provided:

```
obi import convert GO
# Creates src/ontology/robot_inputs/GO_input.tsv based on src/ontology/Ontofox_inputs/GO_input.txt
```

#### Normalize

`obi import normalize` sorts and formats OntoFox import config files. It acts on config files listed as arguments, or all config files if no arguments are provided:

```
obi import normalize UBERON PATO
# Sorts and formats the UBERON and PATO config files
```

#### Rebuild
`obi import rebuild` rebuilds an import module from its config file. It acts on modules listed as arguments, or all modules if no arguments are provided:

```
obi import rebuild GO
# Creates src/ontology/*_outputs/GO_imports.owl based on src/ontology/*_inputs/GO_input.*
```

### Source
`obi source` subcommands interact with the source files from which ROBOT import modules extract terms.

#### Download
`obi source download` downloads the source file for an import module and puts it in `build/`. The default source IRI for `*_imports.owl` is `http://purl.obolibrary.org/obo/*.owl`. If a different source is set in `src/ontology/import_sources.tsv`, that file will be downloaded instead.

```
obi source download UBERON
# Downloads UBERON source file to build/UBERON_import_source.owl
```

#### Set
`obi source set` sets the source IRI for an import module. Non-default import source IRIs are recorded in `src/ontology/import_sources.tsv`.

```
obi source set CL http://purl.obolibrary.org/obo/cl/cl-base.owl
# Sets http://purl.obolibrary.org/obo/cl/cl-base.owl as the source IRI for the CL import module
```

#### Remove
`obi source remove` removes a set source IRI from `src/ontology/import_sources.tsv` to return to using the default source IRI for a particular module.

```
obi source remove CL
# Removes any non-default source IRI for CL from src/ontology/import_sources.tsv
```
