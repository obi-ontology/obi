#!/bin/sh

# Create an OBI release candidate with a GitHub PR.
# Requires `git`, `make`, and `gh`.
# Requires "admin:org", "repo", and "workflow" permissions for gh CLI token

### Utility Functions
#
# Prompt for user confirmation.
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

fail() {
    echo "ERROR: $1"
    exit 1
}

for COMMAND in make git gh
do
    if ! command -v ${COMMAND} > /dev/null
    then
        fail "Required command '${COMMAND}' was not found"
    fi
done

# Check repository status
test "$(git branch --show-current)" = 'master' || fail 'Must be on `master` branch'
git pull || fail "Must be up-to-date with origin/master"
test "$(git rev-list HEAD...origin/master --count)" -eq 0 || fail "Must be up-to-date with origin/master"
git diff --exit-code . || fail "Changes to src/ must be committed"

# Build release files
make clean all || fail "There were problems with the build"
echo "Check obi.owl and views/obi_core.owl"
confirm "Ready to create release candidate?"

# Make a new release-candidate
DATE="$(date '+%Y-%m-%d')"
BRANCH="rc-${DATE}"
TITLE="Release Candidate ${DATE}"
git checkout -b "${BRANCH}" || fail "Problem creating branch ${BRANCH}"
git add -u obi.owl views/ || fail "Problem adding files"
git commit -m "${TITLE}" || fail "Problem committing"
make build/new-entities.txt || fail "Problem getting new entities"
git push -u origin "${BRANCH}"
gh pr create \
  --title "${TITLE}" \
  --body-file build/new-entities.txt \
  || fail "Problem creating PR"
URL="$(gh pr view --json url --jq .url)"
EMAIL="build/release-candidate-email.txt"

cat << EOF > "${EMAIL}"
To: <obi-devel@lists.sourceforge.net>
Subject: OBI ${TITLE}

Hi everyone,

A new OBI release candidate is available:

- Pull Request: ${URL}
- Main OWL: https://raw.githubusercontent.com/obi-ontology/obi/${BRANCH}/obi.owl

Please review it and comment on the PR if you see any problems. We will make a release decision in one week.

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

echo "Done!"
