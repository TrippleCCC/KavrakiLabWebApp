DROP TABLE IF EXISTS pdb_files;

CREATE TABLE pdb_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    allele TEXT NOT NULL,
    peptide TEXT NOT NULL,
    binder INTEGER NOT NULL DEFAULT 0,
    filepath TEXT NOT NULL
);