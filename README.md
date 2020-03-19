# Ontology for Biomedical Investigations

[![Build Status](https://travis-ci.org/obi-ontology/obi.svg?branch=master)](https://travis-ci.org/obi-ontology/obi)

The Ontology for Biomedical Investigations (OBI) helps you communicate clearly about scientific investigations by defining more than 2500 terms for assays, devices, objectives, and more.

This is the developer repository for OBI. You can download the most up-to-date OBI products [here](http://obofoundry.org/ontology/obi.html) and learn more about OBI through [our documentation](https://github.com/obi-ontology/obi/wiki).

# Editing

Our ontology terms come in three groups:

1. external terms (from other ontologies): We use [OntoFox](http://ontofox.hegroup.org) for imports. Edit the corresponding [`src/ontology/OntoFox_inputs/`](src/ontology/OntoFox_inputs/) file.
2. template terms: We use [ROBOT templates](http://robot.obolibrary.org/template) to convert spreadsheets to OWL. Edit the relevant [`src/ontology/templates/`](src/ontology/templates/) file:
    - [`obsolete.tsv`](src/ontology/templates/obsolete.tsv) for obsolete terms
    - [`assays.tsv`](src/ontology/templates/assays.tsv) for general assays
    - [`epitope-assays.tsv`](src/ontology/templates/epitope-assays.tsv) specifically for immune epitope assays
    - [`value-specifications.tsv`](src/ontology/templates/value-specifications.tsv)
    - [`biobank-specimens.tsv`](src/ontology/templates/biobank-specimens.tsv)
    - [`medical-history.tsv`](src/ontology/templates/medical-history.tsv) for medical history classifications and related selection criteria
    - [`study-designs.tsv`](src/ontology/templates/study-designs.tsv) for study designs
3. other terms: Edit [`src/ontology/obi-edit.owl`](src/ontology/obi-edit.owl) in Protege.

See below for a full list of files, build instructions, and instructions on using Git and GitHub for OBI.


# Files

- [`README.md`](README.md) this overview document
- [`obi.owl`](obi.owl) the latest release of OBI
- [`obi_core.owl`](obi_core.owl) the latest release of OBI Core: ~100 key terms
- [`Makefile`](Makefile) scripts for building OBI
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


# Building

The [`Makefile`](Makefile) contains scripts for building OBI. On macOS or Linux, you should just be able to run `make` or one of the specific tasks below. On Windows consider using some sort of Linux virtual machine such as Docker or Vagrant. Most results will be in the `build/` directory. If you have trouble, contact [James](mailto:james@overton.ca).

- `make all` prepare for a release
- `make obi.owl` build the release file; reasoning can take about 10 minutes
- `make imports` update OntoFox imports
- `make modules` update ROBOT templates
- `make build/obi_merged.owl` merge `obi-edit.owl` into a single file, don't reason
- `make clean` remove temporary files
- `make test` merge and run SPARQL tests
- `make check` check for bad line-endings (see below)
- `make fix` fix bad line-endings (see below)


# Development

We use git and GitHub to develop OBI. There's a lot of good documentation on both:

- git [website](https://git-scm.com) with files and documentation
- GitHub [Help](https://help.github.com) and [Flow](https://guides.github.com/introduction/flow/)
- [git command-line overview](http://dont-be-afraid-to-commit.readthedocs.io/en/latest/git/commandlinegit.html)


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
5. `git status` and `git diff` inspect your changes
6. `git add --update` add all updated files to staging
7. `git commit --message "Description, issue #123"` commit staged changes with a message; it's good to include an issue number
8. `git push --set-upstream origin your-branch-name` push your commit to GitHub
9. open <https://github.com/obi-ontology/obi> in your browser and click the "Make Pull Request" button

Your Pull Request will be automatically tested. If there are problems, we will update your branch. When all tests have passed, your PR can be merged into `master`. Rinse and repeat!


## Line endings

The easiest way to edit our `src/ontology/template/` files is with Excel. Unfortunately Excel on macOS [uses old line endings](http://developmentality.wordpress.com/2010/12/06/excel-2008-for-macs-csv-bug/), and this messes up our diffs. We've adopted [this solution](https://github.com/dfalster/baad/commit/1620ecbdede6feeab59bc1d0db3ff14824af5643).

If you're not using macOS or Excel, you should ignore these instructions.

Before you start using a new clone of the repository under macOS, please set up a git hook that checks for bad line endings before every commit. From the repository root, run:

    ln -s ../../src/scripts/check-line-endings.sh .git/hooks/pre-commit

This will check that all files have Unix endings once files have been staged (so after git's `crlf` treatment). You can run it manually to check by running

    src/scripts/check-line-endings.sh

which looks at staged files only, or

    src/scripts/check_line_endings.sh tsv

which looks at *all* tsv files in the project, including uncommitted, unstaged, ignored files, etc.

To *fix* line endings, run

    src/scripts/fix-eol.sh path/to/file.tsv

To fix *all* files in the project, run

    src/scripts/fix-eol-all.sh

which looks at all tsv files, regardless of git status, ending correctness, etc.

If you *really* need to override a pre-commit check, use git's `--no-verify` option.
