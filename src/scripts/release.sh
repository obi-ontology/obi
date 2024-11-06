#!/bin/sh

# Create an OBI release.

### Utility Functions
#
# Prompt for user confirmation
# Based on https://stackoverflow.com/a/3232082
confirm() {
  # call with a prompt string or use a default
  echo "${1:-Are you sure?} [y/N] "
  read -r response
  case "$response" in
    [yY][eE][sS]|[yY]) true ;;
    *) exit 1 ;;
  esac
}

# Print error message and exit
fail() {
    echo "ERROR: $1"
    exit 1
}

# Check for required commands
for COMMAND in make git gh
do
    if ! command -v ${COMMAND} > /dev/null
    then
        fail "Required command '${COMMAND}' was not found"
    fi
done

# Check repository status
test "$(git branch --show-current)" == 'master' || fail 'Must be on `master` branch'
git pull || fail "Must be up-to-date with origin/master"
test "$(git rev-list HEAD...origin/master --count)" -eq 0 || fail "Must be up-to-date with origin/master"
git diff --exit-code . || fail "Changes to src/ must be committed"

# Get the date from the obi.owl file.
DATE="$(grep owl:versionInfo obi.owl | head -n1 | grep -o '[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}')"
DATE="${DATE:?Invalid date}"
confirm "Is this the release date: '${DATE}'?"

# Make a new GitHub release.
echo "Creating GitHub release:"
gh release create "v${DATE}" --title "${DATE} Release" --notes-file build/new-entities.txt || fail "Failed to create GitHub release"

# Draft an announcement email.
EMAIL="build/release-email.txt"

cat << EOF > "${EMAIL}"
To: <obi-devel@lists.sourceforge.net>, <obi-users@googlegroups.com>
Subject: OBI Release ${DATE}

Hi everyone,

A new OBI release is available:

- Versioned OWL: http://purl.obolibrary.org/obo/obi/${DATE}/obi.owl
- Notes: https://github.com/obi-ontology/obi/releases/tag/v${DATE}
- Branch: https://github.com/obi-ontology/obi/tree/v${DATE}

Please see the notes for changes.

Best,

James
EOF

if command -v himalaya > /dev/null
then
    himalaya --folder Drafts save < "${EMAIL}"
    echo "Draft email created"
else
    echo "Draft email created in ${EMAIL}"
fi

echo "Update PURLs then send the announcement email:"
echo "https://github.com/OBOFoundry/purl.obolibrary.org/blob/master/config/obi.yml"
