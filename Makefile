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
	curl -L -o $@ https://github.com/ontodev/robot/releases/download/v1.9.4/robot.jar

ROBOT := java -jar build/robot.jar --prefix "REO: http://purl.obolibrary.org/obo/REO_"


### RDFTab
#
# Use RDFTab to create SQLite databases from OWL files.
UNAME := $(shell uname)
ifeq ($(UNAME), Darwin)
	RDFTAB_URL := https://github.com/ontodev/rdftab.rs/releases/download/v0.1.1/rdftab-x86_64-apple-darwin
	SED = sed -i.bak
else
	RDFTAB_URL := https://github.com/ontodev/rdftab.rs/releases/download/v0.1.1/rdftab-x86_64-unknown-linux-musl
	SED = sed -i
endif

build/rdftab: | build
	curl -L -o $@ $(RDFTAB_URL)
	chmod +x $@


### Imports
#
# Use Ontofox to import various modules.
build/%_imports.owl: src/ontology/OntoFox_inputs/%_input.txt | build
	curl -s -F file=@$< -o $@ https://ontofox.hegroup.org/service.php

# Remove annotation properties from CLO to avoid weird labels.
src/ontology/OntoFox_outputs/CLO_imports.owl: build/CLO_imports.owl
	$(ROBOT) remove --input $< --select annotation-properties --trim false --output $@

# Use ROBOT to ensure that serialization is consistent for the rest.
src/ontology/OntoFox_outputs/%_imports.owl: build/%_imports.owl
	$(ROBOT) convert -i build/$*_imports.owl -o $@

IMPORT_FILES := $(wildcard src/ontology/*_outputs/*_imports.owl)

.PHONY: imports
imports: $(IMPORT_FILES)

build/%_import_source.owl:
	curl -sL http://purl.obolibrary.org/obo/$*.owl -o $@

build/%_edit_module.owl: src/ontology/robot_inputs/%_edit.tsv
	echo "" > $@
	robot merge \
	--input src/ontology/obi-edit.owl \
	template \
	--template $< \
	annotate \
	--ontology-iri "http://purl.obolibrary.org/obo/obi/dev/import/Uberon_edit.owl" \
	--output $@

src/ontology/robot_outputs/Uberon_imports.owl: build/Uberon_import_source.owl src/ontology/robot_inputs/Uberon_input.txt src/ontology/robot_inputs/Uberon_remove.txt build/Uberon_edit_module.owl
	$(ROBOT) extract --method MIREOT --input $< \
	--upper-term UBERON:0000465 \
	--lower-terms $(word 2,$^) \
	--intermediates minimal \
	export --header IRI \
	--export build/mireot_Uberon.txt
	robot extract --method subset --input $< \
	--term-file build/mireot_Uberon.txt \
	--term BFO:0000050 \
	--term BFO:0000051 \
	remove --term-file $(word 3,$^) \
	reduce --reasoner ELK \
	merge --input $(word 4,$^) \
	annotate --ontology-iri "http://purl.obolibrary/org/obo/obi/dev/import/Uberon_imports.owl" \
	convert -o $@



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
MODULE_NAMES := administration\
 antibody-purification\
 assays\
 biopsy\
 specimens\
 organizations\
 data-sets\
 data-transformations\
 devices\
 epitope-assays\
 investigations\
 medical-history\
 obsolete\
 physical-examination\
 sample-collection\
 study-designs\
 sequence-analysis\
 specimen-assay-data\
 value-specifications
MODULE_FILES := $(foreach x,$(MODULE_NAMES),src/ontology/modules/$(x).owl)
TEMPLATE_FILES := $(foreach x,$(MODULE_NAMES),src/ontology/templates/$(x).tsv)

.PHONY: modules
modules: $(MODULE_FILES)

obi.xlsx: src/scripts/tsv2xlsx.py $(TEMPLATE_FILES)
	python3 $< $@ $(wordlist 2,100,$^)

.PHONY: update-tsv
update-tsv: update-tsv-files sort

.PHONY: update-tsv-files
update-tsv-files:
	$(foreach x,$(MODULE_NAMES),python3 src/scripts/xlsx2tsv.py obi.xlsx $(x) src/ontology/templates/$(x).tsv;)



### Databases

.PHONY: obi-dbs
obi-dbs: build/obi-edit.db build/obi_merged.db

build/obi-edit.db: src/scripts/prefixes.sql src/ontology/obi-edit.owl | build/rdftab
	rm -rf $@
	sqlite3 $@ < $<
	./build/rdftab $@ < $(word 2,$^)
	sqlite3 $@ "CREATE INDEX idx_stanza ON statements (stanza);"
	sqlite3 $@ "ANALYZE;"

build/obi_merged.db: src/scripts/prefixes.sql build/obi_merged.owl | build/rdftab
	rm -rf $@
	sqlite3 $@ < $<
	./build/rdftab $@ < $(word 2,$^)
	sqlite3 $@ "CREATE INDEX idx_stanza ON statements (stanza);"
	sqlite3 $@ "ANALYZE;"


### Build
#
# Here we create a standalone OWL file appropriate for release.
# This involves merging, reasoning, annotating,
# and removing any remaining import declarations.
build/obi_merged.owl: src/ontology/obi-edit.owl $(MODULE_FILES) src/sparql/*-construct.rq src/sparql/fix-iao.rq | build/robot.jar build
	$(ROBOT) merge \
	--input $< \
	query \
	--format TTL \
	--construct src/sparql/add-editor-preferred-term-construct.rq build/editor-preferred-terms.ttl \
	--construct src/sparql/add-curation-status-construct.rq build/curation-status.ttl \
	merge \
	--input build/editor-preferred-terms.ttl \
	--input build/curation-status.ttl \
	query \
	--update src/sparql/fix-iao.rq \
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
	--equivalent-classes-allowed none \
	annotate \
	--ontology-iri "$(OBO)/obi.owl" \
	--version-iri "$(OBO)/obi/$(TODAY)/obi.owl" \
	--annotation owl:versionInfo "$(TODAY)" \
	--output $@

# Build a base file from obi-edit.owl and modules.
views/obi-base.owl: src/ontology/obi-edit.owl $(MODULE_FILES) | build/robot.jar
	$(ROBOT) remove --input $< \
	--select imports \
	merge $(foreach M,$(MODULE_FILES), --input $(M)) \
	annotate \
	--ontology-iri "$(OBO)/obi/obi-base.owl" \
	--version-iri "$(OBO)/obi/$(TODAY)/obi-base.owl" \
	--annotation owl:versionInfo "$(TODAY)" \
	--output $@

views/obi.obo: obi.owl src/scripts/remove-for-obo.txt | build/robot.jar
	$(ROBOT) query \
	--input $< \
	--update src/sparql/obo-format.ru \
	remove \
	--select "parents equivalents" \
	--select "anonymous" \
	remove \
	--term-file $(word 2,$^) \
	--trim true \
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
	--term obo:OBI_0003071 \
	--term APOLLO_SV:00000796 \
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

.PHONY: views
views: views/obi.obo views/obi-base.owl views/obi_core.owl views/NIAID-GSC-BRC.owl


### Test
#
# Run main tests
MERGED_VIOLATION_QUERIES := $(wildcard src/sparql/*-violation.rq) 
MODULE_VIOLATION_QUERIES := $(wildcard src/sparql/*-violation-modules.rq)
PHONY_MODULES := $(foreach x,$(MODULE_NAMES),build/modules/$(x).owl)

build/obi-base-report.tsv: views/obi-base.owl
	$(ROBOT) report \
	--input $< \
	--labels true \
	--base-iri "http://purl.obolibrary.org/obo/OBI_" \
	--fail-on ERROR \
	--print 10 \
	--output $@

build/terms-report.csv: build/obi_merged.owl src/sparql/terms-report.rq | build
	$(ROBOT) query --input $< --select $(word 2,$^) $@

# Always get the most recent version of OBI - in case build directory has not been cleaned
.PHONY: build/obi-previous-release.owl
build/obi-previous-release.owl: | build
	curl -L -o $@ "http://purl.obolibrary.org/obo/obi.owl"

build/released-entities.tsv: build/obi-previous-release.owl src/sparql/get-obi-entities.rq | build/robot.jar
	$(ROBOT) query --input $< --select $(word 2,$^) $@

build/current-entities.tsv: build/obi_merged.owl src/sparql/get-obi-entities.rq | build/robot.jar
	$(ROBOT) query --input $< --select $(word 2,$^) $@

build/terms-report.tsv: build/obi_merged.owl src/sparql/terms-report.rq | build
	$(ROBOT) query --input $< --select $(word 2,$^) $@
	mv $@ $@.tmp
	tail -n+2 $@.tmp | cut -f1,3 | sort -u > $@
	rm $@.tmp

build/new-entities.txt: build/released-entities.tsv build/current-entities.tsv build/terms-report.tsv
	echo "New terms added:" > $@
	echo "" >> $@
	echo "ID | Label" >> $@
	echo "---|---" >> $@
	comm -13 $(wordlist 1,2,$^) \
	| join - $(word 3,$^) \
	| sed "s|^<http://purl.obolibrary.org/obo/OBI_|OBI:|" \
	| sed s/\"//g \
	| sed "s/>//g" \
	| sed "s/@en//g" \
	| sed "s/ /|/" \
	>> $@

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
	reason --equivalent-classes-allowed none \
	--output $@

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
	$(ROBOT) reason --input $< --reasoner ELK --equivalent-classes-allowed none

# Find any IRIs using undefined namespaces
.PHONY: validate-iris
validate-iris: src/scripts/validate-iris.py build/obi_merged.owl
	$^

.PHONY: validate-dl
validate-dl: build/dl-validation.txt
.PRECIOUS: build/dl-validation.txt
build/dl-validation.txt: build/obi_merged.owl
	$(ROBOT) validate-profile --input $< --profile dl --output $@

.PHONY: test
test: reason verify validate-iris validate-dl build/obi-base-report.tsv


### Term reservations
#
# Get current OBI terms
build/obi-terms.tsv: build/obi_merged.owl
	$(ROBOT) export --input $< --header "ID|LABEL" --export $@

# Get the term reservation table
build/reservations.tsv: | build
	curl -Lk "https://docs.google.com/spreadsheets/d/1tpDrSiO1DlEqkvZjrDSJrMm7OvH9GletljaR-SDeMTI/export?format=tsv&id=1tpDrSiO1DlEqkvZjrDSJrMm7OvH9GletljaR-SDeMTI&gid=224833299" > $@

# Create an updated reservation table
build/reservations-updated.tsv: src/scripts/update-term-reservations.py build/reservations.tsv build/obi-terms.tsv
	python3 $^ $@

### General
#
# Full build
.PHONY: all
all: test obi.owl views build/terms-report.csv

# Remove generated files
.PHONY: clean
clean:
	rm -rf build

# Sort template tables, standardize quoting and line endings
.PHONY: sort
sort: src/ontology/templates/
	src/scripts/sort-templates.py

### GitHub Tasks
#
# Require "admin:org", "repo", and "workflow" permissions for gh CLI token

# Create a release candidate
.PHONY: candidate
candidate: obi.owl views build/new-entities.txt
	src/scripts/release-candidate.sh

# Create a release
.PHONY: release
release: build/new-entities.txt
	src/scripts/release.sh
