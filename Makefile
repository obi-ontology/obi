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
TODAY   := $(shell date +%Y-%m-%d)

### Directories
#
# This is a temporary place to put things.
build:
	mkdir -p $@


### ROBOT
#
# We use a forked version of ROBOT for builds.
# TODO: Switch to official version.
build/robot.jar: | build
	curl -L -o $@ https://github.com/jamesaoverton/rogue-robot/releases/download/0.0.1/robot.jar

ROBOT := java -jar build/robot.jar


### Imports
#
# Use Ontofox to import various modules.
src/ontology/OntoFox_outputs/%_imports.owl: src/ontology/OntoFox_inputs/%_input.txt
	curl -s -F file=@$< -o $@ http://ontofox.hegroup.org/service.php

IMPORT_FILES := $(wildcard src/ontology/OntoFox_outputs/*_imports.owl)

.PHONY: imports
imports: $(IMPORT_FILES)


### Templates
#
# The `src/ontology/templates/` directory contains spreadsheets
# used to generate OWL files with ROBOT.
# The first step is to erase any contents of the module OWL file.
# See https://github.com/ontodev/robot/blob/master/docs/template.md
src/ontology/modules/%.owl: src/ontology/templates/%.tsv | build/robot.jar
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
MODULE_NAMES := obsolete biobank-specimens assays midlevel-assays epitope-assays
MODULE_FILES := $(foreach x,$(MODULE_NAMES),src/ontology/modules/$(x).owl)

.PHONY: modules
modules: $(MODULE_FILES)


### Build
#
# Here we create a standalone OWL file appropriate for release.
# This involves merging, reasoning, annotating,
# and removing any remaining import declarations.
build/obi_merged.owl: src/ontology/obi-edit.owl $(MODULE_FILES) src/sparql/*-construct.rq | build/robot.jar build
	$(ROBOT) merge \
	--input $< \
	query \
	--format TTL \
	--construct src/sparql/add-editor-preferred-term-construct.rq build/editor-preferred-terms.ttl \
	--construct src/sparql/add-curation-status-construct.rq build/curation-status.ttl \
	merge \
	--input build/editor-preferred-terms.ttl \
	--input build/curation-status.ttl \
	annotate \
	--ontology-iri "$(OBO)/obi/obi_merged.owl" \
	--version-iri "$(OBO)/obi/$(TODAY)/obi_merged.owl" \
	--annotation owl:versionInfo "$(TODAY)" \
	--output build/obi_merged.tmp.owl
	sed '/<owl:imports/d' build/obi_merged.tmp.owl > $@
	rm build/obi_merged.tmp.owl

obi.owl: build/obi_merged.owl
	$(ROBOT) reason \
	--input $< \
	--reasoner HermiT \
	annotate \
	--ontology-iri "$(OBO)/obi.owl" \
	--version-iri "$(OBO)/obi/$(TODAY)/obi.owl" \
	--annotation owl:versionInfo "$(TODAY)" \
	--output $@

obi_core.owl: obi.owl src/ontology/core.txt
	$(ROBOT) extract \
	--input $< \
	--method STAR \
	--term-file src/ontology/core.txt \
	--strip-term obo:CL_0000010 \
	--strip-term obo:CL_0000001 \
	--strip-term obo:OBI_0001866 \
	--strip-term obo:CLO_0000001 \
	--copy-annotations \
	annotate \
	--ontology-iri "$(OBO)/obi/obi_core.owl" \
	--version-iri "$(OBO)/obi/$(TODAY)/obi_core.owl" \
	--annotation owl:versionInfo "$(TODAY)" \
	--output $@


### Test
#
# Run main tests
VIOLATION_QUERIES := $(wildcard src/sparql/*-violation.rq)

build/terms-report.csv: build/obi_merged.owl src/sparql/terms-report.rq | build
	$(ROBOT) merge \
	--input $< \
	query \
	--select src/sparql/terms-report.rq build/terms-report.csv

# Run validation queries and exit on error.
.PHONY: verify
verify: build/obi_merged.owl $(VIOLATION_QUERIES) | build
	$(ROBOT) merge \
	--input $< \
	verify \
	--report-dir build \
	--queries $(VIOLATION_QUERIES)

.PHONY: test
test: verify


### General
#
# Full build
.PHONY: all
all: obi.owl obi_core.owl build/terms-report.csv

# Remove generated files
.PHONY: clean
clean:
	rm -rf build
