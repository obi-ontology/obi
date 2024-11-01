# Ontology for Biomedical Investigations

[![GitHub Actions](https://github.com/obi-ontology/obi/actions/workflows/obi-test.yml/badge.svg)](https://github.com/obi-ontology/obi/actions/workflows/obi-test.yml)
[![Powered by the ROBOT](https://img.shields.io/static/v1?label=Powered%20by&message=ROBOT&color=green&style=flat)](http://robot.obolibrary.org/)
<a href="http://dashboard.obofoundry.org/dashboard/obi/dashboard.html"><img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FOBOFoundry%2Fobo-dash.github.io%2Fgh-pages%2Fdashboard%2Fobi%2Fdashboard-score-badge.json" /></a>
<a href="http://dashboard.obofoundry.org/dashboard/obi/dashboard.html"><img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FOBOFoundry%2Fobo-dash.github.io%2Fgh-pages%2Fdashboard%2Fobi%2Fdashboard-qc-badge.json" /></a>


The Ontology for Biomedical Investigations (OBI) helps you communicate clearly about scientific investigations by defining more than 2500 terms for assays, devices, objectives, and more.

This is the developer repository for OBI. You can download the most up-to-date OBI products [here](http://obofoundry.org/ontology/obi.html) and learn more about OBI through [our documentation](http://obi-ontology.org/docs/).

# Editing

Our ontology terms come in three groups. Depending on what type of term you want to edit or add, you have to go through different routes:

1. external terms (from other ontologies): We use [OntoFox](http://ontofox.hegroup.org) for imports. Edit the corresponding [`src/ontology/OntoFox_inputs/`](src/ontology/OntoFox_inputs/) file.
2. template terms: We use [ROBOT templates](http://robot.obolibrary.org/template) to convert spreadsheets to OWL. Edit the relevant [`src/ontology/templates/`](src/ontology/templates/) file:
    - [`obsolete.tsv`](src/ontology/templates/obsolete.tsv) for obsolete terms
    - [`assays.tsv`](src/ontology/templates/assays.tsv) for general assays
    - [`epitope-assays.tsv`](src/ontology/templates/epitope-assays.tsv) specifically for immune epitope assays
    - [`value-specifications.tsv`](src/ontology/templates/value-specifications.tsv)
    - [`specimens.tsv`](src/ontology/templates/specimens.tsv) for specimens
    - [`medical-history.tsv`](src/ontology/templates/medical-history.tsv) for medical history classifications and related selection criteria
    - [`study-designs.tsv`](src/ontology/templates/study-designs.tsv) for study designs
    - [`data-sets.tsv`](src/ontology/templates/data-sets.tsv) for data sets

3. other terms: Edit [`src/ontology/obi-edit.owl`](src/ontology/obi-edit.owl) in Protege.

See below for a full list of files, build instructions, and instructions on using Git and GitHub for OBI.

### Importing from a New Ontology

If you wish to import terms from an ontology for which OBI does not currently have an OntoFox import file ([`src/ontology/OntoFox_inputs/`](src/ontology/OntoFox_inputs/)), follow these steps:

1. Write the import file for the new ontology (see existing import files for reference).
2. Update [`catalog-v001.xml`](src/ontology/catalog-v001.xml) to list the new import file like it lists the existing import files.
3. Add an import statement to [`obi-edit.owl`](src/ontology/obi-edit.owl).
4. Create a blank file for the output module in [`src/ontology/OntoFox_outputs/`](src/ontology/OntoFox_outputs), e.g., to make phony output for foo.owl imports:
```
touch src/ontology/OntoFox_outputs/foo_imports.owl
```
5. Build the module & obi.owl.
```
make imports
make obi.owl
```

### Editing Templates in Excel

If you wish to edit a template or templates in Excel, rather than copy & pasting the template, we ask that you follow this workflow to preserve quoting. Going back and forth with Excel can cause some unintentional changes to double quotes within templates.

First, install the python requirements:
```
python3 -m pip install -r requirements.txt
```

Then, make the Excel sheet. In your local OBI git directory, run the following command to create a file called `obi.xlsx`:
```
make obi.xlsx
```

Next, open `obi.xlsx` in Excel (or whatever editor you prefer). This spreadsheet contains a tab for each OBI template (e.g., "study-design", "assays", etc.). Find the tab that corresponds to the template you need to edit, make your changes, and save the Excel spreadsheet to the same location (`obi.xlsx`). Finally, run the following to update the TSV versions of the templates:
```
make update-tsv
```

This will convert the tabs in `obi.xlsx` back to TSVs and overwrite the existing TSVs in the `src/ontology/templates/` directory with your changes. Review your changes (`git diff`) and make your pull request.

### Finding Terms

To find where a term lives, you can use [`src/scripts/locate.py`](src/scripts/locate.py). 

Then you can run the script to find terms by ID or label by passing them as a space-separated list, for example:
```
src/scripts/locate.py OBI:0000070 CHMO:0000087 GO:0000785
```

Labels should be enclosed in double quotes:
```
src/scripts/locate.py "assay" "fluorescence microscopy" "chromatin"
```

## Editing Utility Scripts

The OBI repo includes some Python scripts to help developers efficiently edit both `obi-edit.owl` and OBI templates. These scripts require Python 3.

The scripts also require that you first to build two databases (one from OBI edit, and one from a merged version of OBI):
```
make obi-dbs
```

### Relabeling Terms

Since labels are used in templates, manually finding and replacing all usages of a term can be difficult and tedious. Instead, you can use [`src/scripts/relabel.py`](src/scripts/relabel.py) to automatically update a term's label and its usages.

You can run this by passing the term you want to update and the new label:
```
src/scripts/relabel.py CHMO:0000087 "microscopy with fluorescence"
```

You can also pass the old label as the first argument, as long as it is enclosed in double quotes:
```
src/scripts/relabel.py "fluorescence microscopy" "microscopy with fluorescence"
```

Make sure to commit all changed files to ensure that all usages are updated.


# Files

- [`README.md`](README.md) this overview document
- [`obi.owl`](obi.owl) the latest release of OBI
- [`Makefile`](Makefile) scripts for building OBI
- [`views/`](views/) various specialized views of OBI
    - [`obi.obo`](views/obi.obo) the latest release of OBI in `.obo` file format
    - [`obi_core.owl`](views/obi_core.owl) the latest release of OBI Core: ~100 key terms
- [`src/`](src/)
    - [`ontology/`](src/ontology/) source files for OBI
        - [`obi-edit.owl`](src/ontology/obi-edit.owl) the main OBI OWL file
        - [`core.txt`](src/ontology/core.txt) the list of OBI Core terms
        - [`external-byhand.owl`](src/ontology/external-byhand.owl) some custom imports from other ontologies
        - [`catalog-v001.xml`](src/ontology/catalog-v001.xml) an artisinal list of OWL import overrides
        - [`templates/`](src/ontology/templates/) ROBOT template files for various branches of OBI
        - [`modules/`](src/ontology/modules/) the results of the ROBOT templates
        - [`OntoFox_inputs/`](src/ontology/OntoFox_inputs) OntoFox configuration files for importing from other ontologies
        - [`OntoFox_outputs/`](src/ontology/OntoFox_outputs) OntoFox result files
    - [`sparql/`](src/sparql/) SPARQL queries for building and validating OBI
    - [`scripts/`](src/scripts/) utility scripts
    - [`views/`](src/views/) configuration for views


# Building

The [`Makefile`](Makefile) contains scripts for building OBI. On macOS or Linux, you should just be able to run `make` or one of the specific tasks below. On Windows consider using some sort of Linux virtual machine such as Docker or Vagrant. Most results will be in the `build/` directory. If you have trouble, contact [James](mailto:james@overton.ca).

- `make test` merge and run SPARQL tests (this is run on every push to GitHub)
- `make sort` sort templates, and fix quoting and line endings
- `make imports` update OntoFox imports
- `make modules` update ROBOT templates
- `make obi.owl` build the release file; reasoning can take about 10 minutes
- `make views` update ROBOT templates
- `make all` prepare for a release, runs `imports`, `modules`, `test`, `obi.owl`, and `views`
- `make build/obi_merged.owl` merge `obi-edit.owl` into a single file, don't reason
- `make clean` remove temporary files


# Development

We use git and GitHub to develop OBI. There's a lot of good documentation on both:

- git [website](https://git-scm.com) with files and documentation
- GitHub [Help](https://help.github.com) and [Flow](https://guides.github.com/introduction/flow/)


## Initial Set Up

Before you can start developing with OBI, you will need to do some initial setup:

1. sign up for a [GitHub account](https://github.com)
2. install the [Git command line tool](https://help.github.com/articles/set-up-git/), the [GitHub Desktop app](https://help.github.com/articles/set-up-git/), or another Git client of your choosing
3. [configure Git with your name and email](https://help.github.com/articles/setting-your-username-in-git/)
4. [clone the OBI repository](https://help.github.com/articles/cloning-a-repository/)
5. if you're using macOS and Excel, set up a pre-commit hook (see below for details):

       ln -s ../../src/scripts/check-line-endings.sh .git/hooks/pre-commit


## Making Changes

Changes should be made in manageable pieces, e.g. add one term or edit a few related terms. Most changes should correspond to a single issue on the tracker.

Start from a local copy of the `master` branch of the OBI repository. Make sure your local copy is up-to-date. Make your changes on a new branch. Please use the [OBI Term ID Reservations](https://docs.google.com/spreadsheets/d/1tpDrSiO1DlEqkvZjrDSJrMm7OvH9GletljaR-SDeMTI) sheet to manage new IDs.

When you're ready, push your branch to the OBI repository and make a Pull Request (PR) on the GitHub website. Your PR is a request to merge your branch back into `master`. Your PR will be tested, discussed, adjusted if necessary, then merged. Then the cycle can repeat for the next change that you or another developer will make.

These are the steps with their CLI commands. When using a GUI application the steps will be the same.

1. `git fetch` make sure your local copy is up-to-date
2. `git checkout master` start on the `master` branch
3. `git checkout -b your-branch-name` create a new branch named for the change you're making
4. make your changes
5. `make sort` sort and normalize tables, for cleaner diffs
6. `git status` and `git diff` inspect your changes
7. `git add --update src/` add all updated files in the `src/` directory to staging
8. `git commit --message "Description, issue #123"` commit staged changes with a message; it's good to include an issue number
9. `git push --set-upstream origin your-branch-name` push your commit to GitHub
10. open <https://github.com/obi-ontology/obi> in your browser and click the "Make Pull Request" button

Your Pull Request will be automatically tested. If there are problems, we will update your branch. When all tests have passed, your PR will be reviewed by OBI developers. When that review is complete, a senior OBI developer will merge the PR. Rinse and repeat!


## Keeping Things Tidy

The easiest way to edit our `src/ontology/template/` files is with Excel. Unfortunately Excel has some idiosyncratic rules for quoting cell values, and on macOS [uses old line endings](http://developmentality.wordpress.com/2010/12/06/excel-2008-for-macs-csv-bug/). Both these things make our diffs messy and confusing.

For clean diffs, we also like to keep out templates sorted by ID. The `make sort` command will fix line endings and sorting by running all the templates through a Python script.
