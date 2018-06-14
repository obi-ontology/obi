import sys
import re

before = 'build/previous-entities.tsv'
after = 'build/current-entities.tsv'
dropped = 'build/dropped-entities.txt'

entities = []
dropped_entities = []

with open(after) as file:
	for line in file:
		entities.append(line)

with open(before) as file:
	for line in file:
		if line not in entities:
			if line not in dropped_entities:
				dropped_entities.append(line)

n = len(dropped_entities)
if n > 0:
	# Only write the file if entities have been dropped
	with open(dropped, 'w') as file:
		for c in dropped_entities:
			m = re.search('<http://purl.obolibrary\.org/obo/(.+?)>', c)
			if m:
				curie = m.group(1).replace("_", ":")
			else:
				curie = c
			file.write(curie + "\n")
	# Print error message
	if n == 1:
		print("\nERROR\t1 entity has been dropped since last release.")
	else:
		print("\nERROR\t%d entities have been dropped since last release." % n)
	print("\tSee 'build/dropped-entities.txt' for a complete list.")
	sys.exit(1)
else:
	print("\nSUCCESS\t0 entities have been dropped since last release.")
