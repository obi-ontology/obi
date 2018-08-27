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
# We use the official development version of ROBOT for most things.
build/robot.jar: | build
	curl -L -o $@ https://github.com/ontodev/robot/releases/download/v1.1.0/robot.jar

ROBOT := java -jar build/robot.jar

# We use a forked version of ROBOT for generating obi_core.owl
# TODO: Switch to official version for all tasks
build/rogue-robot.jar: | build
	curl -L -o $@ https://github.com/jamesaoverton/rogue-robot/releases/download/0.0.1/robot.jar

ROGUE_ROBOT := java -jar build/rogue-robot.jar


### Imports
#
# Use Ontofox to import various modules.
build/%_imports.owl: src/ontology/OntoFox_inputs/%_input.txt | build
	curl -s -F file=@$< -o $@ http://ontofox.hegroup.org/service.php

# Use ROBOT to ensure that serialization is consistent.
src/ontology/OntoFox_outputs/%_imports.owl: build/%_imports.owl
	$(ROBOT) convert -i build/$*_imports.owl -o $@

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
MODULE_NAMES := assays\
 biobank-specimens\
 epitope-assays\
 medical-history\
 obsolete\
 study-designs\
 value-specifications
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

obi_core.owl: obi.owl src/ontology/core.txt | build/rogue-robot.jar
	$(ROGUE_ROBOT) extract \
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
MERGED_VIOLATION_QUERIES := $(wildcard src/sparql/*-violation.rq)
EDIT_VIOLATION_QUERIES := $(wildcard src/sparql/*-violation-edit.rq)

build/terms-report.csv: build/obi_merged.owl src/sparql/terms-report.rq | build
	$(ROBOT) query --input $< --select $(word 2,$^) $@

build/obi-previous-release.owl: | build
	curl -L -o $@ "http://purl.obolibrary.org/obo/obi.owl"

build/released-entities.tsv: build/obi-previous-release.owl src/sparql/get-obi-entities.rq | build/robot.jar
	$(ROBOT) query --input $< --select $(word 2,$^) $@

build/current-entities.tsv: build/obi_merged.owl src/sparql/get-obi-entities.rq | build/robot.jar
	$(ROBOT) query --input $< --select $(word 2,$^) $@

build/dropped-entities.tsv: build/released-entities.tsv build/current-entities.tsv
	comm -23 $^ > $@

# Run all validation queries and exit on error.
.PHONY: verify
verify: verify-edit verify-merged verify-entities

# Run validation queries on obi-edit and exit on error.
.PHONY: verify-edit
verify-edit: src/ontology/obi-edit.owl $(EDIT_VIOLATION_QUERIES) | build/robot.jar
	$(ROBOT) verify --input $< --output-dir build \
	--queries $(EDIT_VIOLATION_QUERIES)

# Run validation queries on obi_merged and exit on error.
.PHONY: verify-merged
verify-merged: build/obi_merged.owl $(MERGED_VIOLATION_QUERIES) | build/robot.jar
	$(ROBOT) verify --input $< --output-dir build \
	--queries $(MERGED_VIOLATION_QUERIES)

# Check if any entities have been dropped and exit on error.
.PHONY: verify-entities
verify-entities: build/dropped-entities.tsv
	@echo $(shell < $< wc -l) " OBI IRIs have been dropped"
	@! test -s $<


.PHONY: test
test: verify


### General
#
# Full build
.PHONY: all
all: test obi.owl obi_core.owl build/terms-report.csv

# Remove generated files
.PHONY: clean
clean:
	rm -rf build

# Check for problems such as bad line-endings
.PHONY: check
check:
	src/scripts/check-line-endings.sh tsv

# Fix simple problems such as bad line-endings
.PHONY: fix
fix:
	src/scripts/fix-eol-all.sh
