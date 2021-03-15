import csv
import sqlite3
import itertools

binder_filepath = "/rdf_mount/singleconf/labels.csv"

db = sqlite3.connect("instance/index.db")

curr = db.cursor()

rows = []
with open(binder_filepath, 'r') as binder_file:
	reader = csv.reader(binder_file, delimiter=" ")
	for row in reader:
		rows.append(row)

rows = rows[1:]
print(rows[0])

# Add new column to table
if "binder" not in list(itertools.chain(*db.execute("PRAGMA table_info(pdb_files)").fetchall())):
	db.execute("ALTER TABLE pdb_files ADD COLUMN binder INTEGER")

for row in rows:
	curr.execute("UPDATE pdb_files SET binder = ? WHERE allele = ? AND peptide = ?", (int(row[2]), row[0], row[1]))

db.commit()

db.close()
