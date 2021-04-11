DROP TABLE IF EXISTS pdb_files;
DROP TABLE IF EXISTS singleconf_files;
DROP TABLE IF EXISTS multiconf_files;

CREATE TABLE singleconf_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    allele TEXT NOT NULL,
    peptide TEXT NOT NULL,
    binder INTEGER NOT NULL DEFAULT 0,
    filepath TEXT NOT NULL
);

CREATE TABLE multiconf_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    allele TEXT NOT NULL, 
    peptide TEXT NOT NULL,
    binder INTEGER NOT NULL DEFAULT 0,
    num_confirmations INTEGER NOT NULL,
    folderpath TEXT NOT NULL
);
