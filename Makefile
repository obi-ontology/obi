# OBI Makefile
# James A. Overton <james@overton.ca>
#
# This Makefile is used to build artifacts
# for the Ontology for Biomedical Investigations.
#
# WARN: This file contains significant whitespace, i.e. tabs!
# Ensure that your text editor shows you those characters.

### Configuration
#
# These are standard options to make Make sane:
# <http://clarkgrubb.com/makefile-style-guide#toc2>

MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.SUFFIXES:
.SECONDARY:

### Definitions

SHELL   := /bin/bash
OBO     := http://purl.obolibrary.org/obo
OBI     := $(OBO)/OBI_
DEV     := $(OBO)/obi/dev
MODULES := $(DEV)/modules


### ROBOT
#
# We use a forked version of ROBOT for builds.
# TODO: Switch to official version.
robot.jar:
	curl -LO https://github.com/jamesaoverton/rogue-robot/releases/download/0.0.1/robot.jar

ROBOT := java -jar robot.jar


### Templates
#
# The `src/ontology/templates/` directory contains spreadsheets
# used to generate OWL files with ROBOT.
# The first step is to erase any contents of the module OWL file.
# See https://github.com/ontodev/robot/blob/master/docs/template.md
src/ontology/modules/%.owl: src/ontology/templates/%.tsv | robot.jar
	echo '' > $@
	$(ROBOT) merge \
	--input src/ontology/obi-edit.owl \
	template \
	--template $< \
	annotate \
	--ontology-iri "$(MODULES)/$(notdir $@)" \
	--output $@

# Update all modules.
# NOTE: GNU Make will compare timestamps to see which updates are required.
MODULE_NAMES := obsolete biobank-specimens midlevel-assays epitope-assays
MODULE_FILES := $(foreach x,$(MODULE_NAMES),src/ontology/modules/$(x).owl)

.PHONY: modules
modules: $(MODULE_FILES)


### Build
#
# Here we create a standalone OWL file appropriate for release.
# This involves merging, reasoning, annotating,
# and removing any remaining import declarations.
build:
	mkdir -p build/

obi.owl: src/ontology/obi-edit.owl $(MODULE_FILES)
	$(ROBOT) merge \
	--input $< \
	annotate \
	--ontology-iri "$(OBO)/obi.owl" \
	--version-iri "$(OBO)/obi/$(shell date +%Y-%m-%d)/obi.owl" \
	--annotation owl:versionInfo "$(shell date +%Y-%m-%d)" \
	reason \
	--reasoner HermiT \
	--output tmp.owl
	sed '/<owl:imports/d' tmp.owl > $@
	rm tmp.owl

obi_core.owl: obi.owl src/ontology/core.txt
	$(ROBOT) extract \
	--input obi.owl \
	--method STAR \
	--term-file src/ontology/core.txt \
	--strip-term obo:CL_0000010 \
	--strip-term obo:CL_0000001 \
	--strip-term obo:OBI_0001866 \
	--strip-term obo:CLO_0000001 \
	--copy-annotations \
	--output obi_core.owl


### Test
#
# Run main tests
VIOLATION_QUERIES := $(wildcard src/sparql/*-violation.rq)

reports:
	mkdir -p reports/

# Run validation queries and exit on error.
.PHONY: verify
verify: src/ontology/obi-edit.owl modules $(VIOLATION_QUERIES) | robot.jar reports
	$(ROBOT) merge \
	--input $< \
	verify \
	--report-dir reports \
	--queries $(VIOLATION_QUERIES)

.PHONY: test
test: verify


### General
#
# Full build
.PHONY: all
all: obi.owl obi_core.owl

# Remove generated files
.PHONY: clean
clean:
	rm -rf robot.jar reports
