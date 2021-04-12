import sqlite3

import click
import csv
import os
from glob import glob
from flask import current_app, g
from flask.cli import with_appcontext

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
                current_app.config['DATABASE'],
                detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = dict_factory

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()
    alleles = set()
    peptides = set()

    print("Resetting database...")
    with current_app.open_resource("schema.sql") as schema_script:
        db.executescript(schema_script.read().decode("utf-8"))
    print("Database Reset!\n")

    # Get filenames,
    print("Getting filenames...")
    f = []
    for (dirpath, dirname, filenames) in os.walk("/rdf_mount/singleconf/all_data"):
        f.extend(filenames)
        break
    print("Filenames Retrived!\n")

    # Filter out files that are not pdb files
    print("Filtering out non-pdb files...")
    f = [n for n in f if '.pdb' in n]
    print("Filtered out non-pdb files!\n")

    # Define map function
    def filename_to_row(filename):
        dash = filename.index('-')
        period = filename.index('.')
        allele = filename[:dash]
        peptide = filename[dash+1:period]
        filepath = f'/rdf_mount/singleconf/all_data/{filename}'
        print(allele, peptide, filepath)
        alleles.add(tuple([allele]))
        peptides.add(tuple([peptide]))
        return tuple([allele, peptide, filepath])

    print("Converting filenames to rows...")
    data_rows = list(map(filename_to_row, f))
    print("Created all rows!\n")

    print("Converting rows to dict...")
    data_dict = dict()
    for row in data_rows:
        data_dict[row[:2]] = row
    print("Createed rows dictionary!\n")

    print("Reading binder data...")
    rows = []
    binder_filepath = "/rdf_mount/singleconf/labels.csv"
    with open(binder_filepath, 'r') as binder_file:
        csv_reader = csv.reader(binder_file, delimiter=" ")
        next(csv_reader)
        for row in csv_reader:
            try:
                db_row = data_dict[tuple(row[:2])] + tuple(row[2:])
            except KeyError:
                continue
            print(db_row)
            rows.append(db_row)
    print("Read all binder data!\n")

    # Create cursor.
    c = db.cursor()

    print("Inserting rows into database...")
    c.executemany('''INSERT INTO singleconf_files (allele, peptide, filepath, binder) 
            VALUES (?, ?, ?, ?)''', rows)
    print("Inserted all rows!\n")

    db.commit()

    # Get the list of directories in the multiconf folder
    print("Getting all dir paths in multiconf folder...")
    folder_paths = glob("/rdf_mount/multiconf/ensemble/*/")
    print("Got all dir paths!\n")
    
    # Create list of rows and 
    def dirpaths_to_rows(dirpath):
        allele_peptide = os.path.basename(os.path.normpath(dirpath))
        dash_index = allele_peptide.index("-")
        allele = allele_peptide[:dash_index]
        peptide = allele_peptide[dash_index+1:]
        num_files = len([name for name in os.listdir(dirpath)])
        alleles.add(tuple([allele]))
        peptides.add(tuple([peptide]))
        return tuple([allele, peptide, dirpath, num_files])

    print("Create data rows for multiconf...")
    data_rows = list(map(dirpaths_to_rows, folder_paths))
    print("Finished creating data rows!\n")
    
    print("Converting rows to dict...")
    data_dict = dict()
    for row in data_rows:
        data_dict[row[:2]] = row
    print("Createed rows dictionary!\n")

    print("Reading binder data...")
    rows = []
    binder_filepath = "/rdf_mount/singleconf/labels.csv"
    with open(binder_filepath, 'r') as binder_file:
        csv_reader = csv.reader(binder_file, delimiter=" ")
        next(csv_reader)
        for row in csv_reader:
            try:
                db_row = data_dict[tuple(row[:2])] + tuple(row[2:])
            except KeyError:
                continue
            print(db_row)
            rows.append(db_row)
    print("Read all binder data!\n")

    print("Inserting rows into database...")
    c.executemany('''INSERT INTO multiconf_files (allele, peptide, folderpath, num_confirmations, binder) 
            VALUES (?, ?, ?, ?, ?)''', rows)
    print("Inserted all rows!\n")


    print("Inserting alleles into database...")
    c.executemany("INSERT INTO alleles (allele) VALUES (?)", alleles)
    print("Inserted all alleles!\n")


    print("Inserting peptides into database...")
    c.executemany("INSERT INTO peptides (peptide) VALUES (?)", peptides)
    print("Inserted all peptides!\n")

    db.commit()


@click.command("init-db")
@with_appcontext
def init_db_command():
    init_db()
    click.echo("Initialized the database.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
