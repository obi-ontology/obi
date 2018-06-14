import sys
import re

before = 'build/previous-classes.tsv'
after = 'build/current-classes.tsv'
dropped = 'build/dropped-classes.txt'

classes = []
dropped_classes = []

with open(after) as file:
	for line in file:
		classes.append(line)

with open(before) as file:
	for line in file:
		if line not in classes:
			dropped_classes.append(line)

n = len(dropped_classes)
if n > 0:
	# Only write the file if classes have been dropped
	with open(dropped, 'w') as file:
		for c in dropped_classes:
			m = re.search('<http://purl.obolibrary\.org/obo/(.+?)>', c)
			if m:
				curie = m.group(1).replace("_", ":")
			else:
				curie = c
			file.write(curie)
	# Print error message
	if n == 1:
		print("\nERROR\t1 class has been dropped since last release.")
	else:
		print("\nERROR\t%d classes have been dropped since last release." % n)
	print("\tSee 'build/dropped-classes.txt' for a complete list.")
	sys.exit(1)
else:
	print("\nSUCCESS\t0 classes have been dropped since last release.")
