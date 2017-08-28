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


### ROBOT
#
# We use a forked version of ROBOT for builds.
# TODO: Switch to official version.
robot.jar:
	curl -LO https://github.com/jamesaoverton/rogue-robot/releases/download/0.0.0/robot.jar

ROBOT := java -jar robot.jar


### Testing
#
# Run main tests
.PHONY: test
test: | robot.jar
	$(ROBOT) --help
	echo "Tests succeeded!"


### General
#
# Full build
.PHONY: all
all: test
