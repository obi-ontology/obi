# Managing ROBOT imports with import.py

`src/scripts/import.py` is a script for automating the process of editing ROBOT imports. It acts on input files (e.g., `src/ontology/robot_inputs/Uberon_input.tsv`) that determine the behavior of the ROBOT import workflow. The script can add and remove terms from the input file, prevent terms from being imported, and assert desired parents for imported terms.

## ROBOT import workflow overview

This ROBOT import workflow is a multi-stage process designed to ensure control over precisely which terms are imported from the source ontology. It includes the following steps, with bold text indicating parts of the workflow that are determined by the contents of the input file:

1. A MIREOT extraction from the source to capture a broad selection of desired terms and axioms, including the **input terms** and the terms needed to include all their axioms.
2. A subset extraction with a termlist derived from the MIREOT extraction, to reduce unneeded terms and axioms by including only the desired **relations**.
3. A removal of any remaining **unwanted terms**.
4. A merge with a OWL file containing any **subclass axioms** necessary to connect imported terms into the target ontology's hierarchy.
5. Formatting, including annotation and conversion.

## Input files

Input files are TSVs that dictate the behavior of the steps of ROBOT importing workflow. Input files have five columns:

| ontology ID | label | action | logical type | parent class |
| --- | --- | --- | --- | --- |
| BFO:0000040 | material entity | upper |   |   |
| BFO:0000050 | part of | relate |   |   |
| BFO:0000051 | has part | relate |   |   |
| UBERON:0000007 | pituitary gland | input |   |   |
| UBERON:0000072 | proximo-distal subdivision of respiratory tract | block |   |   |
| UBERON:0000105 | life cycle stage | parent | subclass | biological_process |


The `status` column indicates how a term is used:

- `status: input` terms are passed to ROBOT as lower terms in the initial MIREOT extraction from the source ontology.
- `status: upper` terms are passed to ROBOT as upper terms in the initial MIREOT extraction from the source ontology.
- `status: relate` terms are relations included in the subset extraction. These are the relations (along with subClassOf) that will appear in the output OWL file.
- `status: block` terms are passed to ROBOT as a list of terms to be removed from the subset extraction.
- `status: parent` terms are classes to which a custom subclass axiom is applied. The labels provided in the `parent class` column will be the parents of these terms in the output OWL file.

The output OWL file may include terms that are not mentioned in the input file, as the OWL file's contents are dictated by the logic of the MIREOT and subset extraction methods. However, terms with statuses `input`, `parent`, `relate`, and `upper` will _always_ appear in the output OWL file, and terms with status `block` will _never_ appear in the output OWL file.

## Using import.py

### Arguments

`import.py` has seven arguments:

- The `--ontology` (`-o`) argument (required) indicates which ontology import to work with, e.g., `--ontology PATO` will edit `src/ontology/robot_inputs/PATO_input.tsv`. This is necessary because one might need to add a term from ontology X to the import file for ontology Y to ensure that term shows up properly in axioms from ontology Y, so the script doesn't assume you want to be editing `X_imports.tsv` if you're adding or removing a term from ontology X.
- The `--action` (`-a`) argument (required) indicates what you want to do to the input file. Action options include `add`, `block`, `drop`, `parent`, and `split`, each of which is discussed in more detail below.
- The `--term` (`-t`) and `--termlist` (`-l`) arguments are optional but required for actions that modify the contents of the import files. These arguments indicate the term or terms to act on. `--term` accepts a single CURIE or IRI, and `--termlist` accepts a path to a text file containing one CURIE or IRI per line.
- The `--parent` (`-p`) argument is optional but required for the `parent` action. This argument indicates the intended parent of a term, if it is to be imported as a subclass of a different term than its superclasses in its source ontology, and it accepts the label of the intended parent. The parent term must be an OBI term or a term imported into OBI.
- The `--relation` (`-r`) argument is optionally usable with the `add` action. This argument flags the term as a relation in the `action` column of the input file.
- The `--upper` (`-u`) argument is optionally usable with the `add` action. This argument flags the term as an upper-level term in the `action` column of the input file.

### Actions

The `--action` argument directs the behavior of the script. The actions `add`, `block`, `drop`, and `parent` modify the contents of an input file, while `split` creates a set of build files based on the input file, which are used in the ROBOT import workflow.

#### Add

`--action add` adds a term or terms to the input file. When used with `--term EXAMPLE:0000000`, it adds a row for the term EXAMPLE:0000000. When used with `--termlist example.txt`, it adds one row for each line containing an IRI or CURIE in `example.txt`.

By default, terms added to the file with `--action add` have status `input`, meaning they are classes that will appear in the output OWL file. `--action add EXAMPLE:0000000` can be used with `--relation True` if EXAMPLE:0000000 is a relation, which will add EXAMPLE:0000000 to the input file with status `relate`. `--action add` can also be used with `--upper True` to set EXAMPLE:0000000 as an upper-level term in the initial MIREOT extraction step.

`--parent 'example parent label'` can also be used with `--action add` to add a term with a specified parent that wouldn't otherwise be a superclass of that term in its source ontology. For instance, `--action add --term EXAMPLE:0000000 --parent 'material entity'` will add EXAMPLE:0000000 to the file to be imported as a subclass of BFO:0000040 'material entity'.

#### Block

`--action block` adds a term or terms to the input file with status `block`, so they will _not_ be included in the output OWL file. When used with `--term EXAMPLE:0000000`, it adds a row for the term EXAMPLE:0000000. When used with `--termlist example.txt`, it adds one row for each line containing an IRI or CURIE in `example.txt`.

#### Drop

`--action drop` removes a term or terms from the input file. When used with `--term EXAMPLE:0000000`, if there is a row for the term EXAMPLE:0000000 in the input file, the script will delete that row from the file. When used with `--termlist example.txt`, it will do the same for each line containing an IRI or CURIE in `example.txt`.

#### Parent

`--action parent` adds a term or terms to the input file with a selected parent, specified with `--parent 'example parent label'`. When used with `--term EXAMPLE:0000000`, it adds a row for the term EXAMPLE:0000000, and the output OWL file will make EXAMPLE:0000000 a subclass of 'example parent label'. When used with `--termlist example.txt`. it will do the same for each line containing an IRI or CURIE in `example.txt`.

If EXAMPLE:0000000 is not already in the input file, `--action parent --term EXAMPLE:0000000 --parent 'example parent label'` is functionally equivalent to `--action add --term EXAMPLE:0000000 --parent 'example parent label'`.

#### Split

`--action split` updates the build files that are passed to the ROBOT import workflow based on the contents of the input file. Splitting is performed automatically as part of the workflow when called with `make path/to/import.owl`, so it's rarely necessary to use `--action split` manually.

The build files produced by `--action split` are as follows, with the relevant ontology abbreviation in place of "example" in the paths:

- `example_input.txt`, a list of all terms with status `input` and `parent`, to be used as lower terms for the initial MIREOT extraction.
- `example_upper.txt`, a list of all terms with status `upper`, to be used as upper terms for the initial MIREOT extraction.
- `example_relations.txt`, a list of all terms with status `relate`, to be used as one termlist in the subset extraction.
- `example_blocklist.txt`, a list of all terms with status `block`, to be used as the list of terms to be removed from the results of the subset extraction.
- `example_parent.tsv`, a table of all terms with status `parent`, to be used as a template for creation of an OWL file containing the custom subclass axioms, which is merged in with the extracted terms to create the output OWL file.

# Tutorial: Creating an input file

This tutorial demonstrates how to use import.py to set up an input file to use with the ROBOT import workflow. We'll use Uberon as an example for the ontology from which we're importing.

Steps marked OPTIONAL aren't strictly necessary for making a working input file, but the examples shown in the tutorial will use those steps.

## 1: Gather a list of terms

First we'll make a list of CURIEs or IRIs of classes we want. For convenience later, we're going to put them into a text file like this (the commented labels are for human readability and convenience, they're not strictly necessary):

```
UBERON:0000029 # lymph node
UBERON:0000105 # life cycle stage
UBERON:0000178 # blood
UBERON:0000465 # material anatomical entity
UBERON:0000479 # tissue
UBERON:0000945 # stomach
UBERON:0001555 # digestive tract
```

We'll call this text file `terms.txt`.

### 1.1: (OPTIONAL) Choose and add upper-level terms

If a lot of our terms come from a single branch of an ontology, setting an upper-level term can minimize the amount of high-level terms that will need to be trimmed out later. Setting an upper-level term isn't necessary, so this step can be skipped.

In this case, most of the terms we're importing are in the 'material anatomical entity' branch. The term 'life cycle stage' is the exception to the rule, but we'll deal with that later. For now, we'll base our upper term on this branch. The "attachment point" between our ontology and Uberon's 'material anatomical entity' hierarchy is BFO:0000040 'material entity', the parent class of 'material anatomical entity'. So we'll set BFO:0000040 'material entity' as our upper-level term:

```
python3 src/scripts/import.py -o Uberon -a add -t BFO:0000040 -u True
```

The `-o` (`--ontology`) argument specifies that we want to edit the Uberon import, the `-a` (`--action`) argument indicates that we want to be _adding_ a term to the file, the `-t` (`--term`) argument indicates that BFO:0000040 is the term we want to be adding, and the `-u` (`--upper`) argument specifies that we want to add BFO:0000040 as an upper-level term.

Because the Uberon input file doesn't exist yet, the script will ask to confirm that we want to create it. Once we confirm, the script will create the file, and it will look like this:

| ontology ID | label | status | logical type | parent class |
| --- | --- | --- | --- | --- |
| BFO:0000040 | material entity | upper |   |   |

## 2: Add terms to the input file

Next, we'll add the terms we included in `terms.txt` to the import file:

```
python3 src/scripts/import.py -o Uberon -a add -l terms.txt
```

The `-o` (`--ontology`) argument specifies that we want to edit the Uberon import, the `-a` (`--action`) argument indicates that we want to be _adding_ a term to the file, and the `-l` (`--termlist`) argument indicates that we want to be adding the terms we listed in `terms.txt`.

If we didn't add an upper-level term earlier, the Uberon import file doesn't exist yet, so the script will ask to confirm that we want to create it at this point.

Our file now has a line for each of the terms in `terms.txt`:

| ontology ID | label | status | logical type | parent class |
| --- | --- | --- | --- | --- |
| BFO:0000040 | material entity | upper |   |   |
| UBERON:0000029 | lymph node | input |   |   |
| UBERON:0000105 | life cycle stage | input |   |   |
| UBERON:0000178 | blood | input |   |   |
| UBERON:0000465 | material anatomical entity | input |   |   |
| UBERON:0000479 | tissue | input |   |   |
| UBERON:0000945 | stomach | input |   |   |
| UBERON:0001555 | digestive tract | input |   |   |

### 2.1: (OPTIONAL) Choose and add relations

By default, subclass relations between the terms are captured, but there are probably other relations we want to make use of, too. For this, parthood relations would be useful to capture the relations between 'stomach' and 'digestive tract'. So we'll add BFO:0000050 'part of' and BFO:0000051 'has part':

```
python3 src/scripts/import.py -o Uberon -a add -t BFO:0000050 -r True
```

```
python3 src/scripts/import.py -o Uberon -a add -t BFO:0000051 -r True
```

The `-r` (`--relation`) argument indicates that we want to add these terms to the file as relations.

Here, we called the script separately for each relation we wanted to add, because we only had two relations to add, but we could put them into a text file like we did with the classes.

Our file now looks like this:

| ontology ID | label | status | logical type | parent class |
| --- | --- | --- | --- | --- |
| BFO:0000040 | material entity | upper |   |   |
| BFO:0000050 | part of | relate |   |   |
| BFO:0000051 | has part | relate |   |   |
| UBERON:0000029 | lymph node | input |   |   |
| UBERON:0000105 | life cycle stage | input |   |   |
| UBERON:0000178 | blood | input |   |   |
| UBERON:0000465 | material anatomical entity | input |   |   |
| UBERON:0000479 | tissue | input |   |   |
| UBERON:0000945 | stomach | input |   |   |
| UBERON:0001555 | digestive tract | input |   |   |

























Let's say I want to add UBERON:0002299 'alveolus of lung' to OBI's Uberon import.

I'll use the `--ontology` (`-o`) argument to specify that I want to edit the Uberon import: `-o Uberon`.

Then I'll use the `--action` (`-a`) argument to specify that I want to **add** a term: `-a add`.

Lastly, I'll use the `--term` (`-t`) argument to indicate which term I want to import: `-t UBERON:0002299`.

So I call the script like this:

```
python3 src/scripts/import.py -o Uberon -a add -t UBERON:0002299
```

The script will then add the following row to `src/ontology/robot_inputs/Uberon_input.tsv`:

| ontology ID | label | action | logical type | parent class |
| --- | --- | --- | --- | --- |
| UBERON:0002299 | alveolus of lung | input |   |   |

The script automatically labels and sorts rows in the input file for ease of use and readability. It also ensures that the same term can't be added twice.

### Adding multiple terms at once

If I want to add several terms to the Uberon import at once, I can create a text file with the CURIEs or IRIs of the terms I want to import, like this:

```
UBERON:0002299
UBERON:0004821
UBERON:0008874
UBERON:0009664
UBERON:0010368
```

Then, instead of using `-t UBERON:0002299`, I can use the `--termlist` (`-l`) argument:

```
python3 src/scripts/import.py -o Uberon -a add -l path/to/file.txt
```

The script then adds a row to the input file for each term in the term list.

## Removing Terms from an Import

`import.py` has two different methods for removing terms from an import:

- The action `block` prevents a term from being imported. Blocked terms will never show up in the resulting OWL file.
- The action `drop` removes a term's line in the import file. A term may still show up in the resulting OWL file after being dropped due to its logical connections to other imported terms. `drop` can also remove blocks on terms.

### Blocking Terms

Sometimes, importing a handful of terms from an ontology may import a of higher-level term that isn't needed in that import file. The `block` action prevents specific terms from showing up in the import file to solve problems like that. For instance, OBI imports two terms from HP. To avoid importing the upper-level term HP:0000001 'All' along with those terms, we can block that term:

```
python3 src/scripts/import.py -o HP -a block -t HP:0000001
```

The script will then add the following row to `src/ontology/robot_inputs/HP_input.tsv`:

| ontology ID | label | action | logical type | parent class |
| --- | --- | --- | --- | --- |
| HP:0000001 | All | block |   |   |

Then, HP:0000001 will not be included in `src/ontology/robot_outputs/HP_imports.owl`.

Like with `add`, you can use the `--termlist` (`-l`) argument to specify a path to a text file with a list of CURIEs or IRIs to block multiple terms at once.

### Dropping Terms

`drop` removes the row for a term from the input file, regardless of whether that term is imported or blocked. To remove the block on HP:0000001:

```
python3 src/scripts/import.py -o HP -a drop -t HP:0000001
```

You can also use the `--termlist` (`-l`) argument to specify a path to a text file with a list of CURIEs or IRIs to drop multiple terms at once.

## Selecting Parents for Imported Terms

Some terms may be subclasses of terms that we don't intend to import. 
