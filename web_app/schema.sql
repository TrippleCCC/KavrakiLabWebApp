DROP TABLE IF EXISTS alleles;
DROP TABLE IF EXISTS peptides;
DROP TABLE IF EXISTS singleconf_files;
DROP TABLE IF EXISTS multiconf_files;

CREATE TABLE alleles (
    allele TEXT NOT NULL PRIMARY KEY
);

CREATE TABLE peptides (
    peptide TEXT NOT NULL PRIMARY KEY
);

CREATE TABLE singleconf_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    allele TEXT NOT NULL,
    peptide TEXT NOT NULL,
    binder INTEGER NOT NULL DEFAULT 0,
    filepath TEXT NOT NULL,
    FOREIGN KEY(allele) REFERENCES alleles(allele),
    FOREIGN KEY(peptide) REFERENCES peptides(peptide)
);

CREATE TABLE multiconf_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    allele TEXT NOT NULL, 
    peptide TEXT NOT NULL,
    binder INTEGER NOT NULL DEFAULT 0,
    num_confirmations INTEGER NOT NULL,
    folderpath TEXT NOT NULL,
    FOREIGN KEY(allele) REFERENCES alleles(allele),
    FOREIGN KEY(peptide) REFERENCES peptides(peptide)
);
