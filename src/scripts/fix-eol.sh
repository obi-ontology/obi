#!/bin/sh
# Convert Windows -> Unix
perl -pi -e 's/\r\n/\n/g' "$1"
# Convert *old* Mac -> Unix (thanks Excel).
perl -pi -e 's/\r/\n/g' "$1"
