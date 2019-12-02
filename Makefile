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
build:
	mkdir -p $@


### ROBOT
#
# We use the official development version of ROBOT for most things.
build/robot.jar: | build
	curl -L -o $@ https://github.com/ontodev/robot/releases/download/v1.4.3/robot.jar

ROBOT := java -jar build/robot.jar

# ROBOT JAR with feature to remove foreign axioms
build/robot-test.jar: | build
	curl -Lk -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/foreign-ax/lastSuccessfulBuild/artifact/bin/robot.jar

ROBOT_TEST := java -jar build/robot-test.jar

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

obi.obo: obi.owl | build/robot.jar
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

obi_core.owl: obi.owl src/ontology/core.txt | build/robot.jar
	$(ROBOT) remove \
	--input $< \
	--term obo:OBI_0600036 \
	--term obo:OBI_0600037 \
	--term obo:OBI_0000838 \
	--select "self descendants" \
	--preserve-structure false \
	extract \
	--method STAR \
	--term-file src/ontology/core.txt \
	--individuals definitions \
	--copy-ontology-annotations true \
	annotate \
	--ontology-iri "$(OBO)/obi/obi_core.owl" \
	--version-iri "$(OBO)/obi/$(TODAY)/obi_core.owl" \
	--annotation owl:versionInfo "$(TODAY)" \
	--output $@

obi_base.owl: obi.owl | build/robot-test.jar
	$(ROBOT_TEST) remove \
	 --input $< \
	 --base-iri http://purl.obolibrary.org/obo/OBI_ \
	 --axioms external \
	annotate \
	 --ontology-iri "$(OBO)/obi/$@" \
	 --version-iri "$(OBO)/obi/$(TODAY)/$@" \
	 --annotation owl:versionInfo "$(TODAY)" \
	 --output $@


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

# Files to create pseudo-core
build/bfo-classes.owl:
	curl -Lk -o $@ http://purl.obolibrary.org/obo/bfo/classes.owl

build/ro-core.owl:
	curl -Lk -o $@ http://purl.obolibrary.org/obo/ro/core.owl

build/iao-metadata.owl:
	curl -Lk -o $@ http://purl.obolibrary.org/obo/iao/ontology-metadata.owl

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


.PHONY: verify-all
verify-all: verify verify-integration

# Run validation queries on obi-edit and exit on error.
.PHONY: verify-edit
verify-edit: src/ontology/obi-edit.owl $(EDIT_VIOLATION_QUERIES) | build/robot.jar

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
	@echo $(shell < $< wc -l) "OBI IRIs have been dropped"
	@! test -s $<

# Merge OBI base with BFO, RO, and IAO and reason with HermiT
# HermiT might not work on Travis so we don't include this in the Travis test
# If this fails with an OntologyLogicException, it creates a build/unsatisfiable.owl file
# All console output is logged in build/integration-log.txt
# Only run 'make explain' on failure
verify-integration: build/pseudo-core-plus-obi.owl
build/pseudo-core-plus-obi.owl: build/bfo-classes.owl build/ro-core.owl build/iao-metadata.owl obi_base.owl | build/robot.jar
	@echo "Running integration test (this may take a few minutes)..."
	@$(ROBOT) merge \
	 --input $< \
	 --input $(word 2,$^) \
	 --input $(word 3,$^) \
	 --input $(word 4,$^) \
	reason \
	 --reasoner HermiT \
	 --dump-unsatisfiable build/unsatisfiable.owl \
	 --output $@ > build/integration-log.txt \
	&& ([ $$? -eq 0 ] && echo "Integration test success!") \
	  || (echo "Integration test failed! See build/integration-log.txt for details." \
	      && make explain)

# Extract unsatisfiable classes from the log
# build/unsatisfiable.txt will be deleted if it is empty
extract-unsat: build/unsatisfiable.txt
build/unsatisfiable.txt: build/integration-log.txt
	@cat $< | sed -ne 's/.*unsatisfiable: \([^ ]*\)$$/\1/p' > $@
	@if [ ! -s $@ ] ; then \
	  rm $@; \
	fi

# Explain unsatisfiable - always fails so that 'make' exits with failure
.PHONY: explain
explain: extract-unsat | build/robot.jar
	@test -s build/unsatisfiable.txt \
	 || (echo "No unsatisfiable classes to explain." && false)
	@test -s build/unsatisfiable.owl \
	 || (echo "No unsatisfiable classes to explain." && false)
	@mkdir -p build/explain
	@while read line; do \
		FILE=`echo $$line | sed 's/.*obo\/\(.*\)$$/\1/'`; \
		echo "Creating explanation: build/explain/$$FILE.md"; \
		$(ROBOT) explain \
		 --input build/unsatisfiable.owl \
		 --axiom "$$line SubClassOf owl:Nothing" \
		 --reasoner HermiT \
		 --explanation build/explain/$$FILE.md; \
	done < build/unsatisfiable.txt && false

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
all:
	@echo "------------- RUNNING UNIT TESTS --------------"
	@make test 
	@echo ""
	@echo "---------- CREATING RELEASE PRODUCTS ----------"
	@make obi.owl obi_core.owl obi_base.owl 
	@echo ""
	@echo "------------------ REPORTING ------------------"
	@make build/terms-report.csv
	@echo ""
	@echo "---------- RUNNING INTEGRATION TEST -----------"
	@make verify-integration

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
