import os
import sqlite3

conn = sqlite3.connect('index.db')

c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS pdb_files
                (allele text, protein text, filepath text, PRIMARY KEY(allele,
                protein))''')

f = []
for (dirpath, dirname, filenames) in os.walk("/rdf_mount/singleconf/all_data"):
        f.extend(filenames)
        break

f = [n for n in f if '.pdb' in n]

def filename_to_column(filename):
        dash = filename.index('-')
        period = filename.index('.')
        allele = filename[:dash]
        protein = filename[dash+1:period]
        filepath = f'/rdf_mount/singleconf/all_data/{filename}'
        print(allele, protein, filepath)
        return tuple([allele, protein, filepath])

columns = list(map(filename_to_column, f))

c.executemany('INSERT INTO pdb_files VALUES (?, ?, ?)', columns)

conn.commit()

conn.close()
