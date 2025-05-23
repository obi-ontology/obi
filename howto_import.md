# Managing ROBOT imports with import.py

`src/scripts/import.py` is a script for automating the process of editing ROBOT imports. It acts on input files (e.g., `src/ontology/robot_inputs/Uberon_input.tsv`) that determine the behavior of the ROBOT import workflow. The script can add and remove terms from the input file, prevent terms from being imported, and assert desired parents for imported terms.

## ROBOT import workflow overview

This ROBOT import workflow is a multi-stage process designed to ensure control over precisely which terms are imported from the source ontology into the target ontology. It includes the following steps:

1. A MIREOT extraction from the source to capture a broad selection of desired terms and axioms.
2. A subset extraction with a termlist derived from the MIREOT extraction.
3. A removal of any remaining unwanted terms.
4. A merge with a OWL file containing any subclass axioms necessary to connect imported terms into the target ontology's hierarchy.
5. Formatting, including annotation and conversion.

## Input files

Input files are TSVs that dictate the behavior of the steps of ROBOT importing workflow. Input files have five columns:

| ontology ID | label | action | logical type | parent class |
| --- | --- | --- | --- | --- |
| BFO:0000040 | material entity | limit |   |   |
| BFO:0000050 | part of | relate |   |   |
| BFO:0000051 | has part | relate |   |   |
| UBERON:0000007 | pituitary gland | import |   |   |
| UBERON:0000072 | proximo-distal subdivision of respiratory tract | ignore |   |   |
| UBERON:0000105 | life cycle stage | parent | subclass | biological_process |

The `action` column indicates how a term is used:

- `action: import` terms will always be included in the output OWL file.
- `action: ignore` terms will never be included in the output OWL file.
- `action: limit` terms set an upper limit on the import's hierarchy, with no terms above the limit term being imported.
- `action: relate` terms are the object properties that will be included in the output OWL file.

The output OWL file may include terms that are not mentioned in the input file, as the OWL file's contents are dictated by the logic of the MIREOT and subset extraction methods.

## Using import.py

`import.py` automates the process of editing input files. It can be run from the command line with the following general command structure:

```
python3 src/scripts/import.py [subcommand] [ontology] [term] [flags]
```
### Subcommands

#### Import

`import` adds terms to the input file to be imported. It can be used with the flags `--limit` (`-l`) and `--parent` (`-p`) to set a term as an upper limit on the imported hierarchy or to specify a parent for that term respectively.

#### Ignore

`ignore` adds terms to the input file to be ignored, so they will not appear in the output OWL file.

#### Remove

`remove` removes a term from the input file. A removed term may still appear in the output OWL file based on its logical relationships to other terms in the file.

#### Split

`split` creates several build files based on the input file to pass to the ROBOT import workflow. This subcommand is implemented in the Makefile, and it is unlikely that most users will need to call it directly.

### Setting the source ontology

The source ontology is the name of the ontology that is being imported from, e.g., Uberon, GO, or HP. By default, the script will look for a local copy at `build/[ontology]_import_source.owl`, but a different path can be specified with the `--source` flag.

### Specifying terms

The terms to act on can be specified in four different ways:

- CURIE, e.g., `EXAMPLE:0000000`
- IRI, e.g., `http://purl.obolibrary.org/obo/EXAMPLE_0000000`
- Label, e.g., "soup"
- Path to a text file with one CURIE, IRI, or label per line, e.g., `path/to/terms.txt`

## Examples

The following examples use a mix of methods for specifying terms in commands, but any method (CURIE, IRI, label, or text file) works with any subcommand.

Import `EXAMPLE:0000000` 'soup':

```
python3 src/scripts/import.py import example soup
```

Import `EXAMPLE:0000001` 'bowl' as a subclass of `BFO:0000040` 'material entity':

```
python3 src/scripts/import.py import example EXAMPLE:0000001 -p "material entity"
```

Import `BFO:0000040` 'material entity' as an upper limit to the imported hierarchy:

```
python3 src/scripts/import.py import example BFO:0000040 -l
```

Import terms listed in the file `soups.txt`:

```
python3 src/scripts/import.py import example soups.txt
```

Remove `EXAMPLE:0000004` 'chowder':

```
python3 src/scripts/import.py remove example EXAMPLE:0000004
```

Ignore `EXAMPLE:0000005` 'potato':

```
python3 src/scripts/import.py ignore example potato
```
