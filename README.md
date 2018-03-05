# Ontology for Biomedical Investigations

[![Build Status](https://travis-ci.org/obi-ontology/obi.svg?branch=master)](https://travis-ci.org/obi-ontology/obi)


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

Start from a local copy of the `master` branch of the OBI repository. Make sure your local copy is up-to-date. Make your changes on a new branch. When you're ready, push your branch to the OBI repository and make a Pull Request (PR) on the GitHub website. Your PR is a request to merge your branch back into `master`. Your PR will be tested, discussed, adjusted if necessary, then merged. Then the cycle can repeat for the next change that you or another developer will make.

These are the steps with their CLI commands. When using a GUI application the steps will be the same.

1. `git fetch` -- make sure your local copy is up-to-date
2. `git checkout master` -- start on the `master` branch
3. `git checkout -b your-branch-name` -- create a new branch named for the change you're making
4. make your changes
5. `git status` and `git diff` -- inspect your changes
6. `git add --update` -- add all updated files to staging
7. `git commit --message "Desciption, issue #123"` -- commit staged changes with a message; it's good to include an issue number
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
