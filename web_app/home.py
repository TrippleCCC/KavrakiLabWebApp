import time
import os
import io
import zipfile
from flask import (
        Blueprint, render_template, redirect, url_for, request, current_app, jsonify, send_file, flash
)

from web_app.db import get_db

bp = Blueprint("home", __name__, "/")

results_query = """
SELECT allele, peptide, binder, filepath
FROM pdb_files
WHERE allele LIKE :allele AND peptide LIKE :allele
AND binder IN :binder_values
"""

LIMIT_MESSAGE = "Results have been limited to 2000 for all-allele, all-pepetide search"

@bp.route("/", methods=["GET"])
def home():
    return render_template("base.html", allele=None)


@bp.route("/search", methods=["POST"])
def search():
    # Handle query parameters. Then redirect.
    allele = request.form.get("allele") or "any-allele"
    peptide = request.form.get("peptide") or "any-peptide"
    binder = request.form.get("binder") or "off"
    non_binder = request.form.get("non-binder") or "off"
    return redirect(url_for(".results", allele=allele, peptide=peptide, binder=binder, non_binder=non_binder))


@bp.route("/results", methods=["GET"])
def results():
    db = get_db()
    data = []
    parameters = dict()

    allele = request.args.get("allele")
    peptide = request.args.get("peptide")
    binder = 1 if request.args.get("binder") == "on" else 0
    non_binder = 1 if request.args.get("non_binder") == "on" else 0

    binder_values = []
    if binder:
        binder_values.append("1")
    if non_binder:
        binder_values.append("0")

    binder_values = "(" + ", ".join(binder_values) + ")"

    start = time.time()
    # Check the parameters and search the database
    # TODO: add pagination functionality for these results.
    if (allele, peptide) == ("any-allele", "any-peptide"):
        # Let user know theres a limit on the results.
        flash(LIMIT_MESSAGE, "warning")
        data = db.execute(f"SELECT * FROM pdb_files WHERE binder IN {binder_values} LIMIT 2000").fetchall()
    elif allele == "any-allele":
        data = db.execute(f"SELECT * FROM pdb_files WHERE peptide = ? AND binder IN {binder_values}",
                (peptide,)).fetchall()
    elif peptide == "any-peptide":
        data = db.execute(f"SELECT * FROM pdb_files WHERE allele = ? AND binder in {binder_values}",
                (allele,)).fetchall()
    else:
        data = db.execute(f"""SELECT * FROM pdb_files WHERE allele = ?
            AND peptide = ? AND binder in {binder_values}""", (allele, peptide)).fetchall()
    end = time.time()

    query_time = end - start
    num_results = len(data)

    return render_template("results.html", results=data, allele=allele, 
            peptide=peptide, num_results=num_results, query_time=query_time,
            binder=binder, non_binder=non_binder)


@bp.route("/suggest/<suggest_type>", methods=["GET"])
def suggest(suggest_type):
    db = get_db()
    query = request.args.get("query")
    # Get the suggestions based on the suggestion type
    if suggest_type == 'allele':
        data = db.execute("SELECT DISTINCT allele FROM pdb_files WHERE allele LIKE ? LIMIT 5", (f'%{query}%',)).fetchall()
        data = list(map(lambda r: {"value":r["allele"], "data":r["allele"]}, data))
    elif suggest_type == "peptide":
        data = db.execute("SELECT DISTINCT peptide FROM pdb_files WHERE peptide LIKE ? LIMIT 5", (f'%{query}%',)).fetchall()
        data = list(map(lambda r: {"value":r["peptide"], "data":r["peptide"]}, data))
    else:
        data = []

    return jsonify({"suggestions":data}) 


