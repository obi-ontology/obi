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
TS      := $(shell date +'%d:%m:%Y %H:%M')

### Directories
#
# This is a temporary place to put things.
build build/views:
	mkdir -p $@


### ROBOT
#
# We use the official development version of ROBOT for most things.
build/robot.jar: | build
	curl -L -o $@ https://github.com/ontodev/robot/releases/download/v1.6.0/robot.jar

ROBOT := java -jar build/robot.jar --prefix "REO: http://purl.obolibrary.org/obo/REO_"


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
 devices\
 epitope-assays\
 medical-history\
 obsolete\
 organizations\
 study-designs\
 sequence-analysis\
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

views/obi.obo: obi.owl | build/robot.jar
	$(ROBOT) query \
	--input $< \
	--update src/sparql/obo-format.ru \
	remove \
	--select "parents equivalents" \
	--select "anonymous" \
	remove \
	--term-file src/scripts/remove-for-obo.txt \
	--trim true \
	annotate \
	--ontology-iri "$(OBO)/obi.obo" \
	--version-iri "$(OBO)/obi/$(TODAY)/obi.obo" \
	convert \
	--output $(basename $@)-temp.obo && \
	grep -v ^owl-axioms $(basename $@)-temp.obo | \
	grep -v ^date | \
	perl -lpe 'print "date: $(TS)" if $$. == 3'  > $@ && \
	rm $(basename $@)-temp.obo

views/obi_core.owl: obi.owl src/ontology/views/core.txt | build/robot.jar
	$(ROBOT) remove \
	--input $< \
	--term obo:OBI_0600036 \
	--term obo:OBI_0600037 \
	--term obo:OBI_0000838 \
	--select "self descendants" \
	--preserve-structure false \
	extract \
	--method STAR \
	--term-file $(word 2,$^) \
	--individuals definitions \
	--copy-ontology-annotations true \
	annotate \
	--ontology-iri "$(OBO)/obi/obi_core.owl" \
	--version-iri "$(OBO)/obi/$(TODAY)/obi_core.owl" \
	--annotation owl:versionInfo "$(TODAY)" \
	--output $@

build/views/NIAID-GSC-BRC.txt: src/ontology/views/NIAID-GSC-BRC.tsv | build/views
	tail -n+3 $< | cut -f1 > $@

views/NIAID-GSC-BRC.owl: obi.owl build/views/NIAID-GSC-BRC.txt src/ontology/views/NIAID-GSC-BRC.tsv | build/robot.jar
	$(ROBOT) extract \
	--input $< \
	--method STAR \
	--term-file $(word 2,$^) \
	--individuals definitions \
	--copy-ontology-annotations true \
	remove \
	--term IAO:0000233 \
	--term IAO:0000234 \
	--term IAO:0000589 \
	--term IAO:0010000 \
	--term OBI:0001847 \
	--term OBI:0001886 \
	--term OBI:9991118 \
	template \
	--template $(word 3,$^) \
	--merge-before \
	--output $@
	sed '/<obo:IAO_0000589/d' $@ | sed '/<dc:description/d' > $@.tmp.owl
	$(ROBOT) annotate \
	--input $@.tmp.owl \
	--ontology-iri "$(OBO)/obi/NIAID-GSC-BRC.owl" \
	--version-iri "$(OBO)/obi/$(TODAY)/NIAID-GSC-BRC.owl" \
	--annotation owl:versionInfo "$(TODAY)" \
	--language-annotation dc11:description "A subset of OBI containing all terms specified by the NIAID GSCID and BRC Project, Sample and Sequencing Assay Core Metadata Standards. This OBI view includes NIAID GSCID and BRC community preferred labels and field IDs specified in the standards (https://www.niaid.nih.gov/research/human-pathogen-and-vector-sequencing-metadata-standards)." en \
	--output $@
	rm $@.tmp.owl


### Test
#
# Run main tests
MERGED_VIOLATION_QUERIES := $(wildcard src/sparql/*-violation.rq) 
MODULE_VIOLATION_QUERIES := $(wildcard src/sparql/*-violation-modules.rq)
PHONY_MODULES := $(foreach x,$(MODULE_NAMES),build/modules/$(x).owl)

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

# Directory for phony modules
build/modules:
	mkdir -p build/modules

# Remove all annotation properties from modules
build/modules/%.owl: src/ontology/modules/%.owl | build/robot.jar
	$(ROBOT) remove --input $< --select annotation-properties --output $@

# Build OBI edit + modules without annotation properties
build/modules/merged.owl: src/ontology/obi-edit.owl $(PHONY_MODULES) | build/robot.jar
	$(eval INPUTS := $(foreach x,$(PHONY_MODULES),--input $(x) ))
	$(ROBOT) remove --input $< --select imports \
	merge $(INPUTS) \
	reason --output $@

# Run all validation queries and exit on error.
.PHONY: verify
verify: verify-modules verify-merged verify-entities

# Run validation queries on merged modules and exit on error.
.PHONY: verify-modules
verify-modules: build/modules/merged.owl $(MODULE_VIOLATION_QUERIES) | build/robot.jar
	$(ROBOT) verify --input $< --output-dir build \
	--queries $(MODULE_VIOLATION_QUERIES)

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

# Run a basic reasoner to find inconsistencies
.PHONY: reason
reason: build/obi_merged.owl | build/robot.jar
	$(ROBOT) reason --input $< --reasoner ELK

.PHONY: test
test: reason verify


### General
#
# Full build
.PHONY: all
all: test obi.owl views/obi.obo views/obi_core.owl views/NIAID-GSC-BRC.owl build/terms-report.csv

# Remove generated files
.PHONY: clean
clean:
	rm -rf build

# Sort template tables, standardize quoting and line endings
.PHONY: sort
sort: src/ontology/templates/
	src/scripts/sort-templates.py
