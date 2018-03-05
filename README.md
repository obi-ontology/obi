# Ontology for Biomedical Investigations

[![Build Status](https://travis-ci.org/obi-ontology/obi.svg?branch=master)](https://travis-ci.org/obi-ontology/obi)

More documentation coming soon!


# Development

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
