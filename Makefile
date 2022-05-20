# OBI Makefile
# James A. Overton <james@overton.ca>
#
# This Makefile is used to build artifacts
# for the Ontology for Biomedical Investigations.
#
# WARN: This file contains significant whitespace, i.e. tabs!
# Ensure that your text editor shows you those characters.

### Workflow
#
# **Setup**
# 1. [Build database](build/obi-tables.db)
# 2. [Load OBI](load_obi)
# 3. [Load imports](load_imports)
#
# ** Template Workflow** 
# 1. [View prototype](./src/scripts/run.py)
# 2. [Update templates](update_templates)
# 3. [Rebuild OBI](load_obi)
#
# **Import Workflow**
# 1. [Update import table](update_import)
# 2. Select your import module from the list below to rebuild, then [rebuild OBI](load_obi)
#
# Import modules:
# - [ChEBI](src/ontology/imports/chebi_imports.owl)
# - [CL](src/ontology/imports/cl_imports.owl)
# - [CLO](src/ontology/imports/clo_imports.owl)
# - [COB](src/ontology/imports/chebi_imports.owl)
# - [EnVO](src/ontology/imports/chebi_imports.owl)
# - [GO](src/ontology/imports/chebi_imports.owl)
# - [HP](src/ontology/imports/chebi_imports.owl)
# - [IDO](src/ontology/imports/chebi_imports.owl)
# - [NCBITaxon](src/ontology/imports/chebi_imports.owl)
# - [OGMS](src/ontology/imports/chebi_imports.owl)
# - [OMIABIS](src/ontology/imports/chebi_imports.owl)
# - [OMRSE](src/ontology/imports/chebi_imports.owl)
# - [OPL](src/ontology/imports/chebi_imports.owl)
# - [PATO](src/ontology/imports/chebi_imports.owl)
# - [PR](src/ontology/imports/chebi_imports.owl)
# - [SO](src/ontology/imports/chebi_imports.owl)
# - [Uberon](src/ontology/imports/chebi_imports.owl)
# - [UO](src/ontology/imports/chebi_imports.owl)
# - [VO](src/ontology/imports/chebi_imports.owl)
#

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

define \n


endef

### Directories
#
# This is a temporary place to put things.
build build/views build/templates build/imports:
	mkdir -p $@


### ROBOT
#
# We use the official development version of ROBOT for most things.
build/robot.jar: | build
	curl -L -o $@ https://github.com/ontodev/robot/releases/download/v1.8.3/robot.jar

ROBOT := java -jar build/robot.jar --prefix "REO: http://purl.obolibrary.org/obo/REO_"


### LDTab
#
# Use LDTab to create SQLite databases from OWL files.
build/ldtab.jar: | build
	curl -L -o $@ "https://github.com/ontodev/ldtab.clj/releases/download/v2022-03-17/ldtab.jar"

LDTAB := java -jar build/ldtab.jar


### Imports
#
# We use gadget (https://github.com/ontodev/gadget) to create various import modules.
# Currently excluding ChEBI, NCBITaxon, and PR due to memory constraints with LDTab
IMPORTS := $(filter-out chebi ncbitaxon pr imports,$(shell tail -n +2 src/ontology/imports/import_config.tsv | awk '{print $$1}' | uniq))
IMPORT_FILES := $(foreach I,$(IMPORTS),src/ontology/imports/$(I)_imports.owl)

# Get CLO in correct RDFXML format.
build/clo.owl.gz: | build/robot.jar
	$(ROBOT) convert --input-iri "$(OBO)/clo.owl" --output build/clo.owl
	gzip build/clo.owl

# Download compressed ChEBI to save some time.
build/chebi.owl.gz: | build
	curl -Lk "http://purl.obolibrary.org/obo/$(notdir $@)" > $@

# Download compressed NCBITaxon to save some time (we have to get the URL from the latest release).
build/ncbitaxon.owl.gz: | build
	$(eval URL = $(shell curl -s https://api.github.com/repos/obophenotype/ncbitaxon/releases/latest | jq --raw-output '.assets[5] | .browser_download_url'))
	curl -Lk $(URL) > $@

# Download the rest of the source ontologies.
build/%.owl.gz: | build
	curl -Lk "http://purl.obolibrary.org/obo/$*.owl" | gzip > $@

# Create UO database, deleting owl:Class declarations on owl:NamedIndividuals.
build/imports/uo.db: build/uo.owl.gz src/prefix.tsv | build/ldtab.jar
	rm -rf $@
	sqlite3 $@ "CREATE TABLE prefix (prefix TEXT NOT NULL, base TEXT NOT NULL);"
	$(LDTAB) prefix $@ $(word 2,$^)
	gunzip $<
	sqlite3 $@ "CREATE TABLE uo (\
	            assertion INT NOT NULL, \
	            retraction INT NOT NULL DEFAULT 0, \
	            graph TEXT NOT NULL, \
	            subject TEXT NOT NULL, \
	            predicate TEXT, \
	            object TEXT NOT NULL, \
	            datatype TEXT NOT NULL, \
	            annotation TEXT);" || { gzip $(basename $<); exit 1; }
	$(LDTAB) import --table uo $@ $(basename $<) || { gzip $(basename $<); exit 1; }
	sqlite3 $@ "DELETE FROM uo WHERE ROWID IN \
	  (SELECT s1.ROWID FROM uo s1 JOIN uo s2 ON s1.subject = s2.subject \
	   WHERE s1.object = 'owl:Class' AND s2.object = 'owl:NamedIndividual');" || { gzip $(basename $<); exit 1; }
	gzip $(basename $<)

# Create the rest of the databases.
build/imports/%.db: build/%.owl.gz src/prefix.tsv | build/ldtab.jar
	rm -rf $@
	sqlite3 $@ "CREATE TABLE prefix (prefix TEXT NOT NULL, base TEXT NOT NULL);"
	$(LDTAB) prefix $@ $(word 2,$^)
	gunzip $<
	sqlite3 $@ "CREATE TABLE $* (\
	            assertion INT NOT NULL, \
	            retraction INT NOT NULL DEFAULT 0, \
	            graph TEXT NOT NULL, \
	            subject TEXT NOT NULL, \
	            predicate TEXT, \
	            object TEXT NOT NULL, \
	            datatype TEXT, \
	            annotation TEXT);" || { gzip $(basename $<); exit 1; }
	$(LDTAB) import --table $* $@ $(basename $<) || { gzip $(basename $<); exit 1; }
	gzip $(basename $<)

# Extract NCBITaxon with oio:hasExactSynonym mapped to IAO:0000118.
.PHONY: build/ncbitaxon_imports.ttl
build/ncbitaxon_imports.ttl: build/imports/ncbitaxon.db | src/ontology/imports/import_config.tsv src/ontology/imports/import.tsv
	python3 -m gadget.extract \
	--database $< \
	--statement ncbitaxon \
	--config src/ontology/imports/import_config.tsv \
	--imports src/ontology/imports/import.tsv \
	--copy rdfs:label IAO:0000111 \
	--copy oio:hasExactSynonym IAO:0000118 \
	--source ncbitaxon > $@
	rm -f $@ && $(LDTAB) export -t extract $< $@

# Extract the terms and copy rdfs:label to 'editor preferred term' for the rest.
.PHONY: import-ttl
import-ttl:
build/%_imports.ttl: build/imports/%.db import-ttl | src/ontology/imports/import_config.tsv src/ontology/imports/import.tsv
	python3 -m gadget.extract \
	--database $< \
	--statement $* \
	--config src/ontology/imports/import_config.tsv \
	--imports src/ontology/imports/import.tsv \
	--copy rdfs:label IAO:0000111 \
	--source $*
	rm -f $@ && $(LDTAB) export -t extract $< $@

# Remove extra intermediate classes from NCBITaxon using 'robot collapse'.
build/ncbitaxon_terms.txt: src/ontology/imports/import.tsv
	grep "^ncbitaxon" $< | awk '{print $$2}' > $@

src/ontology/imports/ncbitaxon_imports.owl: build/ncbitaxon_imports.ttl build/ncbitaxon_terms.txt | build/robot.jar
	$(ROBOT) collapse \
	--input $< \
	--precious-terms $(word 2,$^) \
	--threshold 2 \
	annotate \
	--ontology-iri "$(OBO)/obi/dev/import/$(notdir $@)" \
	--output $@

# Add the IRI and convert to OWL format for the rest.
src/ontology/imports/%_imports.owl: build/%_imports.ttl | build/robot.jar
	$(ROBOT) annotate \
	--input $< \
	--ontology-iri "$(OBO)/obi/dev/import/$(notdir $@)" \
	--output $@

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
 biopsy\
 biobank-specimens\
 organizations\
 devices\
 epitope-assays\
 medical-history\
 obsolete\
 sample-collection\
 study-designs\
 sequence-analysis\
 specimen-assay-data\
 value-specifications
MODULE_FILES := $(foreach x,$(MODULE_NAMES),src/ontology/modules/$(x).owl)
TEMPLATE_FILES := $(foreach x,$(MODULE_NAMES),src/ontology/templates/$(x).tsv)

.PHONY: modules
modules: $(MODULE_FILES)

obi.xlsx: src/scripts/tsv2xlsx.py $(TEMPLATE_FILES) src/ontology/imports/import.tsv
	python3 $< $@ $(wordlist 2,100,$^)

.PHONY: update-tsv
update-tsv: update-tsv-files sort

.PHONY: update-tsv-files
update-tsv-files: src/scripts/xlsx2tsv.py
	$(foreach x,$(MODULE_NAMES),python3 src/scripts/xlsx2tsv.py obi.xlsx $(x) src/ontology/templates/$(x).tsv;)
	python3 src/scripts/xlsx2tsv.py obi.xlsx import src/ontology/imports/import.tsv

# Index containing ID, label, and table for all terms
# TODO: add imports
build/index.tsv: $(TEMPLATE_FILES) src/ontology/imports/import.tsv | build
	echo -e "ID\tlabel\ttable" >> $@
	$(foreach f,$(TEMPLATE_FILES),tail -n +3 $(f) | cut -f1,2 | sed -e 's/$$/\t$(subst -,_,$(notdir $(basename $(f))))/' >> $@${\n})
	tail -n +2 src/ontology/imports/import.tsv | cut -f2,3 | sed -e 's/$$/\timport/' >> $@

### Databases

# The SQL inputs are the templates without the ROBOT template strings
SQL_INPUTS = $(foreach t,$(MODULE_NAMES),build/templates/$(t).tsv)
build/templates/%.tsv: src/ontology/templates/%.tsv | build/templates
	sed '2d' $< > $@

# Load all tables into SQLite database
build/obi-tables.db: src/table.tsv src/column.tsv src/datatype.tsv src/prefix.tsv build/index.tsv $(SQL_INPUTS)
	python3 -m cmi_pb_script.load $< $@ > $(basename $@).sql

# Then add OBI using LDTab
# We use a version of OBI created with ELK reasoner to save time
.PHONY: load_obi
load_obi: build/obi_reasoned.owl build/obi_search_view.sql | build/ldtab.jar
	sqlite3 build/obi-tables.db "DROP TABLE IF EXISTS obi;"
	sqlite3 build/obi-tables.db "CREATE TABLE obi (assertion INT NOT NULL, retraction INT NOT NULL DEFAULT 0, graph TEXT NOT NULL, subject TEXT NOT NULL, predicate TEXT NOT NULL, object TEXT NOT NULL, datatype TEXT NOT NULL, annotation TEXT);"
	$(LDTAB) import --table obi build/obi-tables.db $<
	sqlite3 build/obi-tables.db < $(word 2,$^)

build/%_search_view.sql: src/scripts/search_view_template.sql
	sed 's/TABLE_NAME/$*/g' $< > $@

IMPORT_LOADS := $(foreach I,$(IMPORTS),load_$(I)_import)

.PHONY: dump-sql
dump-sql:
load_%_import: build/%_search_view.sql | build/imports/%.db build/ldtab.jar
	sqlite3 build/obi-tables.db "DROP TABLE IF EXISTS $*;"
	sqlite3 build/imports/$*.db '.dump "$*"' | sqlite3 build/obi-tables.db
	sqlite3 build/obi-tables.db < $<
	sqlite3 build/obi-tables.db "CREATE INDEX idx_$*_subject ON $* (subject);"
	sqlite3 build/obi-tables.db "CREATE INDEX idx_$*_predicate ON $* (predicate);"
	sqlite3 build/obi-tables.db "CREATE INDEX idx_$*_object ON $* (object);"
	sqlite3 build/obi-tables.db "ANALYZE;"

load_imports: $(IMPORT_LOADS)

EXPORT_TEMPLATES := $(foreach M,$(MODULE_NAMES),export_$(M))

.PHONY: export_template
export_template:
export_%:
	python3 -m cmi_pb_script.export data build/obi-tables.db build/templates $(subst -,_,$*)
	echo -e "$$(head -2 src/ontology/templates/$*.tsv)\n$$(sed '1d' build/templates/$(subst -,_,$*).tsv)" > src/ontology/templates/$*.tsv

update_templates: $(EXPORT_TEMPLATES)

.PHONY: update_import
update_import:
	python3 -m cmi_pb_script.export data build/obi-tables.db src/ontology/imports import
	python3 -m cmi_pb_script.export data build/obi-tables.db src/ontology/imports import_config

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
	annotate \
	--ontology-iri "$(OBO)/obi.owl" \
	--version-iri "$(OBO)/obi/$(TODAY)/obi.owl" \
	--annotation owl:versionInfo "$(TODAY)" \
	--output $@

views/obi-base.owl: src/ontology/obi-edit.owl | build/robot.jar
	$(ROBOT) remove --input $< \
	--select imports \
	merge $(foreach M,$(MODULE_FILES), --input $(M)) \
	query --update src/sparql/fix-iao.rq \
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

# Run a basic reasoner to find inconsistencies then remove any assertions of owl:Thing as a parent
build/obi_reasoned.owl: build/obi_merged.owl | build/robot.jar
	$(ROBOT) reason --input $< --reasoner ELK relax reduce --output $@

# Find any IRIs using undefined namespaces
.PHONY: validate-iris
validate-iris: src/scripts/validate-iris.py build/obi_merged.owl
	$^

.PHONY: test
test: build/obi_reasoned.owl verify validate-iris


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

# Create a release candidate
# Requires "admin:org", "repo", and "workflow" permissions for gh CLI token
.PHONY: candidate
candidate: obi.owl views build/new-entities.txt
	$(eval REMOTE := $(shell git remote -v | grep "obi-ontology/obi.git" | head -1 | cut -f 1))
	git checkout -b $(TODAY)
	git add -u
	git commit -m "$(TODAY) release candidate"
	git push -u $(REMOTE) $(TODAY)
	gh pr create \
	--title "$(TODAY) release candidate" \
	--body "$$(cat build/new-entities.txt)" \
	--repo obi-ontology/obi
