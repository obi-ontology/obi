#!/bin/sh
find src -name '*.tsv' -print0 | while read -d $'\0' file
do
    ./src/scripts/fix-eol.sh "$file"
done
